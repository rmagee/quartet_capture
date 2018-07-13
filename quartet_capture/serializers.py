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
# Copyright 2018 SerialLab LLC.  All rights reserved.
'''
This module defines the default serializers for the
rule framework model.
'''

from rest_framework.serializers import ModelSerializer
from quartet_capture import models


class StepParameterSerializer(ModelSerializer):
    class Meta:
        model = models.StepParameter
        fields = '__all__'


class StepSerializer(ModelSerializer):
    class Meta:
        model = models.Step
        fields = '__all__'


class RuleParameterSerializer(ModelSerializer):
    class Meta:
        model = models.RuleParameter
        fields = '__all__'


class RuleSerializer(ModelSerializer):
    step_set = StepSerializer(many=True, read_only=True)

    class Meta:
        model = models.Rule
        fields = '__all__'

class TaskMessageSerializer(ModelSerializer):
    '''
    Default serializer for the TaskMessage model.
    '''
    class Meta:
        model = models.TaskMessage
        fields = '__all__'

class TaskSerializer(ModelSerializer):
    taskmessage_set = TaskMessageSerializer(many=True, read_only=True)

    class Meta:
        model = models.Task
        fields = '__all__'

class TaskHistorySerializer(ModelSerializer):
    '''
    Default serializer for the TaskHistory model.
    '''
    class Meta:
        model = models.TaskHistory
        fields = '__all__'

