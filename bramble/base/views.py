import datetime
import functools
import anyjson as json
from django import http
from django.conf import settings as django_settings
from django.shortcuts import render, render_to_response
from django.template import RequestContext

from redis_utils import redis_client


def json_view(f):
    @functools.wraps(f)
    def wrapper(*args, **kw):
        response = f(*args, **kw)
        if isinstance(response, http.HttpResponse):
            return response
        else:
            return http.HttpResponse(json.dumps(response),
                                     content_type='application/json')
    return wrapper


def index(request):
    data = {}
    return render(request, 'base/index.html', data)



@json_view
def machinecounts(request):
    data = {}
    no_bars = int(request.GET.get('bars', 21))
    resolution = int(request.GET.get('resolution', 60 * 60))

    last = datetime.datetime.utcnow()
    from random import randint
    dates = []
    for i in range(no_bars + 1):
        _next = last - datetime.timedelta(seconds=resolution)
        range_ = _next, last

        #....
        dates.append({
          'date': range_[0].isoformat(),
          'working': randint(10, 20),
          'idle': randint(2, 8),
          'error': randint(0, 5),
        })
        last = _next

    return {'dates': dates}
