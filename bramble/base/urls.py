from django.conf.urls.defaults import *

import api
import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='bramble.base.index'),
    url(r'^redis/$', views.redis_info, name='bramble.base.redis_info'),
    url(r'^builds/$', api.get_builds, name='bramble.base.get_builds'),
    url(r'^builds/(?P<uid>\w{32})/$', api.get_builds, name='bramble.base.get_build'),
)
