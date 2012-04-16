import cronjobs
import datetime
import logging

from machinecounts import parse_dtime, derive_hourly_info, get_all_slave_names
from bramble.base.redis_utils import redis_client
from redis import ConnectionError


@cronjobs.register
def derive_machine_info(*args):
    '''
    derives machine information and stores it in redis.

    args:
        datetime_from - when to start from (optional)
                        default = utc_now() - 24hours
                        format: YYYY-MM-DD.HH

        datetime_to - when to run until (optional, NA without datetime_from)
                      default = utc_now()
                      format: YYYY-MM-DD.HH
    '''
    current = datetime.datetime.utcnow()
    last = current - datetime.timedelta(hours=24)
    if len(args) is 2:
        current = parse_dtime(args[1])
    if len(args) > 0:
        last = parse_dtime(args[0])

    if current < last:
        last, current = current, last

    # get all these once and reuse them
    # to reduce the risk of timeout during the while loop
    redis_source = redis_client('briar-patch')
    redis_store = redis_client('bramble')
    slave_names = get_all_slave_names()
    while current > last:
        retry_hourly_info_forever(current, redis_source, redis_store,
                                  slave_names)
        current -= datetime.timedelta(hours=1)

def retry_hourly_info_forever(current, redis_source, redis_store, slave_names):
    try:
        derive_hourly_info(current, redis_source, redis_store, slave_names)
    except ConnectionError:
        logging.warning("%s occured while deriving %s, retrying...",
                        ConnectionError, current)
        retry_hourly_info_forever(current, redis_source, redis_store,
                                  slave_names)
