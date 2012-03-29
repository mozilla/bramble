import re
import datetime
from optparse import make_option
from django.core.management.base import BaseCommand

from bramble.base.redis_utils import redis_client
from bramble.base.machinecounts import (
  build_machinecounts, make_key, get_all_slave_names)


def process_date(date, slave_names, redis_source, redis_store,
                 dry_run=False,
                 quiet=False,
                 force_refresh=False):
    if not quiet:
        print (' %s ' % date).center(79, '=')

    successes_key = make_key('successes', date)
    failures_key = make_key('failures', date)
    idles_key = make_key('idles', date)
    if (redis_store.exists(successes_key) and
        redis_store.exists(failures_key) and
        redis_store.exists(idles_key)):
        # already processed this date
        if force_refresh:
            redis_store.delete(successes_key)
            redis_store.delete(failures_key)
            redis_store.delete(idles_key)
        else:
            if not quiet:
                print "Already processed this date"
            return

    data = build_machinecounts(
        date,
        redis_source=redis_source,
        redis_store=redis_store,
        slave_names=slave_names,
        dry_run=dry_run,
    )

    if not quiet:
        if data:
            print "SUCCESSES".ljust(25), len(data['successes'])
            print "FAILURES".ljust(25), len(data['failures'])
            print "IDLES".ljust(25), len(data['idles'])
            print "_UNKNOWN_SLAVES".ljust(25), len(data['_unknown_slaves'])
            print "_CHECK", len(slave_names), (len(data['successes'])
                                                + len(data['failures'])
                                                + len(data['idles'])
                                                - len(data['_unknown_slaves']))
        else:
            print "NO BUILD DATA AVAILABLE :("


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
        make_option('--force-refresh',
            action='store_true',
            dest='force_refresh',
            default=False,
            help="process it again even if we have the data"),
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
            process_date(date, slave_names, redis, redis_store,
                         dry_run=options['dryrun'],
                         quiet=not int(options['verbosity']),
                         force_refresh=options['force_refresh']
                         )
