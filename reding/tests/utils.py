from reding.app import app
import unittest
import json
from datetime import datetime
from dateutil import parser as dtparser
from urllib import urlencode
from urlparse import parse_qs, urlsplit, urlunsplit


def set_query_parameter(url, param_name, param_value):
    """Given a URL, set or replace a query parameter and return the
    modified URL. Stackoverflow: http://stackoverflow.com/a/12897375

    >>> set_query_parameter('http://example.com?foo=bar&biz=baz', 'foo', 'stuff')
    'http://example.com?foo=stuff&biz=baz'

    """
    scheme, netloc, path, query_string, fragment = urlsplit(url)
    query_params = parse_qs(query_string)

    query_params[param_name] = [param_value]
    new_query_string = urlencode(query_params, doseq=True)

    return urlunsplit((scheme, netloc, path, new_query_string, fragment))


class RedingTestCase(unittest.TestCase):

    user_vote_dates = {}
    querystring_params = []
    url = ''
    app = app.test_client()

    def set_url_with_querystring_params(self, url):
        self.url = url
        for k, v in self.querystring_params:
            self.url = set_query_parameter(self.url, k, v)

    def assert_get(self, url):
        self.set_url_with_querystring_params(url)
        r = self.app.get(self.url)
        self.assertEqual(r.status_code, 200, msg=r.data)
        self.assertEqual(r.mimetype, 'application/json')
        return r

    def assert_delete(self, url):
        self.set_url_with_querystring_params(url)
        r = self.app.delete(self.url)
        self.assertEqual(r.status_code, 204, msg=r.data)
        self.assertEqual(r.mimetype, 'application/json')
        self.assertFalse(r.data)
        return r

    def assert_post_or_put(self, url, headers, data, put=False):
        self.set_url_with_querystring_params(url)
        if not put:
            r = self.app.post(self.url, headers=headers, data=data)
        else:
            r = self.app.put(self.url, headers=headers, data=data)
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
