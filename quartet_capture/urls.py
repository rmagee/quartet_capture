# -*- coding: utf-8 -*-
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

from django.conf.urls import url
from . import views
from quartet_capture.routers import urlpatterns as route_patterns

app_name = 'quartet_capture'

# the capture URL is versioned at v1
urlpatterns = [
    url(r'^quartet-capture/$',
        views.CaptureInterface.as_view(),
        name='quartet-capture'),
    url(r'^epcis-capture/$',
        views.EPCISCapture.as_view(),
        name='epcis-capture'),
    url(r'^execute/$',
        views.ExcuteTaskView.as_view(),
        name='execute'),
    url(r'^execute/(?P<task_name>[a-zA-Z0-9\-]{1,40})/?$',
        views.ExcuteTaskView.as_view(),
        name='execute-task'),
    url(r'^task-data/(?P<task_name>[a-zA-Z0-9\-]{1,40})/?$',
        views.GetTaskData.as_view(),
        name='task-data'),
    url(r'^clone-rule/$',
        views.CloneRuleView.as_view(),
        name='clone'),
    url(
        r'^clone-rule/(?P<rule_name>[0-9a-zA-Z\W\s]*)/(?P<new_rule_name>[0-9a-zA-Z\W\s]*)/$',
        views.CloneRuleView.as_view(),
        name='clone-rule')
]

urlpatterns += route_patterns
