import re
import logging
import datetime
import anyjson as json
from optparse import make_option
from django.core.cache import cache
from django.core.management.base import BaseCommand

from bramble.base.redis_utils import redis_client

SLAVES_API_URL = 'http://slavealloc.build.mozilla.org/api/slaves'


def get_all_slave_names():
    key = 'all-slave-names'
    value = cache.get(key)
    if value is None:
        from urllib import urlopen
        content = urlopen(SLAVES_API_URL).read()
        parsed = json.loads(content)
        value = [x['name'] for x in parsed]
        cache.set(key, value, 60 * 60)
    return value


def cache_redis_op(r, command, arg, exp=60):
    key = 'r:%s:%s' % (command, arg)
    value = cache.get(key)
    if value is None:
        value = getattr(r, command)(arg)
        if value is not None:
            cache.set(key, value, exp)
    return value


def process_date(date, slave_names, redis_source, redis_store,
                  dry_run=False, quiet=False):
    if not quiet:
        print (' %s ' % date).center(79, '=')

    successes = set()
    failures = set()
    _success_and_failure = set()
    _unknown_slaves = set()

    _builds_key = 'build:%s' % date
    if not quiet:
        print "Going through", redis_source.scard(_builds_key), "builds"
    for each in cache_redis_op(redis_source, 'smembers', _builds_key):
        if 'None' in each:
            continue
        type_, builduid = each.split(':')
        _jobs_key = 'build:%s' % builduid
        for job_key in cache_redis_op(redis_source, 'smembers', _jobs_key):
            job = cache_redis_op(redis_source, 'hgetall', job_key)
            slave = job['slave']
            if slave not in slave_names:
                _unknown_slaves.add(slave)
            result = int(job['results'])

            if result:
                failures.add(slave)
            else:
                successes.add(slave)

    _success_and_failure = successes & failures
    successes -= failures

    # the rest are considered idles in that hour
    idles = set(slave_names) - successes - failures

    # save it all
    if not dry_run:
        successes_key = 'successes:%s' % date
        [redis_store.sadd(successes_key, each) for each in successes]
        failures_key = 'failures:%s' % date
        [redis_store.sadd(failures_key, each) for each in failures]
        idles_key = 'idles:%s' % date
        [redis_store.sadd(idles_key, each) for each in idles]

    if not quiet:
        print "SUCCESSES".ljust(25), len(successes)
        print "FAILURES".ljust(25), len(failures)
        print "IDLES".ljust(25), len(idles)
        print "_SUCCESS_AND_FAILURE".ljust(25), len(_success_and_failure)
        print "_UNKNOWN_SLAVES".ljust(25), len(_unknown_slaves)
        print "_CHECK", len(slave_names), (len(successes)
                                            + len(failures)
                                            + len(idles)
                                            - len(_unknown_slaves))


class Command(BaseCommand):
    """
    This command updates our Redis store with build information about which
    slaves (aka. machines) are successful, failing or idle within 1 hour.

    Note that it reads data from one Redis db and writes to another.

    The idea is that this command can be run once an hour by cron and if you
    need to backfill you simply call it with the --date parameter.

    Note2 All read operations are (at the time of writing) proxy cached using
    the Django cache framework (which almost ironically writes to a third
    Redis). This only really helps when in debug mode because you want to
    minimize the number of excessive reads from the remote Redis.
    XXX Consider moving this to an optional parameter.

    """
    args = '[date1, [date2, ...]]'
    option_list = BaseCommand.option_list + (
        make_option('--dry-run',
            action='store_true',
            dest='dryrun',
            default=False,
            help="don't save anything"),
        )

    def handle(self, *dates, **options):
        redis = redis_client('default')
        redis_store = redis_client('store')

        if not dates:
            dates = [(datetime.datetime.utcnow()
                      .strftime('%Y-%m-%d.%H'))]
        for date in dates:
            assert re.findall('\.\d{1,2}$', date)  # must end in .HH or .H

        slave_names = get_all_slave_names()
        assert slave_names
        assert len(slave_names) == len(set(slave_names))
        for date in dates:
            logging.debug("Processing machine counts for %s" % date)
            process_date(date, slave_names, redis, redis_store,
                         dry_run=options['dryrun'],
                         quiet=not int(options['verbosity']),
                         )
