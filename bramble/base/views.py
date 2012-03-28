import re
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

        # more realistic (smoother) totals
        total = randint(1600, 1630)
        working = randint(1000, 1300)
        error = randint(100, 200)
        idle = total - working - error

        #XXXXXXXXXXXXXXXXXXXXXXXXX
        dates.append({
          'date': range_[0].isoformat(),
          'working': working,
          'idle': idle,
          'error': error,
        })
        last = _next

    return {'dates': dates}


@json_view
def machinecounts_specifics(request):
    when = request.GET.get('when')  # a timestamp
    when = parse_datetime(when)
    resolution = int(request.GET.get('resolution', 60 * 60))

    data = {
      'working': ['slave1', 'slave2', 'slave4'],
      'idle': ['slaveX', 'slaveY'],
      'error': ['slave0'],
    }
    return {'machines': data}


_timestamp_regex = re.compile('\d{13}|\d{10}\.\d{0,4}|\d{10}')
def parse_datetime(datestr):
    _parsed = _timestamp_regex.findall(datestr)
    if _parsed:
        datestr = _parsed[0]
        if len(datestr) >= len('1285041600000'):
            try:
                return datetime.datetime.fromtimestamp(float(datestr)/1000)
            except ValueError:
                pass
        if len(datestr) >= len('1283140800'):
            try:
                return datetime.datetime.fromtimestamp(float(datestr))
            except ValueError:
                pass # will raise
    raise DatetimeParseError(datestr)
