from reding.tests.utils import RedingTestCase


class GenericTestCase(RedingTestCase):

    def assert_404_on_get(self, url):
        r = self.app.get(url)
        self.assertEqual(r.status_code, 404, msg=r.data)
        self.assertEqual(r.mimetype, 'application/json')
        return r

    def test_404_on_vote(self):
        self.assert_404_on_get('/objects/error404/users/notfound/')
