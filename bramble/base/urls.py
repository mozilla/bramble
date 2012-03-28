from django.conf.urls.defaults import *

import api
import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='bramble.base.index'),
    url(r'^machinecounts/$', views.machinecounts, name='bramble.base.machinecounts'),
    url(r'^builds/$', api.get_builds, name='bramble.base.get_builds'),
    url(r'^builds/(?P<uid>\w{32})/jobs$', api.get_build_jobs,
        name='bramble.base.get_build_jobs'),
    url(r'^builds/(?P<uid>\w{32})/changeset$', api.get_changeset_info,
        name='bramble.base.get_changeset_info'),
    url(r'^machines/events/(?P<event_type>\w+)/$', api.get_machine_events,
        name='bramble.base.get_machine_events'),
    url(r'^jobs/(?P<uid>\w{32})/(?P<master>\w{8}-\w+)/(?P<build_number>\d+)/$', api.get_job_info,
        name='bramble.base.get_job_info'),
)
