# These Tests only check if every api path that should work is responding to requests, the functionality is not yet checked
# Therefore this only detects grievous errors in the request handling.

from fastapi.testclient import TestClient

from context import apiserver
from context import storage
import unittest


class SomeTests(unittest.TestCase):
    def setUp(self):
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


# PUT a new dataset, store the id in global variable

# GET the specific dataset

# DELETE the specific dataset
