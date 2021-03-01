# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright 2018 SerialLab Corp.  All rights reserved.
from __future__ import absolute_import, unicode_literals
import io
import re
from logging import getLogger
from typing import List
from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from django.utils.timezone import datetime
from django.db.utils import IntegrityError
from django.core.files.storage import get_storage_class
from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from quartet_capture.errors import RuleNotFound
from quartet_capture.models import Task as DBTask, Rule as DBRule, \
    TaskHistory, Filter, RuleFilter
from quartet_capture.rules import Rule
import time
from quartet_capture.models import haikunate

StringList = List[str]
logger = getLogger('quartet_capture')


def execute_rule(message: bytes, db_task: DBTask):
    '''
    Helper function that executes a rule inline and returns
    the context.  The celery task below essentially does the same thing
    without returning the rule context.
    When a message arrives, creates a record of the message and parses
    it using the appropriate parser.
    :param message_data: The data to be handled.
    '''
    # create an executable task from a database rule
    c_rule = Rule(db_task.rule, db_task)
    # execute the rule
    c_rule.execute(message)
    # return the context
    return c_rule.context


@shared_task(name='execute_queued_task')
def execute_queued_task(task_name: str, user_id: int = None,
                        raise_exception=False):
    '''
    Queues up a rule for execution by saving the file to file storage
    and putting the descriptor and rule name on a queue.
    :param message: The message to queue.
    '''
    if user_id:
        User = get_user_model()
        user = User.objects.get(id=user_id)
    else:
        user = None
    db_task = DBTask.objects.get(name=task_name)
    if user and user.id:
        TaskHistory.objects.create(task=db_task, user=user)
    try:
        start = time.time()
        logger.debug('Running task %s', db_task.name)
        # update the start time and status
        db_task.start = datetime.now()
        db_task.status = 'RUNNING'
        db_task.save()
        # load the message
        storage_class = get_storage_class()
        django_storage = storage_class()
        message_file = django_storage.open(
            name='{0}.dat'.format(db_task.name))
        data = message_file.read()
        c_rule = Rule(db_task.rule, db_task)
        # execute the rule
        c_rule.execute(data)
        db_task.status = 'FINISHED'
    except SoftTimeLimitExceeded:
        logger.exception('The task exceeded the configured time limit '
                         'threshold.  Consider either raising the time '
                         'limit in your Celery configuration and/or adjust '
                         'your computing resources accordingly.')
        db_task.status = 'QUEUED'
        db_task.save()
    except Exception:
        logger.exception('Could not execute task with name %s', task_name)
        db_task.status = 'FAILED'
        db_task.save()
        if raise_exception:
            raise
    finally:
        db_task.end = datetime.now()
        end = time.time()
        db_task.execution_time = (end - start)
        db_task.save()


def create_and_queue_task(data, rule_name: str,
                          task_type: str = 'Input',
                          run_immediately: bool = False,
                          initial_status='QUEUED',
                          task_parameters=[],
                          user_id: int = None,
                          rule: Rule = None):
    '''
    Will queue an outbound task in the rule engine for processing using
    the rule specified by name in the rule_name parameter.
    :param data: The data to queue. The data should be a proper File
    object or any python file-like object, ready to be read from
    the beginning or a string (which will be converted to a stream).
    :param rule_name: The name of the rule that will process the queued
    data.  This rule is typically a rule that is responsible for sending
    the data somewhere using a network protocol.
    :param task_type: The type of task.  Mostly descriptive in nature and
    a way of letting users know what the general intent of the task is.
    :param run_immediately: If this is set to true, the task will be created
    and sent directly to the rule engine for processing thereby bypassing
    the Celery task queue.  When False, the task gets queued using Celery.
    :return: The task instance.
    '''
    try:
        # get the rule
        if rule == None:
            rule = DBRule.objects.get(name=rule_name)
        # if the rule exists, store the file using the configured
        # storage class
        file_store = get_storage_class()
        task = DBTask()
        task.rule = rule
        task.type = task_type
        # correlate the name of the file with the task
        filename = '{0}.dat'.format(task.name)
        if isinstance(data, str):
            data = io.BytesIO(data.encode('utf-8'))
        elif isinstance(data, bytes):
            data = io.BytesIO(data)
        task.location = file_store().save(name=filename, content=data)
        task.status = initial_status
        try:
            task.save()
        except IntegrityError:
            logger.warning('There was a task name conflict trying to generate '
                           'a new one...')
            task.name = haikunate()
            task.save()
        for task_parameter in task_parameters:
            task_parameter.task = task
            task_parameter.save()
        if run_immediately:
            # execute in line (skips the rule engine and celery)
            execute_queued_task(task_name=task.name, user_id=user_id,
                                raise_exception=True)
        else:
            # queue up the task using celery
            execute_queued_task.delay(task_name=task.name, user_id=user_id)
        return task
    except IntegrityError:
        logger.exception('There was an error creating and queuing the task.')
        raise
    except DBRule.DoesNotExist:
        raise RuleNotFound(
            _('The Rule with name %s could not be found.  Please check '
              'your configuration and ensure a Rule with that name exists.'),
            rule_name
        )


def get_rules_by_filter(filter_name: str, message: str,
                        return_all: bool = True) -> StringList:
    '''
    Looks up any matching rules based on an inbound filter and returns a list
    of matches regardless of whether one or more matches is found and
    regardless of whether the `return_all` flag has been set to false.
    :param filter_name: The name of the filter to use (which contains the
    search term).
    :param message: The message to search within.
    :param: return_all: Whether to return the first match or all matches.
    Default is True.
    :return: A list of rule names instances.
    '''
    if isinstance(message, bytes):
        message = message.decode('utf-8')

    if not isinstance(message, str):
        message = str(message.read())

    filter = Filter.objects.prefetch_related('rulefilter_set').get(
        name=filter_name)
    ret = []
    match_found = False
    for rule_filter in filter.rulefilter_set.all():
        if not match_found and rule_filter.default:
            ret.append(rule_filter.rule.name)
        elif match_found and rule_filter.default:
            pass
        elif rule_filter.search_type == 'search':
            match = rule_filter.search_value in message \
                    and not rule_filter.reverse
            if match:
                match_found = True
                ret.append(rule_filter.rule.name)
                if not return_all or rule_filter.break_on_true: break
        elif rule_filter.search_type == 'regex':
            pattern = re.compile(rule_filter.search_value)
            match = pattern.match(message) and not rule_filter.reverse
            if match:
                match_found = True
                ret.append(rule_filter.rule.name)
                if not return_all or rule_filter.break_on_true: break
    return ret


def get_rule_by_filter(filter_name: str, message: str) -> str:
    '''
    Looks up a rule name based on a search value within a message.  If found,
    the message will be routed to the rule that was found.
    :param filter_name:
    :return:
    '''
    filter = Filter.objects.prefetch_related('rulefilter_set').get(
        name=filter_name)
    ret = None
    for rule_filter in filter.rulefilter_set.all():
        if rule_filter.search_type == 'search':
            match = rule_filter.search_value in message \
                    and not rule_filter.reverse
            if match:
                ret = rule_filter.rule.name
                break
        if rule_filter.search_type == 'regex':
            pattern = re.compile(rule_filter.search_value)
            match = pattern.match(message) and not rule_filter.reverse
            if match:
                ret = rule_filter.rule.name
                break
    return ret
