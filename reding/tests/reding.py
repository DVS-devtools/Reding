from reding.app import app
import unittest


class MyTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def test_json_post(self):
        headers = [('Content-Type', 'application/json')]
        data = 'vote=4'
        headers.append(('Content-Length', len(data)))
        response = self.app.post('/objects/o1/users/u1/', headers=headers, data=data)
        self.assertTrue(True)
