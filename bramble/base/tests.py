import time
import datetime
import os
import anyjson as json
from django.test import TestCase
from django.conf import settings
from django.core.urlresolvers import reverse
from bramble.base.redis_utils import redis_client

fixture_file_location = os.path.join(os.path.dirname(__file__),
                                     'slaves_test_fixture.json')


class MachinecountsTestCase(TestCase):

    def setUp(self):
        super(MachinecountsTestCase, self).setUp()
        settings.SLAVES_API_URL = 'file://' + fixture_file_location

        settings.REDIS_BACKENDS = {
          'briar-patch': 'redis://localhost:6379?socket_timeout=0.5&db=6',
          'bramble': 'redis://localhost:6379?socket_timeout=0.5&db=7',
        }

        self.redis_store = redis_client('bramble')
        self.redis_store.flushdb()
        self.redis_source = redis_client('briar-patch')
        self.redis_source.flushdb()

        from django.core.cache import cache
        cache.clear()

    def tearDown(self):
        super(MachinecountsTestCase, self).setUp()
        self.redis_store.flushdb()
        self.redis_source.flushdb()

    def test_machinecounts_1_hour_resolution(self):
        date = datetime.datetime(2012, 1, 1, 1, 0)
        assert not self.redis_source.smembers('build:2012-01-01.01')
        url = reverse('bramble.base.machinecounts')

        # populate some stuff in the so the test makes sense
        k = 'build:2012-01-01.00'
        self.redis_source.sadd(k, 'job:builduidA1')
        self.redis_source.sadd(k, 'job:builduidA2')
        self.redis_source.sadd(k, 'job:None')  # junk
        j = 'build:builduidA1'
        self.redis_source.sadd(j, 'job:1:A1')
        self.redis_source.sadd(j, 'job:1:A2')
        self.redis_source.hmset('job:1:A1',
                                {'slave': 'slave1', 'results': '0'})
        self.redis_source.hmset('job:1:A2',
                                {'slave': 'slave3', 'results': '1'})

        timestamp = int(time.mktime(date.timetuple()))
        response = self.client.get(url, {
            'last': timestamp,
            'bars': 1,
            'resolution': 60 * 60
        })
        self.assertEqual(response.status_code, 200)
        structure = json.loads(response.content)
        dates = structure['dates']
        self.assertEqual(len(dates), 1)  # 1 bar
        self.assertEqual(dates[0]['date'], u'2012-01-01T00:00:00')
        self.assertEqual(dates[0]['working'], 1)
        self.assertEqual(dates[0]['error'], 1)
        self.assertEqual(dates[0]['idle'], 3)

        # ask for it a second time and we should expect the same result
        response = self.client.get(url, {
            'last': timestamp,
            'bars': 1,
            'resolution': 60 * 60
        })
        self.assertEqual(response.status_code, 200)
        structure = json.loads(response.content)
        second_time_dates = structure['dates']
        self.assertEqual(second_time_dates, dates)

        # get the specifics out
        url = reverse('bramble.base.machinecounts_specifics')
        response = self.client.get(url, {
            'when': timestamp,
            'resolution': 60 * 60
        })
        self.assertEqual(response.status_code, 200)
        structure = json.loads(response.content)
        data = structure['machines']
        # use sorted() because sets are not ordered
        self.assertEqual(data['working'], ['slave1'])
        self.assertEqual(data['error'], ['slave3'])
        self.assertEqual(sorted(data['idle']),
                         ['slave2', 'slave4', 'slave5'])
        self.assertEqual(timestamp, structure['time'])

    def test_machinecounts_6_hour_resolution(self):
        date = datetime.datetime(2012, 1, 1, 6, 0)
        url = reverse('bramble.base.machinecounts')

        # populate some stuff in the so the test makes sense
        ## 0th hour
        # 1 working slave
        i = 0
        k = 'build:2012-01-01.0%d' % i
        self.redis_source.sadd(k, 'job:builduidA1')
        j = 'build:builduidA1'
        self.redis_source.sadd(j, 'job:%s:A1' % i)
        self.redis_source.hmset('job:%s:A1' % i,
                                {'slave': 'slave1', 'results': '0'})

        ## 1th hour
        # 1 failing slave
        i = 1
        k = 'build:2012-01-01.0%d' % i
        self.redis_source.sadd(k, 'job:builduidA1')
        j = 'build:builduidA1'
        self.redis_source.sadd(j, 'job:%s:A2' % i)
        self.redis_source.hmset('job:%s:A2' % i,
                                {'slave': 'slave3', 'results': '1'})

        ## 2th hour
        # everything idle

        ## 3th hour
        # 1 working, 1 failing
        i = 3
        k = 'build:2012-01-01.0%d' % i
        self.redis_source.sadd(k, 'job:builduidA1')
        j = 'build:builduidA1'
        self.redis_source.sadd(j, 'job:%s:A1' % i)
        self.redis_source.hmset('job:%s:A1' % i,
                                {'slave': 'slave2', 'results': '1'})
        self.redis_source.sadd(j, 'job:%s:A2' % i)
        self.redis_source.hmset('job:%s:A2' % i,
                                {'slave': 'slave4', 'results': '0'})

        ## 4th hour
        # everything idle again

        ## 5th hour
        # 1 failing that previously worked
        i = 4
        k = 'build:2012-01-01.0%d' % i
        self.redis_source.sadd(k, 'job:builduidA1')
        j = 'build:builduidA1'
        self.redis_source.sadd(j, 'job:%s:A1' % i)
        self.redis_source.hmset('job:%s:A1' % i,
                                {'slave': 'slave1', 'results': '3'})

        timestamp = int(time.mktime(date.timetuple()))
        response = self.client.get(url, {
            'last': timestamp,
            'bars': 1,
            'resolution': 60 * 60 * 6
        })
        self.assertEqual(response.status_code, 200)
        structure = json.loads(response.content)
        dates = structure['dates']
        self.assertEqual(len(dates), 1)  # 1 bar
        self.assertEqual(dates[0]['date'], u'2012-01-01T00:00:00')
        self.assertEqual(dates[0]['working'], 1)
        self.assertEqual(dates[0]['error'], 3)
        self.assertEqual(dates[0]['idle'], 1)

        # and do it again a second time and expect it to return the same
        response = self.client.get(url, {
            'last': timestamp,
            'bars': 1,
            'resolution': 60 * 60 * 6
        })
        self.assertEqual(response.status_code, 200)
        structure = json.loads(response.content)
        second_time_dates = structure['dates']
        self.assertEqual(second_time_dates, dates)

        # get the specifics out
        url = reverse('bramble.base.machinecounts_specifics')
        response = self.client.get(url, {
            'when': timestamp,
            'resolution': 60 * 60 * 6
        })
        self.assertEqual(response.status_code, 200)
        structure = json.loads(response.content)
        data = structure['machines']
        # use sorted() because sets are not ordered
        self.assertEqual(data['working'], ['slave4'])
        self.assertEqual(sorted(data['error']),
                         ['slave1', 'slave2', 'slave3'])
        self.assertEqual(sorted(data['idle']),
                         ['slave5'])
