# These Tests check if the PUT calls work as intended, checking both valid puts and invalid puts

from fastapi.testclient import TestClient

from context import apiserver
from context import storage

client = TestClient(apiserver.app)

# PUT a new dataset, store the id in global variable, verify via a GET if it worked

# PUT an invalid type (i.e. a type not in the enum)
