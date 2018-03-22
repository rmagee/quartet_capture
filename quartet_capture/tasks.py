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
from logging import getLogger
from django.utils.timezone import datetime
from django.core.files.storage import get_storage_class
from celery import shared_task
from quartet_capture.models import Rule as DBRule
from quartet_capture.models import Task as DBTask
from quartet_capture.rules import Rule
import time

logger = getLogger('quartet_capture')


@shared_task(name='execute_rule')
def execute_rule(message: str, rule_name: str):
    '''
    When a message arrives, creates a record of the message and parses
    it using the appropriate parser.
    :param message_data: The data to be handled.
    '''
    # get the rule from the database
    print('executing task')
    db_rule = DBRule.objects.get(name=rule_name)
    # create a rule instance with the db rule
    c_rule = Rule(db_rule)
    # execute the rule
    c_rule.execute(message)


@shared_task(name='execute_queued_task')
def execute_queued_task(task_name: str):
    '''
    Queues up a rule for execution by saving the file to file storage
    and putting the descriptor and rule name on a queue.
    :param message: The message to queue.
    :param rule_name: The rule name to process the message with.
    '''
    db_task = DBTask.objects.get(name=task_name)
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
        message_file = django_storage.open(name='{0}.dat'.format(db_task.name))
        data = message_file.read()
        # call execute rule
        execute_rule(data, db_task.rule.name)
        db_task.status = 'FINISHED'
    except Exception:
        logger.exception('Could not execute task with name %s', task_name)
        db_task.status = 'FAILED'
        raise
    finally:
        db_task.end = datetime.now()
        end = time.time()
        db_task.execution_time = (end - start)
        db_task.save()
