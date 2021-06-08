from fastapi.testclient import TestClient

from context import apiserver, storage
import unittest


class NonAuthTests(unittest.TestCase):
    def setUp(self):
        #TODO: we should do better here (cleanup or use some testing dir)
        self.client = TestClient(apiserver.app)

    def test_root(self):
        rsp = self.client.get('/')
        self.assertEqual(rsp.status_code, 200, 'Should return 200')
        self.assertEqual(
            rsp.json(), [{'dataset': '/dataset'}, {'storage_target': '/storage_target'}])

    def test_types(self):
        for location_type in storage.LocationDataType:
            rsp = self.client.get('/' + location_type.value)
            self.assertEqual(rsp.status_code, 200)

    def test_get_datasets(self):
        rsp = self.client.get('/dataset/')
        self.assertEqual(rsp.status_code, 200)
        self.assertEqual(rsp.json(), [])

    def test_create_ds(self):
        rsp = self.client.put('/dataset/3', json={"id": "foobar"})
        self.assertEqual(rsp.status_code, 401)

    def test_me(self):
        rsp = self.client.get('/me')
        self.assertEqual(rsp.status_code, 401, 'Auth required')

    def test_token(self):
        rsp = self.client.post('/token', data={'username': 'foo', 'password': 'bar'})
        self.assertEqual(rsp.status_code, 401, 'Ath')

    def test_get_non_existing(self):
        rsp = self.client.get('/dataset/foo')
        self.assertEqual(404, rsp.status_code)
        j = rsp.json()
        self.assertTrue('message' in j, f"{j} should contain message")
        self.assertTrue('foo' in j['message'], f"{j} should contain object id (foo)")

