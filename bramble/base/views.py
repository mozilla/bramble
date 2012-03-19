from django.conf import settings as django_settings
from django.shortcuts import render, render_to_response
from django.template import RequestContext

from redis_utils import redis_client

def index(request):
    data = {}
    return render(request, 'base/index.html', data)

def redis_info(request):
    """Admin view that displays redis INFO+CONFIG output for all backends."""
    redis_info = {}
    for key in django_settings.REDIS_BACKENDS.keys():
        redis_info[key] = {}
        client = redis_client(key)
        redis_info[key]['connection'] = django_settings.REDIS_BACKENDS[key]
        try:
            cfg = client.config_get()
            redis_info[key]['config'] = [{'key': k, 'value': cfg[k]} for k in
                                         sorted(cfg)]
            info = client.info()
            redis_info[key]['info'] = [{'key': k, 'value': info[k]} for k in
                                       sorted(info)]
        except ConnectionError:
            redis_info[key]['down'] = True

    return render_to_response('base/redis.html',
                              {'redis_info': redis_info,
                               'title': 'Redis Information'},
                              RequestContext(request, {}))
