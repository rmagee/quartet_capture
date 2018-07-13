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
'''
Defines the Django Rest Framework model view sets for the API.
The url routes are established in the routers module and appended
to the urlparams in urls.py.
'''

from quartet_capture import models
from rest_framework import viewsets
from quartet_capture import serializers


class RuleViewSet(viewsets.ModelViewSet):
    queryset = models.Rule.objects.prefetch_related(
        'step_set',
    ).all()
    serializer_class = serializers.RuleSerializer


class RuleParameterViewSet(viewsets.ModelViewSet):
    queryset = models.RuleParameter.objects.all()
    serializer_class = serializers.RuleParameterSerializer


class StepViewSet(viewsets.ModelViewSet):
    queryset = models.Step.objects.prefetch_related(
        'stepparameter_set'
    ).all()
    serializer_class = serializers.StepSerializer


class StepParameterViewSet(viewsets.ModelViewSet):
    queryset = models.StepParameter.objects.all()
    serializer_class = serializers.StepParameterSerializer


class TaskViewset(viewsets.ModelViewSet):
    queryset = models.Task.objects.all()
    serializer_class = serializers.TaskSerializer
    search_fields = ['name', 'status', 'status_changed']

class TaskHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    '''
    CRUD ready model view for the TaskHistory model.
    '''
    queryset = models.TaskHistory.objects.all()
    serializer_class = serializers.TaskHistorySerializer
