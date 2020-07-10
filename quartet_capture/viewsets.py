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

from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import viewsets
from django.db.models import Q
from quartet_capture import serializers
from quartet_capture import models

class RuleViewSet(viewsets.ModelViewSet):
    queryset = models.Rule.objects.prefetch_related(
        'step_set',
    ).all()
    serializer_class = serializers.RuleSerializer

    def list(self, request, *args, **kwargs):
        """
        Refactored to support searching steps from the rule
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        try:
            search = request.GET['search']
            order_by = request.GET['ordering']
        except Exception:
            # just set search to none, this is not a search.
            search = None
        if search is not None:
            queryset = self.queryset.filter(
                  Q(name__contains=search) |
                  Q(description__contains=search)).order_by(order_by)
            if len(queryset) == 0:
                # Search the steps
                queryset = models.Rule.objects.prefetch_related('step_set').filter(
                    Q(step__name__contains=search) |
                    Q(step__description__contains=search) |
                    Q(step__step_class__contains=search)).order_by(order_by)
        else:
            # this isn't a search so use the class' queryset, as is.
            queryset = self.queryset

        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)



class RuleParameterViewSet(viewsets.ModelViewSet):
    queryset = models.RuleParameter.objects.all()
    serializer_class = serializers.RuleParameterSerializer


class StepViewSet(viewsets.ModelViewSet):
    queryset = models.Step.objects.prefetch_related(
        'stepparameter_set'
    ).all()
    serializer_class = serializers.StepSerializer

    def retrieve(self, request, pk=None):
        step = get_object_or_404(self.queryset, pk=pk)
        serializer = serializers.StepSerializer(step)
        ret_val = Response(serializer.data)
        return ret_val

class StepParameterViewSet(viewsets.ModelViewSet):
    queryset = models.StepParameter.objects.all()
    serializer_class = serializers.StepParameterSerializer


class TaskViewset(viewsets.ModelViewSet):
    queryset = models.Task.objects.all()
    serializer_class = serializers.TaskSerializer
    search_fields = ['name', 'status', 'status_changed', 'rule__name']

class TaskHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    '''
    CRUD ready model view for the TaskHistory model.
    '''
    queryset = models.TaskHistory.objects.all()
    serializer_class = serializers.TaskHistorySerializer

class FilterViewSet(viewsets.ModelViewSet):
    '''
    CRUD ready model view for the Filter model.
    '''
    queryset = models.Filter.objects.prefetch_related('rulefilter_set').all()
    serializer_class = serializers.FilterSerializer

class RuleFilterViewSet(viewsets.ModelViewSet):
    '''
    CRUD ready model view for the RuleFilter model.
    '''
    queryset = models.RuleFilter.objects.all()
    serializer_class = serializers.RuleFilterSerializer

