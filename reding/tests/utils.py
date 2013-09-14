from reding.app import app
import unittest
import json
from datetime import datetime
from dateutil import parser as dtparser


class RedingTestCase(unittest.TestCase):

    user_vote_dates = {}

    def __init__(self, methodName='runTest'):
        super(RedingTestCase, self).__init__(methodName)
        self.app = app.test_client()

    def assert_get(self, url):
        r = self.app.get(url)
        self.assertEqual(r.status_code, 200, msg=r.data)
        self.assertEqual(r.mimetype, 'application/json')
        return r

    def assert_delete(self, url):
        r = self.app.delete(url)
        self.assertEqual(r.status_code, 204, msg=r.data)
        self.assertEqual(r.mimetype, 'application/json')
        self.assertFalse(r.data)
        return r

    def assert_post_or_put(self, url, headers, data, put=False):
        if not put:
            r = self.app.post(url, headers=headers, data=data)
        else:
            r = self.app.put(url, headers=headers, data=data)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.mimetype, 'application/json')
        return r

    def _check_post(self, response, object_id, user_id, vote, review=None):
        resp = json.loads(response.data)
        self.assertEqual(resp['object_id'], object_id)
        self.assertEqual(resp['user_id'], user_id)
        self.assertEqual(resp['vote'], vote)
        self.assertEqual(resp['review'], review)
        self.user_vote_dates.setdefault(user_id, {})
        self.user_vote_dates[user_id][object_id] = resp['when']
        dt = dtparser.parse(resp['when'])
        self.assertEqual(type(dt), datetime)
