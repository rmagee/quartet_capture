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
from rest_framework.routers import DefaultRouter
from quartet_capture import viewsets, views

router = DefaultRouter()
router.register(r'rules', viewsets.RuleViewSet, base_name='rules')
router.register(r'rule-parameters', viewsets.RuleParameterViewSet,
                base_name='rule-parameters')
router.register(r'steps', viewsets.StepViewSet, base_name='steps')
router.register(r'step-parameters', viewsets.StepParameterViewSet,
                base_name='step-parameters')
router.register(r'tasks', viewsets.TaskViewset, base_name='tasks')
router.register(r'task-history', viewsets.TaskHistoryViewSet,
                base_name='task-history')
urlpatterns = router.urls
