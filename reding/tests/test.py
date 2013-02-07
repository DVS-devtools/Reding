from reding.app import app
import unittest
import json
import redis

"""
'accept_ranges'
'add_etag'
'age'
'allow'
'autocorrect_location_header'
'automatically_set_content_length'
'cache_control'
'call_on_close'
'charset'
'close'
'content_encoding'
'content_language'
'content_length'
'content_location'
'content_md5'
'content_range'
'content_type'
'data'
'date'
'default_mimetype'
'default_status'
'delete_cookie'
'direct_passthrough'
'expires'
'fix_headers'
'force_type'
'freeze'
'from_app'
'get_app_iter'
'get_etag'
'get_wsgi_headers'
'get_wsgi_response'
'header_list'
'headers'
'implicit_sequence_conversion'
'is_sequence'
'is_streamed'
'iter_encoded'
'last_modified'
'location'
'make_conditional'
'make_sequence'
'mimetype'
'mimetype_params'
'response'
'retry_after'
'set_cookie'
'set_etag'
'status'
'status_code'
'stream'
'vary'
'www_authenticate'
"""

class RedingTestCase(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.redis = redis.StrictRedis()
        self.redis.flushdb()

    def _test_get(self, url):
        r = self.app.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.mimetype, 'application/json')
        return r

    def _test_post(self, url, headers, data):
        r = self.app.post(url, headers=headers, data=data)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.mimetype, 'application/json')
        return r

    def test_voted_list_resource_empty(self):
        response =  self._test_get('/objects/')
        self.assertEqual(json.loads(response.data), [])

    def test_vote_summary_resource_first(self):
        url_parts = {
            'object_id': '978-0132678209',
            'user_id': 'gsalluzzo',
        }
        headers = []
        data = dict(vote=10)
        response =  self._test_post(
            '/objects/{object_id}/users/{user_id}/'.format(**url_parts),
            headers,
            data
        )
        resp = json.loads(response.data)
        self.assertEqual(resp['object_id'], url_parts['object_id'])
        self.assertEqual(resp['user_id'], url_parts['user_id'])
        self.assertEqual(resp['vote'], data['vote'])


if __name__ == '__main__':
    unittest.main()
