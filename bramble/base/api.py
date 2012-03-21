import logging

import anyjson as json

from django.conf import settings as django_settings
from django.http import HttpResponse, HttpResponseBadRequest
from redis_utils import redis_client, RedisError


def get_builds(request):
    '''
    returns all known build uids

    params:
        :date - restrict result to builds on a particular day (optional)
                format YYYY-MM-DD
        :hour - restrict to builds in a particular hour (optional)
                format HH, valid iff the date is provided
    '''
    date_string = request.GET.get('date', None)
    hour_string = request.GET.get('hour', None)

    if hour_string and not date_string:
        return HttpResponseBadRequest(
                json.serialize({'message': 'hour option requires date'}),
                content_type="application/json")

    redis_key = "metrics.hashes"
    if date_string:
        if hour_string:
            date_string += "." + hour_string
        redis_key = "build:" + date_string

    try:
        r = redis_client('default')
        hashes = r.smembers(redis_key)
    except RedisError as e:
        log.error('redis error: %s', e)
        hashes = set()
    result = []
    for build_hash in hashes:
        verb, uid = build_hash.split(":")
        result.append(uid)
    return HttpResponse(json.serialize({'uids': result}),
            content_type="application/json")

def get_build(uid):
    return HttpResponse(content_type="application/json")

def get_changes():
    return HttpResponse(content_type="application/json")

def get_change():
    return HttpResponse(content_type="application/json")

def get_machines(event):
    return HttpResponse(content_type="application/json")
