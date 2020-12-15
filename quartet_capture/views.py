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
import coreapi
import coreschema
import io
import logging
from django.conf import settings
from django.core.files import storage
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.utils.translation import gettext as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework import exceptions
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.schemas import ManualSchema
from rest_framework.views import APIView

from quartet_capture.errors import TaskExecutionError
from quartet_capture.models import Rule, Task, TaskParameter, Filter
from quartet_capture.parsers import RawParser
from quartet_capture.rules import clone_rule
from quartet_capture.tasks import execute_queued_task, create_and_queue_task, \
    get_rules_by_filter
from rest_framework_xml.renderers import XMLRenderer

logger = logging.getLogger('quartet_capture')

# Set RETURN_ALL_RULES in your settings to overide the default behavior of
# the capture filters.  Setting to false will make the default behavior
# to return the first matched filter.
DEFAULT_RETURN_ALL_RULES = getattr(settings, 'RETURN_ALL_RULES', True)


class ExcuteTaskView(APIView):
    """
    Will, by task name, execute a given task.  This can be useful if a task
    was queued and never started due to the Celery task queue being unavailable
    or if, for whatever reason, a task failed and needs to be re-executed.

    Usage:

        http[s]://[host]:[port]/capture/execute/?task-name=[task name]

    """
    queryset = Task.objects.none()

    def get(self, request: Request, task_name: str = None, format=None):
        if task_name:
            run = request.query_params.get('run-immediately', False)
            user_id = None
            if request.user:
                user_id = request.user.id
            try:
                if run:
                    # create a task and queue it for processing - returns the task name
                    execute_queued_task(task_name=task_name, user_id=user_id)
                    task = Task.objects.get(task_name=task_name)
                    if task.status == 'FAILED':
                        raise TaskExecutionError()
                else:
                    execute_queued_task.delay(task_name=task_name,
                                              user_id=user_id)
                ret = Response(
                    _('Task %s has been re-queued for execution.') % task_name)
            except TaskExecutionError:
                ret = Response(
                    _('Task %s has failed execution.') % task_name,
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            except Exception:
                logger.error('There was an unexpected error executing the '
                             'task')
                ret = Response(
                    'There was an unexpected error executing the '
                    'task.  More info is available in the '
                    'error log.',
                    status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            ret = Response()
        return ret


class CloneRuleView(APIView):
    """
    Will clone a rule instance.  The clone will contain copies of the
    rule parameters, steps and step parameters.  No RuleFilter references
    will be copied.

    For more info on functionality, see the `quartet_capture.rules.clone_rule`
    function.
    """
    queryset = Rule.objects.none()

    schema = ManualSchema(fields=[
        coreapi.Field(
            "rule_name",
            required=True,
            location="path",
            schema=coreschema.String()
        ),
        coreapi.Field(
            "new_rule_name",
            required=True,
            location="path",
            schema=coreschema.String()
        ),
    ])

    def post(self, request, rule_name=None, new_rule_name=None):
        if rule_name:
            try:
                new_rule = clone_rule(rule_name, new_rule_name=new_rule_name)
                ret = Response(new_rule.name)
            except Exception:
                if getattr(settings, 'DEBUG', False):
                    logger.exception('Error trying to clone rule with name.'
                                     % rule_name)
                    ret = Response(
                        'There was an unexected error cloning the rule.',
                        status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                else:
                    raise
        else:
            ret = Response()
        return ret


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

    If multiple rules were executed, only the last rule
    name will be returned.
    '''
    # set the parser to handle HTTP post / upload
    parser_classes = (MultiPartParser, RawParser)
    # this is the throttle scope for this view
    throttle_scope = 'capture_upload'
    # sentry queryset for permissions
    queryset = Task.objects.none()

    @swagger_auto_schema(responses=
                         {201: 'Returns the created task identifier.',
                          500: 'Internal server error descriptions.'}
                         )
    def post(self, request: Request, format=None, epcis=False):
        logger.info('Message from %s', getattr(request.META, 'REMOTE_HOST',
                                               'Host Info not Available'))
        # get the message from the request
        files = request.FILES if len(request.FILES) > 0 else request.POST
        if len(files) == 0:
            files = self._inspect_data(request)
        elif len(files) > 1:
            raise exceptions.APIException(
                'Only one file may be posted at a time.',
                status.HTTP_400_BAD_REQUEST
            )
        for file, message in files.items():
            if not message:
                raise exceptions.ParseError(
                    'No "file" field variable found in the HTTP POST data.  The '
                    'multiform data must be posted with the name "file" as '
                    'it\'s variable name.',
                    status.HTTP_400_BAD_REQUEST
                )
            # first see if a filter is being used
            rules = []
            filter_name = request.query_params.get('filter', None)
            if filter_name:
                logger.debug('Grabbing a list of rules for filter %s.',
                             filter_name)
                return_all_rules = request.query_params.get(
                    'return-all-rules') or DEFAULT_RETURN_ALL_RULES
                try:
                    rules = get_rules_by_filter(filter_name, message,
                                                return_all_rules)
                except Filter.DoesNotExist:
                    exc = exceptions.APIException(
                        'The filter %s does not exist.  Make sure your '
                        'filter parameter is correct and corresponds with'
                        ' the name of a valid filter on this instance.'
                        % filter_name
                    )
                    exc.status_code = status.HTTP_400_BAD_REQUEST
                    raise exc
            # get the rule from the query parameter
            if len(rules) == 0:
                logger.debug('No rules were found.')
                if epcis:
                    rules = [request.query_params.get('rule', 'EPCIS')]
                else:
                    rule = request.query_params.get('rule', None)
                    if rule:
                        rules = [rule]
            run = True if request.query_params.get('run-immediately') in \
                          ['true', 'True'] else False
            if len(rules) == 0 and not filter_name:
                exc = exceptions.APIException(
                    'You must supply the rule Query '
                    'Parameter at the end of your request URL. '
                    'For example: ?rule=EPCIS.  The quartet_capture rule '
                    'framework uses this value to determine how to process '
                    'your message. Otherwise, you must specify a filter name',
                )
                exc.status_code = status.HTTP_400_BAD_REQUEST
                raise exc
            # execute the rule as a task in celery
            for rule_name in rules:
                logger.debug('Executing rule %s', rule_name)
                if not self._rule_exists(rule_name):
                    exc = exceptions.APIException(
                        'The rule with name %s, does '
                        'not exist in the system.' %
                        rule_name
                    )
                    exc.status_code = status.HTTP_400_BAD_REQUEST
                    raise exc
                storage_class = storage.get_storage_class()
                django_storage = storage_class()
                # create a task and get the task name to return to the
                # calling application
                user_id = self._get_user_id(request)
                try:
                    ret = create_and_queue_task(
                        message,
                        rule_name,
                        run_immediately=run,
                        task_parameters=self._get_task_parameters(request),
                        user_id=user_id
                    )
                except Exception as err:
                    exc = exceptions.APIException(
                        'Error in rule %s: %s' % (
                            rule_name, ','.join(err.args))
                    )
                    exc.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
                    raise exc

                return Response(ret.name, status=status.HTTP_201_CREATED)
            raise exceptions.APIException('No task was created.  This is most '
                                          'likely due to a filter with no '
                                          'rules assigned.',
                                          status.HTTP_500_INTERNAL_SERVER_ERROR
                                          )

    def _inspect_data(self, request: Request):
        """
        Will take the raw data if a multipart upload was not specified.
        Just simulates what a file input would look like.
        :param request: The inbound request.
        :return: A dictionary with a single entry with the key `raw`
        and the value of the request.data field.
        """
        if len(request.data) > 0:
            return {'raw': request.data}
        else:
            raise exceptions.APIException(
                'No data was posted.',
                status.HTTP_400_BAD_REQUEST
            )

    def _get_user_id(self, request) -> int:
        '''
        Returns the primary key of the user in the request.
        :param request: The HttpRequest
        :return: A user id. (int)
        '''
        user = getattr(request, 'user', None)
        user_id = None
        if user:
            user_id = user.id
        return user_id

    def _rule_exists(self, rule_name) -> Rule:
        '''
        Looks up the rule and throws a DoesNotExist exception if it can not
        be found.  Will prevent the potential queueing of large messages
        that don't have a rule to process them with.
        '''
        try:
            rule = Rule.objects.get(name=rule_name)
            return rule
        except Rule.DoesNotExist:
            pass

    def _queue_task(self, message, rule, file_store: storage.Storage,
                    request: HttpRequest):
        '''
        Saves the file using
        the configured FileStorage class using the task.name with `.dat` at
        the end and then saves the task in the database.  Celery tasks)
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
        self._get_task_parameters(task, request)
        return task.name

    def _get_task_parameters(self, request: HttpRequest,
                             ignore=['run-immediately', 'format', 'rule']):
        '''
        Converts the GET parameters into Task parameters if supplied.
        Will ignore format, rule and run-immediately parameters.
        :param db_task: The Task to add parameters to.
        :param ignore: The list of get parameters to ignore.
        :return: None
        '''
        params = request.GET.dict()
        ret = []
        for k, v in params.items():
            if k not in ignore:
                ret.append(TaskParameter(
                    name=k,
                    value=v
                ))
        return ret


class TaskXMLRenderer(XMLRenderer):

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data


class GetTaskData(APIView):
    """
    Will return the data associated with a given task.
    """
    queryset = Task.objects.none()

    def get(self, request: Request, task_name: str = None, format=None):
        storage_class = storage.get_storage_class()
        django_storage = storage_class()
        file_name = '{0}.dat'.format(task_name)
        message_file = django_storage.open(file_name)
        data = message_file.read()
        response = HttpResponse(data, content_type='application/text')
        response['Content-Disposition'] = 'attachment; filename=%s' % file_name
        return response


class EPCISCapture(CaptureInterface):
    '''
    A more strict implementation of the EPCIS capture interface to
    meet requirements in section 10.2 of the EPCIS 1.2 protocol.
    '''
    queryset = Task.objects.none()

    def post(self, request: Request, format=None):
        return super().post(request, format, True)
