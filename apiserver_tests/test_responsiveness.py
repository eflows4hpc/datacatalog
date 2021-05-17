# These Tests only check if every api path that should work is responding to requests, the functionality is not yet checked
# Therefore this only detects grievous errors in the request handling.

from fastapi.testclient import TestClient

from context import apiserver
from context import storage

client = TestClient(apiserver.app)

# get root
def test_root():
    rsp = client.get('/')
    assert rsp.status_code >= 200 and rsp.status_code < 300 # any 200 response is fine, as a get to the root should not return any error

# get every type in type enum
def test_types():
    for location_type in storage.LocationDataType:
        rsp = client.get('/' + location_type.value)
        assert rsp.status_code >= 200 and rsp.status_code < 300 # any 200 response is fine, as a get to the datatypes should not return any error