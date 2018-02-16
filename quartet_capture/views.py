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
from rest_framework.parsers import FileUploadParser
from rest_framework.request import Request

from quartet_capture.tasks import handle_message

import logging
logger = logging.getLogger('quartet_capture')

class CaptureInterface(APIView):
    '''
    The view responsible for capturing the files and handing
    off the queuing to a celery task.
    '''
    # set the parser to handle HTTP post / upload
    parser_classes = (FileUploadParser,)

    def post(self, request: Request, format=None):
        logger.info('Message from %s', getattr(request.META['REMOTE_HOST'],
                                               'Host Info not Available'))
        message = request.FILES['file']

