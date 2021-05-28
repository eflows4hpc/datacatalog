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
        assert rsp.status_code >= 200 and rsp.status_code < 300 # any 200 response is fine, as a get to the root should not return any error

    def test_types(self):
        for location_type in storage.LocationDataType:
            rsp = self.client.get('/' + location_type.value)
            assert rsp.status_code >= 200 and rsp.status_code < 300 # any 200 response is fine, as a get to the datatypes should not return any error

# PUT a new dataset, store the id in global variable

# GET the specific dataset

# DELETE the specific dataset
