from reding.app import app
import unittest
import json
import redis
from datetime import datetime
from dateutil import parser as dtparser
import pytz


class RedingTestCase(unittest.TestCase):

    user_vote_dates = {}

    def setUp(self):
        self.app = app.test_client()
        self.redis = redis.StrictRedis()

    def _test_get(self, url):
        r = self.app.get(url)
        self.assertEqual(r.status_code, 200, msg=r.data)
        self.assertEqual(r.mimetype, 'application/json')
        return r

    def _test_delete(self, url):
        r = self.app.delete(url)
        self.assertEqual(r.status_code, 204, msg=r.data)
        self.assertEqual(r.mimetype, 'application/json')
        return r

    def _test_post_or_put(self, url, headers, data, put=False):
        if not put:
            r = self.app.post(url, headers=headers, data=data)
        else:
            r = self.app.put(url, headers=headers, data=data)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.mimetype, 'application/json')
        return r

    def _check_post(self, response, object_id, user_id, vote):
        now = datetime.utcnow().replace(tzinfo=pytz.utc)
        resp = json.loads(response.data)
        self.assertEqual(resp['object_id'], object_id)
        self.assertEqual(resp['user_id'], user_id)
        self.assertEqual(resp['vote'], vote)
        self.user_vote_dates[user_id] = resp['when']
        dt = dtparser.parse(resp['when'])
        self.assertLessEqual(now, dt)

    def test_00_voted_list_resource_empty(self):
        self.redis.flushdb()
        response = self._test_get('/objects/')
        self.assertEqual(json.loads(response.data), [])

    def test_01_vote_summary_resource_first_vote(self):
        url_parts = {
            u'object_id': u'978-0132678209',
            u'user_id': u'gsalluzzo',
        }
        headers = []
        data = {
            u'vote': 10,
        }
        response = self._test_post_or_put(
            '/objects/{object_id}/users/{user_id}/'.format(**url_parts),
            headers,
            data,
        )
        data.update(url_parts)
        self._check_post(response, **data)

    def test_02_vote_summary_resource_correct_vote(self):
        url_parts = {
            u'object_id': u'978-0132678209',
            u'user_id': u'gsalluzzo',
        }
        headers = []
        data = {
            u'vote': 9,
        }
        response = self._test_post_or_put(
            '/objects/{object_id}/users/{user_id}/'.format(**url_parts),
            headers,
            data,
            put=True,
        )
        data.update(url_parts)
        self._check_post(response, **data)

    def test_03_voted_list_resource_check_first_vote(self):
        response = self._test_get('/objects/')
        expected = [
            {
                u'amount': 9,
                u'average': u'9.0',
                u'object_id': u'978-0132678209',
                u'votes_no': 1,
            }
        ]
        self.assertEqual(json.loads(response.data), expected)

    def test_04_vote_summary_resource_second_vote(self):
        url_parts = {
            u'object_id': u'978-0132678209',
            u'user_id': u'wchun',
        }
        headers = []
        data = {
            'vote': 10,
        }
        response = self._test_post_or_put(
            '/objects/{object_id}/users/{user_id}/'.format(**url_parts),
            headers,
            data,
        )
        data.update(url_parts)
        self._check_post(response, **data)

    def test_05_voted_list_resource_check_votes(self):
        response = self._test_get('/objects/')
        expected = [
            {
                u"amount": 19,
                u"average": u"9.5",
                u"object_id": u"978-0132678209",
                u"votes_no": 2,
            }
        ]
        self.assertEqual(json.loads(response.data), expected)

    def test_06_voted_list_resource_check_votes_single_object(self):
        url_parts = {
            u'object_id': u'978-0132678209',
        }
        response = self._test_get('/objects/{object_id}/'.format(**url_parts))
        expected = {
            u"amount": 19,
            u"average": u"9.5",
            u"object_id": url_parts['object_id'],
            u"votes_no": 2,
        }
        self.assertEqual(json.loads(response.data), expected)

    def test_07_voted_list_resource_check_vote_single_user(self):
        url_parts = {
            u'object_id': u'978-0132678209',
            u'user_id': u'gsalluzzo',
        }
        # FIXME: adding ?vote= to let the test passing, bug in Flask or Flask-RESTful?
        response = self._test_get(
            '/objects/{object_id}/users/{user_id}/'.format(**url_parts)
        )
        expected = {
            u"vote": 9,
            u"when": self.user_vote_dates[url_parts['user_id']]
        }
        expected.update(url_parts)
        self.assertEqual(json.loads(response.data), expected)

    def test_08_voted_list_resource_delete_second_user(self):
        url_parts = {
            u'object_id': u'978-0132678209',
            u'user_id': u'wchun',
        }
        # FIXME: adding ?vote= to let the test passing, bug in Flask or Flask-RESTful?
        response = self._test_delete(
            '/objects/{object_id}/users/{user_id}/'.format(**url_parts)
        )


if __name__ == '__main__':
    unittest.main()
