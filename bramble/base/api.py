import logging

import anyjson as json

from django.conf import settings as django_settings
from django.http import HttpResponse, HttpResponseBadRequest
from redis_utils import redis_client, RedisError

log = logging.getLogger(__name__)

def get_builds(request):
    '''
    url handler that returns all known build uids

    request params:
        :date -    restrict result to builds on a particular day (optional)
                   format YYYY-MM-DD
        :hour -    restrict to builds in a particular hour (optional)
                   format HH, valid iff the date is provided
        :changes - if true, restrict to builds with source changes
                   (optional), valid iff date or date and time provided
    '''
    date_string = request.GET.get('date', None)
    hour_string = request.GET.get('hour', None)
    changesets = request.GET.get('changes', None)

    if hour_string and not date_string:
        return HttpResponseBadRequest(
                json.serialize({'message': 'hour option requires date'}),
                content_type="application/json")

    redis_key = "metrics.hashes"
    if date_string:
        if hour_string:
            date_string += "." + hour_string
        redis_key = "change:" if changesets else "build:"
        redis_key += date_string

    try:
        r = redis_client('default')
        hashes = r.smembers(redis_key)
    except RedisError as e:
        log.error('redis error: %s', e)
        hashes = set()
    result = []
    for h in hashes:
        t,u = h.split(':')
        result.append({'type': t, 'uid': u})
    return HttpResponse(json.serialize([result]),
            content_type="application/json")


def get_build_jobs(request, uid=None):
    """
    url handler that returns a list of jobs spawned by a specific build uid

    uid - the 32 digit alphanumeric build uid
    """
    if not uid:
        return HttpResponseBadRequest(
                json.serialize({'message': 'valid uid required'}),
                content_type="application/json")
    redis_key = "build:%s" % (uid)
    try:
        r = redis_client('default')
        hashes = r.smembers(redis_key)
    except RedisError as e:
        log.error('redis error: %s', e)
        hashes = set()
    result = []
    for build_hash in hashes:
        t, job_info = build_hash.split(":")
        uid, master, build_number = job_info.split(".")
        result.append({'type': t, 'uid': uid, 'master': master,
                        'build_number': build_number})
    return HttpResponse(json.serialize(result),
            content_type="application/json")


def get_changeset_info(request, uid=None):
    """
    url handler that returns an object with changeset information for a
    particular build uid

    uid - the 32 digit alphanumeric build uid
    """
    if not uid:
        return HttpResponseBadRequest(
                json.serialize({'message': 'valid uid required'}),
                content_type="application/json")
    redis_key = "change:%s" % (uid)
    try:
        r = redis_client('default')
        changeset_info = r.hgetall(redis_key)
    except RedisError as e:
        log.error('redis error: %s', e)
        changeset_info = {}
    return HttpResponse(json.serialize(changeset_info),
            content_type="application/json")


def get_machine_events(request, event_type=None):
    """
    url handler that returns machine events and counts for how often they
    have occured

    event_type - restrict event types to one of `connect`, `disconnect`,
                 'build'
    """
    if event_type not in ('connect', 'disconnect', 'build'):
        return HttpResponseBadRequest(
                json.serialize({'message': ('event_type must be one of',
                                '`connect`, `disconnect`, or `builds`')}),
                                content_type="application/json")
    redis_key = "metrics:%s" % (event_type)
    try:
        r = redis_client('default')
        events = r.hgetall(redis_key)
    except RedisError as e:
        log.error('redis error: %s', e)
        events = {}
    metrics = []
    for k, v in events.iteritems():
        event, machine = k.rsplit(':', 1)
        if event_type is 'build':
            t, event = event.split(':')
        else:
            t = "machine"
        metrics.append({'type': t, 'event': event, 'count': v,
                        'machine_name': machine})
    return HttpResponse(json.serialize(metrics),
                        content_type="application/json")


def get_job_info(request, uid=None, master=None, build_number=None):
    """
    url handler that returns all information about a job, pulled from the Pulse
    stream

    uid          - the build uid for the job
    master       - the master managing the jobs
    build_number - the build number
    """
    if not (uid and master and build_number):
        return HttpResponseBadRequest(
                json.serialize({"message": ("uid, master, and buildnumber are",
                                "required")}), content_type="application/json")
    redis_key = "job:%s.%s.%s" % (uid, master, build_number)
    try:
        r = redis_client('default')
        job = r.hgetall(redis_key)
    except RedisError as e:
        log.error('redis error: %s', e)
        job = {}
    return HttpResponse(json.serialize(job), content_type="application/json")
