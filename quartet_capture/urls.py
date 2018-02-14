# -*- coding: utf-8 -*-
from django.conf.urls import url
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    url(
        regex="^message/~create/$",
        view=views.messageCreateView.as_view(),
        name='message_create',
    ),
    url(
        regex="^message/(?P<pk>\d+)/~delete/$",
        view=views.messageDeleteView.as_view(),
        name='message_delete',
    ),
    url(
        regex="^message/(?P<pk>\d+)/$",
        view=views.messageDetailView.as_view(),
        name='message_detail',
    ),
    url(
        regex="^message/(?P<pk>\d+)/~update/$",
        view=views.messageUpdateView.as_view(),
        name='message_update',
    ),
    url(
        regex="^message/$",
        view=views.messageListView.as_view(),
        name='message_list',
    ),
	]
