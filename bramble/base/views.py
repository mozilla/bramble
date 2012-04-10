import re
import logging
import time
import datetime
import functools
import anyjson as json
from django import http
from django.shortcuts import render
from redis_utils import redis_client
from bramble.base.machinecounts import fetch_machine_info, format_date


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
def machine_details(request):
    data = {}
    last = parse_dtime(request.GET.get('from', None))
    current = parse_dtime(request.GET.get('to', None))
    if current < last:
        last, current = current, last

    redis_store = redis_client('bramble')

    data = []
    while current > last:
        data.extend(fetch_machine_info(current, redis_store))
        current -= datetime.timedelta(hours=1)
    return {'machines': data}


def parse_dtime(datestr):
    '''
    Parses a string of the format YYYY-MM-DD.HH and returns a datetime object
    '''
    _regex = re.compile('^\d{4}-\d{2}-\d{2}\.\d{2}$')
    _parsed = _regex.findall(datestr)
    if not _parsed:
        raise ValueError(datestr)
    datestring, hour = _parsed[0].split('.')
    year, month, day = datestring.split('-')
    return datetime.datetime(int(year), int(month), int(day), int(hour))
