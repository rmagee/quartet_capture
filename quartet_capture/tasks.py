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
from logging import getLogger
from django.db import transaction
from django.contrib.auth.models import User
from django.utils.translation import gettext as _
from django.utils.timezone import datetime
from django.core.files.storage import get_storage_class
from celery import shared_task
from quartet_capture.errors import RuleNotFound
from quartet_capture.models import Task as DBTask, Rule as DBRule, TaskHistory
from quartet_capture.rules import Rule
import time

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
def execute_queued_task(task_name: str, user_id: int = None):
    '''
    Queues up a rule for execution by saving the file to file storage
    and putting the descriptor and rule name on a queue.
    :param message: The message to queue.
    '''
    if user_id:
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
    except Exception:
        logger.exception('Could not execute task with name %s', task_name)
        db_task.status = 'FAILED'
        db_task.save()
    finally:
        db_task.end = datetime.now()
        end = time.time()
        db_task.execution_time = (end - start)
        db_task.save()

def create_and_queue_task(data, rule_name: str,
                          task_type: str = 'Input',
                          run_immediately: bool = False,
                          initial_status='QUEUED',
                          task_parameters=[]):
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
            data = io.StringIO(data)
        task.location = file_store().save(name=filename, content=data)
        task.status = initial_status
        task.save()
        for task_parameter in task_parameters:
            task_parameter.task = task
            task_parameter.save()
        if run_immediately:
            # execute in line (skips the rule engine and celery)
            execute_queued_task(task_name=task.name)
        else:
            # queue up the task using celery
            execute_queued_task.delay(task_name=task.name)
        return task
    except DBRule.DoesNotExist:
        raise RuleNotFound(
            _('The Rule with name %s could not be found.  Please check '
              'your configuration and ensure a Rule with that name exists.'),
            rule_name
        )
