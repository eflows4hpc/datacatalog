from fastapi.testclient import TestClient

from context import apiserver, storage
import unittest


# a properly formatted uuidv4 to ensure the proper errors are returned by the api; the exact value is irrelevant
proper_uuid = "3a33262e-276e-4de8-87bc-f2d5a0195faf"

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
        self.assertEqual(rsp.status_code, 401, 'Auth required')

    def test_get_non_existing(self):
        rsp = self.client.get(f'/dataset/{proper_uuid}')
        self.assertEqual(404, rsp.status_code)
        j = rsp.json()
        self.assertTrue('message' in j, f"{j} should contain message")
        self.assertFalse('foo' in j['message'], f"error message should not contain object id (foo)")

    def test_get_invalid_oid(self):
        rsp = self.client.get('/dataset/invalid-uuid')
        self.assertEqual(400, rsp.status_code)
        j = rsp.json()
        self.assertTrue('detail' in j, f"{j} should contain message")

