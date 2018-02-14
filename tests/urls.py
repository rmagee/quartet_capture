# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from django.conf.urls import url, include

from quartet_capture.urls import urlpatterns as quartet_capture_urls

app_name = 'quartet_capture'

urlpatterns = [
    url(r'^', include(quartet_capture_urls)),
]
