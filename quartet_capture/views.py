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
import io
from django.core.files import storage
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from rest_framework import exceptions
from django.db import transaction

from quartet_capture.tasks import execute_queued_task
from quartet_capture.models import Rule, Task

import logging

logger = logging.getLogger('quartet_capture')


class CaptureInterface(APIView):
    '''
    The view responsible for capturing the files and handing
    off the queuing to a celery task.

    This view loads the full request onto the celery broker, so you may
    want to set some upload/size limits on inbound messages to avoid
    any type of memory issues under heavy load.  The messages are only
    briefly in memory but it can be an issue.

    When configuring the REST_FRAMEWORK attributes, use the
    DEFAULT_THROTTLE_CLASS of 'rest_framework.throttling.ScopedRateThrottle'
    and configure your upload throttle using the scope `capture_upload`.
    '''
    # set the parser to handle HTTP post / upload
    parser_classes = (MultiPartParser,)
    # this is the throttle scope for this view
    throttle_scope = 'capture_upload'

    def post(self, request: Request, format=None):
        logger.info('Message from %s', getattr(request.META, 'REMOTE_HOST',
                                               'Host Info not Available'))
        # get the rule from the query parameter
        rule_name = request.query_params.get('rule', None)
        run = request.query_params.get('run-immediately', False)
        if not rule_name:
            raise exceptions.APIException(
                'You must supply the rule Query '
                'Parameter at the end of your request URL. '
                'For example: ?rule=epcis.  The quartet_capture rule '
                'framework uses this value to determine how to process '
                'your message.',
                status.HTTP_400_BAD_REQUEST
            )
        # get the message from the request
        message = request.FILES.get('file') or request.POST.get('file')
        if not message:
            raise exceptions.APIException(
                'No "file" field variable found in the HTTP POST data.  The '
                'multiform data must be posted with the name "file" as '
                'it\'s variable name.',
                status.HTTP_400_BAD_REQUEST
            )
        # execute the rule as a task in celery
        logger.debug('Executing rule %s', rule_name)
        rule = self._rule_exists(rule_name)
        storage_class = storage.get_storage_class()
        django_storage = storage_class()
        ret = self._queue_task(message, rule, django_storage)

        if run:
            # create a task and queue it for processing - returns the task name
            execute_queued_task(task_name=ret)
        else:
            execute_queued_task.delay(task_name=ret)

        return Response(ret, status=status.HTTP_201_CREATED)

    def _rule_exists(self, rule_name):
        '''
        Looks up the rule and throws a DoesNotExist exception if it can not
        be found.  Will prevent the potential queueing of large messages
        that don't have a rule to process them with.
        '''
        rule = Rule.objects.get(name=rule_name)
        return rule

    @transaction.atomic
    def _queue_task(self, message, rule, file_store: storage.Storage):
        '''
        Saves the file using
        the configured FileStorage class using the task.name with `.dat` at
        the end and then saves the task in the database.  Celery tasks
        monitor this table for messages and execute any that are marked as
        QUEUED.
        :param message: The uploaded file.
        :param rule: The rule to execute once Celery picks the message off
        the queue.
        :param file_store: The configured Django FileStorage class.
        :return: The Task.
        '''
        task = Task()
        task.rule = rule
        filename = '{0}.dat'.format(task.name)
        if isinstance(message, str):
            message = io.StringIO(message)
        task.location = file_store.save(name=filename, content=message)
        task.status = 'QUEUED'
        task.save()
        return task.name


class EPCISCapture(CaptureInterface):
    '''
    A more strict implementation of the EPCIS capture interface to
    meet requirements in section 10.2 of the EPCIS 1.2 protocol.
    '''

    def post(self, request: Request):
        message = request.FILES.get('file') or request.POST.get('file')
        if message and not isinstance(message, str):
            message = message.read()
        if 'EPCISDocument' not in message:
            raise status.HTTP_400_BAD_REQUEST(
                'The EPCIS capture interface '
                'is for EPCIS Documents only. To submit other '
                'types of data use the quartet-capture '
                'interface.'
            )
        # TODO: perhaps more sophisticated checking?
        return super().post(request, format)
