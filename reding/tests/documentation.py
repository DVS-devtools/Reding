# coding=utf-8
import os
import json
import redis
from reding import managers
from reding.tests.utils import RedingTestCase
managers.rclient = redis.StrictRedis(
    host=os.getenv('REDING_TEST_REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDING_TEST_REDIS_PORT', 6379)),
    db=int(os.getenv('REDING_TEST_REDIS_DB', 15)),
)


class RedingDocumentationTestCase(RedingTestCase):
    def test_00_voted_list_resource_empty(self):
        managers.rclient.flushdb()
        response = self.assert_get('/objects/')
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
        response = self.assert_post_or_put(
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
        response = self.assert_post_or_put(
            '/objects/{object_id}/users/{user_id}/'.format(**url_parts),
            headers,
            data,
            put=True,
        )
        data.update(url_parts)
        self._check_post(response, **data)

    def test_03_voted_list_resource_check_first_vote(self):
        response = self.assert_get('/objects/')
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
        response = self.assert_post_or_put(
            '/objects/{object_id}/users/{user_id}/'.format(**url_parts),
            headers,
            data,
        )
        data.update(url_parts)
        self._check_post(response, **data)

    def test_05_voted_list_resource_check_votes(self):
        response = self.assert_get('/objects/')
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
        response = self.assert_get('/objects/{object_id}/'.format(**url_parts))
        expected = {
            u"amount": 19,
            u"average": u"9.5",
            u"object_id": url_parts[u'object_id'],
            u"votes_no": 2,
        }
        self.assertEqual(json.loads(response.data), expected)

    def test_07_voted_list_resource_check_vote_single_user(self):
        url_parts = {
            u'object_id': u'978-0132678209',
            u'user_id': u'gsalluzzo',
        }
        response = self.assert_get(
            '/objects/{object_id}/users/{user_id}/'.format(**url_parts)
        )
        expected = {
            u"vote": 9,
            u'review': None,
            u"when": self.user_vote_dates[url_parts[u'user_id']][url_parts[u'object_id']]
        }
        expected.update(url_parts)
        self.assertEqual(json.loads(response.data), expected)

    def test_08_voted_list_resource_delete_second_user(self):
        url_parts = {
            u'object_id': u'978-0132678209',
            u'user_id': u'wchun',
        }
        self.assert_delete(
            '/objects/{object_id}/users/{user_id}/'.format(**url_parts)
        )

    def test_09_vote_summary_resource_third_vote(self):
        url_parts = {
            u'object_id': u'978-0132678209',
            u'user_id': u'mymom',
        }
        headers = []
        data = {
            u'vote': 3,
        }
        response = self.assert_post_or_put(
            '/objects/{object_id}/users/{user_id}/'.format(**url_parts),
            headers,
            data,
        )
        data.update(url_parts)
        self._check_post(response, **data)

    def test_10_voted_list_resource_check_votes(self):
        url_parts = {
            u'object_id': u'978-0132678209',
        }
        response = self.assert_get('/objects/{object_id}/'.format(**url_parts))
        expected = {
            u"amount": 12,
            u"average": u"6.0",
            u"object_id": url_parts[u'object_id'],
            u"votes_no": 2,
        }
        self.assertEqual(json.loads(response.data), expected)

    def test_10_voted_list_resource_check_votes_with_hit_filter(self):
        url_parts = {
            u'object_id': u'978-0132678209',
        }
        response = self.assert_get('/objects/{object_id}/?vote=3'.format(**url_parts))
        expected = {
            u"amount": 3,
            u"average": u"3.0",
            u"object_id": url_parts[u'object_id'],
            u"votes_no": 1,
        }
        self.assertEqual(json.loads(response.data), expected)

    def test_10_voted_list_resource_check_votes_with_miss_filter(self):
        url_parts = {
            u'object_id': u'978-0132678209',
        }
        response = self.assert_get('/objects/{object_id}/?vote=1'.format(**url_parts))
        expected = {
            u"amount": 0,
            u"average": u"0.0",
            u"object_id": url_parts[u'object_id'],
            u"votes_no": 0,
        }
        self.assertEqual(json.loads(response.data), expected)

    def test_11_vote_summary_resource_forth_vote(self):
        url_parts = {
            u'object_id': u'978-0618640140',
            u'user_id': u'gsalluzzo',
        }
        headers = []
        data = {
            u'vote': 10,
            u'review': u'the ☃ loves lotr',
        }
        response = self.assert_post_or_put(
            '/objects/{object_id}/users/{user_id}/'.format(**url_parts),
            headers,
            data,
        )
        data.update(url_parts)
        self._check_post(response, **data)

    def test_12_voted_list_resource_check_vote_single_user(self):
        url_parts = {
            u'user_id': u'gsalluzzo',
        }
        response = self.assert_get(
            '/users/{user_id}/'.format(**url_parts)
        )
        reply_objects = (u'978-0132678209', u'978-0618640140')
        expected = [
            {
                u"vote": 9,
                u'review': None,
                u"when": self.user_vote_dates[url_parts[u'user_id']][reply_objects[0]],
                u"user_id": url_parts[u'user_id'],
                u"object_id": reply_objects[0],
            },
            {
                u"vote": 10,
                u'review': u'the ☃ loves lotr',
                u"when": self.user_vote_dates[url_parts[u'user_id']][reply_objects[1]],
                u"user_id": url_parts[u'user_id'],
                u"object_id": reply_objects[1],
            }
        ]
        self.assertEqual(json.loads(response.data), expected)

    def test_13_voted_list_resource_check_three_votes(self):
        response = self.assert_get('/objects/')
        expected = [
            {
                u"amount": 10,
                u"average": u"10.0",
                u"object_id": u"978-0618640140",
                u"votes_no": 1,
            },
            {
                u"amount": 12,
                u"average": u"6.0",
                u"object_id": u"978-0132678209",
                u"votes_no": 2,
            }
        ]
        self.assertEqual(json.loads(response.data), expected)

    def test_14_user_list_resource(self):
        user_id = u'gsalluzzo'
        object_id = u'978-0618640140'
        response = self.assert_get('/objects/{object_id}/users/'.format(object_id=object_id))
        expected = [
            {
                u'vote': 10,
                u'review': u'the ☃ loves lotr',
                u'user_id': user_id,
                u'when': self.user_vote_dates[user_id][object_id],
                u'object_id': object_id,
            }
        ]
        self.assertEqual(json.loads(response.data), expected)

        response = self.assert_get('/objects/{object_id}/users/?vote=10'.format(object_id=object_id))
        self.assertEqual(json.loads(response.data), expected)

        response = self.assert_get('/objects/{object_id}/users/?vote=1'.format(object_id=object_id))
        expected = []
        self.assertEqual(json.loads(response.data), expected)
