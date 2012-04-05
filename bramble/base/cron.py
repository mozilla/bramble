import cronjobs
import datetime
import logging

from machinecounts import get_all_slave_names
from redis_utils import redis_client
from functools import partial

@cronjobs.register
def derive_machine_info():
    date = datetime.datetime.utcnow() - datetime.timedelta(hours=12)
    derive_hourly_info(date)

def derive_hourly_info(date):
    """
    derives slave machine information from briar-patch and stores it in the
    bramble data store.

    creates a set, machine:yyyy-mm-dd, containing all the slave names for
    the provided date

    creates a hash machine:yyyy-mm-dd.slavename, for each slave in the
    provided list of slave names
    """
    redis_source = redis_client('briar-patch')
    redis_store = redis_client('bramble')
    slave_names = get_all_slave_names()

    # generate a key for today's machine info pool
    pool_key = make_info_pool_key(date)

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
        logging.warning("No build data for %s", date)

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

# redis key making functions, and related
def format_date(date):
    return date.strftime('%Y-%m-%d.%H')

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
