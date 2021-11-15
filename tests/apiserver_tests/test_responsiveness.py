import unittest

from fastapi.testclient import TestClient

from context import apiserver, storage

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
            rsp.json(), [{'dataset': '/dataset'}, {'storage_target': '/storage_target'}, {'airflow_connections' : '/airflow_connections'}])

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
        self.assertFalse('foo' in j['message'], "error message should not contain object id (foo)")

    def test_get_invalid_oid(self):
        rsp = self.client.get('/dataset/invalid-uuid')
        self.assertEqual(422, rsp.status_code)
        j = rsp.json()
        self.assertTrue('detail' in j, f"{j} should contain message")

    def test_accept_headers(self):
        header_accept_json = {'Accept' : "application/json"}
        header_accept_html = {'Accept' : "text/html"}
        header_accept_none = {'Accept' : ""}

        rsp = self.client.get("/", headers=header_accept_json)
        self.assertEqual(rsp.json(), [{element.value: "/" + element.value} for element in storage.LocationDataType])

        rsp = self.client.get("/", headers=header_accept_html, allow_redirects=False)
        self.assertEqual(rsp.status_code, 307)

        rsp = self.client.get("/", headers=header_accept_html, allow_redirects=True)
        self.assertEqual(rsp.status_code, 422) # forwarded to /index.html which does not exist on the apiserver

        rsp = self.client.get("/", headers=header_accept_none)
        self.assertEqual(rsp.json(), [{element.value: "/" + element.value} for element in storage.LocationDataType])

    def test_secrets_access(self):
        # check if access for all secrets endpoints failed with 401 Auth required
        # list secrets, add secret, get secret, delete secret
        rsp = self.client.get(f'/dataset/{proper_uuid}/secrets')
        self.assertEqual(401, rsp.status_code)

        rsp = self.client.get(f'/dataset/{proper_uuid}/secrets/somespecificsecret')
        self.assertEqual(401, rsp.status_code)

        rsp = self.client.post(f'/dataset/{proper_uuid}/secrets', json={'key' : "somekey", "secret" : "somesecret"})
        self.assertEqual(401, rsp.status_code)

        rsp = self.client.delete(f'/dataset/{proper_uuid}/secrets/somespecificsecret')
        self.assertEqual(401, rsp.status_code)
