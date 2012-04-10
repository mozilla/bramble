import logging
import urllib
import anyjson as json
from django.conf import settings
from bramble.base.redis_utils import redis_client


def make_info_key(date, slavename=None):
    if not isinstance(date, basestring):
        date = format_date(date)
    key = 'machines:%s' % date
    if slavename:
        key += ".%s" % slavename
    return key


def make_builds_key(date):
    if not isinstance(date, basestring):
        date = format_date(date)
    return 'build:%s' % (date)


def format_date(date):
    return date.strftime('%Y-%m-%d.%H')


def get_all_slave_names():
    key = 'all-slave-names'
    content = urllib.urlopen(settings.SLAVES_API_URL).read()
    return [x['name'] for x in json.loads(content)]


def build_machine_info(date, redis_source=None, redis_store=None,
                       slave_names=None):
    """
    derives slave machine information from briar-patch and stores it in the
    bramble data store.

    creates a set, machine:yyyy-mm-dd, containing all the slave names for
    the provided date

    creates a hash machine:yyyy-mm-dd.slavename, for each slave in the
    provided list of slave names
    """
    if not redis_source:
        redis_source = redis_client('briar-patch')
    if not redis_store:
        redis_store = redis_client('bramble')
    if not slave_names:
        slave_names = get_all_slave_names()

    _builds_key = make_builds_key(date)
    if not redis_source.exists(_builds_key):
        logging.warning("No build data for %s", date)

    machine_day = make_info_key(date)

    # put all slaves into hashes hash scaffolding
    for slave in slave_names:
        redis_store.hmset(make_info_key(date, slave), {
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
            machine_key = make_info_key(date, slave)

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


def fetch_machine_info(date, redis_store=None):
    '''
    returns a list of machine data from the redis store for the provided date
    '''
    if not redis_store:
        redis_store = redis_client('bramble')

    machines = []
    for slave in redis_store.smembers(make_info_key(date)):
        machine_key = make_info_key(date, slave)
        machine_info = redis_store.hgetall(machine_key)
        machine_info.update({
            'name': slave,
            'date': format_date(date),
        })
        machines.append(machine_info)

    return machines
