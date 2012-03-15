from django.conf.urls.defaults import *

import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='bramble.base.index'),
    url(r'^redis/', views.redis_info, name='bramble.base.redis_info'),
)
