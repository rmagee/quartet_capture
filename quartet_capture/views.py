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

from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from rest_framework import exceptions

from quartet_capture.tasks import execute_rule

import logging

logger = logging.getLogger('quartet_capture')

class CaptureInterface(APIView):
    '''
    The view responsible for capturing the files and handing
    off the queuing to a celery task.
    '''
    # set the parser to handle HTTP post / upload
    parser_classes = (MultiPartParser,)

    def post(self, request: Request, format=None):
        logger.info('Message from %s', getattr(request.META, 'REMOTE_HOST',
                                               'Host Info not Available'))
        #get the rule from the query parameter
        rule_name = request.query_params.get('rule', None)
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
        message = request.FILES.get('file')
        if not message:
            raise exceptions.APIException(
                'No "file" field variable found in the HTTP POST data.  The '
                'multiform data must be posted with the name "file" as '
                'it\'s variable name.',
                status.HTTP_400_BAD_REQUEST
            )
        # execute the rule as a task in celery
        logger.debug('Executing rule %s', rule_name)
        execute_rule(message=message, rule_name=rule_name)
        return Response('Message was queued.')
