import datetime
import logging
import urllib
import re

import anyjson as json
from functools import partial
from django.conf import settings
from bramble.base.redis_utils import redis_client


def make_key(prefix, postfix):
    '''
    makes a redis key. if postfix is not a string, we assume its a datetime
    object and coerce it to a properly formatted string.
    '''
    if not isinstance(postfix, basestring):
        postfix = format_date(postfix)
    return '%s:%s' % (prefix, postfix)


make_builds_key = partial(make_key, 'build')
make_info_pool_key = partial(make_key, 'machines')


def make_info_key(date, slavename):
    return make_info_pool_key(date) + "." + slavename


def format_date(dt):
    return dt.strftime('%Y-%m-%d.%H')


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


def get_all_slave_names():
    key = 'all-slave-names'
    content = urllib.urlopen(settings.SLAVES_API_URL).read()
    return [x['name'] for x in json.loads(content)]


def build_machine_info(dt, redis_source=None, redis_store=None,
                       slave_names=None):
    """
    derives slave machine information from briar-patch and stores it in the
    bramble data store.

    creates a set, machine:yyyy-mm-dd.hh, containing all the slave names for
    the provided datetime, dt

    creates a hash machine:yyyy-mm-dd.hh.slavename, for each slave in the
    provided list of slave names
    """
    if not redis_source:
        redis_source = redis_client('briar-patch')
    if not redis_store:
        redis_store = redis_client('bramble')
    if not slave_names:
        slave_names = get_all_slave_names()

    _builds_key = make_builds_key(dt)
    if not redis_source.exists(_builds_key):
        logging.warning("No build data for %s", _builds_key)

    machine_day = make_info_pool_key(dt)

    # put all slaves into hashes hash scaffolding
    for slave in slave_names:
        redis_store.hmset(make_info_key(dt, slave), {
            'scheduler': '',
            'master': '',
            'platform': '',
            'successes': 0,
            'failures': 0,
        })
        redis_store.sadd(machine_day, slave)

    for build in redis_source.smembers(_builds_key):
        if 'None' in build:
            continue
        type_, builduid = build.split(':')
        _jobs_key = 'build:%s' % builduid
        for job_key in redis_source.smembers(_jobs_key):
            job = redis_source.hgetall(job_key)
            slave = job['slave']

            # create the machine key and machine value objects
            machine_key = make_info_key(dt, slave)

            if not redis_store.sismember(machine_day, machine_key):
                logging.warning("%s not in master slave list, skipping",
                               machine_key)
                continue
            else:
                logging.warning("%s is in master slave list")

            redis_source.hmset(machine_key, {
                'scheduler': job['scheduler'],
                'master': job['master'],
                'platform': job['platform'],
            })

            if job['results'] is "0":
                redis_source.hincrby(machine_key, 'successes')
            else:
                redis_source.hincrby(machine_key, 'failures')


def fetch_machine_info(dt, redis_store=None):
    '''
    returns a list of machine data from the redis store for the provided
    datetime, dt
    '''
    if not redis_store:
        redis_store = redis_client('bramble')

    machines = []
    for slave in redis_store.smembers(make_info_pool_key(dt)):
        machine_key = make_info_key(dt, slave)
        machine_info = redis_store.hgetall(machine_key)
        machine_info.update({
            'name': slave,
            'datetime': format_date(dt),
        })
        machines.append(machine_info)

    return machines


def derive_hourly_info(date, redis_source=None, redis_store=None,
                        slave_names=None):
    """
    derives slave machine information from briar-patch and stores it in the
    bramble data store.

    creates a set, machine:yyyy-mm-dd.hh, containing all the slave names for
    the provided date

    creates a hash machine:yyyy-mm-dd.hh.slavename, for each slave in the
    provided list of slave names
    """
    if not redis_source:
        redis_source = redis_client('briar-patch')
    if not redis_store:
        redis_store = redis_client('bramble')
    if not slave_names:
        slave_names = get_all_slave_names()

    # generate a key for today's machine info pool
    pool_key = make_info_pool_key(date)

    # clean out any previously calculated data
    for slave in redis_store.smembers(pool_key):
        redis_store.delete(make_info_key(date, slave))
    redis_store.delete(pool_key)

    # put all slaves into the pool, add hash scaffolding
    for slave in slave_names:
        redis_store.sadd(pool_key, slave)
        redis_store.hmset(make_info_key(date, slave), {
            'scheduler': '',
            'master': '',
            'platform': '',
            'successes': 0,
            'failures': 0,
        })

    _builds_key = make_builds_key(date)
    if not redis_source.exists(_builds_key):
        logging.warning("No build data for %s", _builds_key)
        return
    logging.warning("deriving data for %s", _builds_key)

    for build in redis_source.smembers(_builds_key):
        if 'None' in build:
            continue
        type_, builduid = build.split(':')
        _jobs_key = make_builds_key(builduid)
        for job_key in redis_source.smembers(_jobs_key):
            job = redis_source.hgetall(job_key)
            slave = job['slave']

            # create the machine key and machine value objects
            machine_key = make_info_key(date, slave)
            if not redis_store.exists(machine_key):
                logging.warning("%s not in master slave list, skipping",
                               machine_key)
                continue

            try:
                for key in ['scheduler', 'master', 'platform']:
                    redis_store.hmset(machine_key, {key: job[key]})
            except KeyError:
                logging.warning("%s not found in latest job for slave %s",
                              key, slave)

            if job['results'] is "0":
                redis_store.hincrby(machine_key, 'successes')
            else:
                redis_store.hincrby(machine_key, 'failures')
