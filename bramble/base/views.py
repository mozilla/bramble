import re
import logging
import time
import datetime
import functools
import anyjson as json
from django import http
from django.shortcuts import render
from redis_utils import redis_client
from bramble.base.machinecounts import (
  fetch_machine_info, build_machinecounts, make_key, format_date)

DEFAULT_RESOLUTION = 60 * 60  # 1 hours


class BuildDataError(Exception):
    pass


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


@json_view
def machinecounts(request):
    data = {}
    no_bars = int(request.GET.get('bars', 21))
    resolution = int(request.GET.get('resolution', DEFAULT_RESOLUTION))

    if request.GET.get('last'):
        last = parse_datetime(request.GET['last'])
    else:
        last = datetime.datetime.utcnow()
    redis_store = redis_client('bramble')

    dates = []
    for i in range(no_bars):
        next = last - datetime.timedelta(seconds=resolution)
        data = _get_machinecounts(next, last, redis_store)
        dates.append({
          'date': next.isoformat(),
          'working': len(data['successes']),
          'idle': len(data['idles']),
          'error': len(data['failures']),
        })
        last = next

    return {'dates': dates}


def _get_machinecounts(from_date, to_date, redis_store):
    date = from_date
    all_successes = set()
    all_failures = set()
    all_idles = set()

    while date < to_date:

        successes_key = make_key('successes', date)
        failures_key = make_key('failures', date)
        idles_key = make_key('idles', date)

        if not redis_store.exists(successes_key):
            logging.info(len(redis_store.smembers(successes_key)))
            logging.info("Have to fetch machinecounts for %s",
                         format_date(date))
            data = build_machinecounts(format_date(date),
                                       redis_store=redis_store)
            successes = data['successes']
            failures = data['failures']
            idles = data['idles']
        else:
            successes = redis_store.smembers(successes_key)
            failures = redis_store.smembers(failures_key)
            idles = redis_store.smembers(idles_key)

        # expand the union
        all_failures |= failures
        all_idles |= idles
        all_successes |= successes

        date += datetime.timedelta(seconds=60 * 60)

    all_successes -= all_failures
    all_idles -= all_failures
    all_idles -= all_successes

    return {
      'successes': all_successes,
      'failures': all_failures,
      'idles': all_idles,
    }


@json_view
def machinecounts_specifics(request):
    when = request.GET.get('when')  # a timestamp
    when = parse_datetime(when)
    resolution = int(request.GET.get('resolution', DEFAULT_RESOLUTION))
    from_ = when - datetime.timedelta(seconds=resolution)
    redis_store = redis_client('store')
    data = _get_machinecounts(from_, when, redis_store)
    data = {
      'working': list(data['successes']),
      'idle': list(data['idles']),
      'error': list(data['failures']),
    }
    return {'machines': data,
            'time': int(time.mktime(when.timetuple()))}

def parse_dtime(datestr):
    '''
    Parses a string of the format YYYY-MM-DD.HH and returns a datetime object
    '''
    _regex = re.compile('\d{4}-\d{2}-\d{2}\.\d{2}')
    _parsed = _regex.findall(datestr)
    if not _parsed:
        raise ValueError(datestr)
    datestring, hour = _parsed[0].split('.')
    year, month, day = datestring.split('-')
    return datetime.datetime(int(year), int(month), int(day), int(hour))

_timestamp_regex = re.compile('\d{13}|\d{10}\.\d{0,4}|\d{10}')

def parse_datetime(datestr):
    _parsed = _timestamp_regex.findall(datestr)
    if _parsed:
        datestr = _parsed[0]
        if len(datestr) >= len('1285041600000'):
            try:
                return datetime.datetime.fromtimestamp(float(datestr) / 1000)
            except ValueError:
                pass
        if len(datestr) >= len('1283140800'):
            try:
                return datetime.datetime.fromtimestamp(float(datestr))
            except ValueError:
                pass  # will raise
    raise ValueError(datestr)
