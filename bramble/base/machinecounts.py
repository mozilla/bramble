import logging
import urllib
import anyjson as json
from django.core.cache import cache
from django.conf import settings
from bramble.base.redis_utils import redis_client


def make_key(prefix, date):
    if not isinstance(date, basestring):
        date = format_date(date)
    return 'machinecounts:%s:%s' % (prefix, date)


def format_date(date):
    return date.strftime('%Y-%m-%d.%H')


def get_all_slave_names(cache_expires=60 * 60):
    key = 'all-slave-names'
    value = cache.get(key)
    if value is None:
        content = urllib.urlopen(settings.SLAVES_API_URL).read()
        parsed = json.loads(content)
        value = [x['name'] for x in parsed]
        cache.set(key, value, cache_expires)
    return value


def build_machinecounts(date,
                        redis_source=None,  # where we read
                        redis_store=None,   # where we write
                        slave_names=None,   # list of ALL possible slave names
                        dry_run=False,      # don't actually write
                        ):
    if not redis_source:
        redis_source = redis_client('briar-patch')
    if not redis_store:
        redis_store = redis_client('bramble')
    if not slave_names:
        slave_names = get_all_slave_names()

    successes_key = make_key('successes', date)
    failures_key = make_key('failures', date)
    idles_key = make_key('idles', date)

    successes = set()
    failures = set()
    _unknown_slaves = set()

    _builds_key = 'build:%s' % date
    if not redis_source.exists(_builds_key):
        logging.warning("No build data for %s", date)
    for each in redis_source.smembers(_builds_key):
        if 'None' in each:
            continue
        type_, builduid = each.split(':')
        _jobs_key = 'build:%s' % builduid
        for job_key in redis_source.smembers(_jobs_key):
            job = redis_source.hgetall(job_key)
            slave = job['slave']
            try:
                result = int(job['results'])
            except ValueError:
                logging.warn('malformed result value for job: %s', job_key)
                continue

            if slave not in slave_names:
                _unknown_slaves.add(slave)
            if result:
                failures.add(slave)
            else:
                successes.add(slave)

    successes -= failures

    # the rest are considered idles in that hour
    idles = set(slave_names) - successes - failures

    # save it all
    if not dry_run:
        [redis_store.sadd(successes_key, each) for each in successes]
        [redis_store.sadd(failures_key, each) for each in failures]
        [redis_store.sadd(idles_key, each) for each in idles]

    result = {
        'successes': successes,
        'failures': failures,
        'idles': idles,
        '_unknown_slaves': _unknown_slaves,
    }
    return result
