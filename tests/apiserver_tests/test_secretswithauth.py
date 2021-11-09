from fastapi.testclient import TestClient
from context import apiserver, storage
#from apiserver import app, my_user, my_auth

from unittest import TestCase
from apiserver.security.user import User

# a properly formatted uuidv4 to ensure the proper errors are returned by the api; the exact value is irrelevant
proper_uuid = "3a33262e-276e-4de8-87bc-f2d5a0195faf"

def myfunc():
    return User(username='secret_foo', email='secret_bar', has_secrets_access=True)

class UserTests(TestCase):

    def setUp(self):
        apiserver.app.dependency_overrides[apiserver.main.my_auth] = myfunc
        apiserver.app.dependency_overrides[apiserver.main.my_user] = myfunc
        
        self.client = TestClient(apiserver.app)

        dummy_object = {
            'name': 'some datase1t', 
            'url': 'http://loc.me/1', 
            'metadata': {'key': 'value'}
        }

        rsp = self.client.post('/dataset', json=dummy_object)
        (self.dummy_oid, data) = rsp.json()
        
    def tearDown(self):
        self.client.delete(f'/dataset/{self.dummy_oid}')
        apiserver.app.dependency_overrides={}

    
    def test_me(self):
       
       resp = self.client.get('/me')
       self.assertEqual(resp.json(), {'username': 'secret_foo', 'has_secrets_access' : True, 'email': 'secret_bar'})


    def test_create_secret(self):
        secret_data = {
            'key' : 'secretkey',
            'secret' : 'secretvalue'
        }

        rsp = self.client.post(f'/dataset/{self.dummy_oid}/secrets', json=secret_data)
        self.assertEqual(rsp.status_code, 200)
        self.client.delete(f'/dataset/{self.dummy_oid}/secrets/secret_key')


    def test_delete_secret(self):
        secret_data = {
            'key' : 'secret_key',
            'secret' : 'secret_value'
        }
        # check deletion of non-existent secret
        rsp = self.client.delete(f'/dataset/{self.dummy_oid}/secrets/secret_key')
        self.assertEqual(rsp.status_code, 404)
        # create secret
        rsp = self.client.post(f'/dataset/{self.dummy_oid}/secrets', json=secret_data)
        # delete secret
        rsp = self.client.delete(f'/dataset/{self.dummy_oid}/secrets/secret_key')
        self.assertEqual(rsp.status_code, 200)
        # check that deletion worked
        rsp = self.client.get(f'/dataset/{self.dummy_oid}/secrets/secret_key')
        self.assertEqual(rsp.status_code, 404)



    def test_create_and_get_secret(self):
        # create multiple secrets, store in local array
        data = [{'key' : f'secret_key_{i}', 'secret' : f'secret_value_{i}'} for i in range(10)]
        for element in data:
            self.client.post(f'/dataset/{self.dummy_oid}/secrets', json=element)
        # get all secrets, verify 200 status and compare data with local array
        # then delete each secret
        for element in data:
            key = element['key']
            rsp = self.client.get(f'/dataset/{self.dummy_oid}/secrets/{key}')
            self.assertEqual(element['secret'], rsp.json())
            rsp = self.client.delete(f'/dataset/{self.dummy_oid}/secrets/{key}')

    def test_list_secrets(self):
        # create several secrets
        data = [{'key' : f'secret_key_{i}', 'secret' : f'secret_value_{i}'} for i in range(10)]
        keys = [element['key'] for element in data]
        for element in data:
            self.client.post(f'/dataset/{self.dummy_oid}/secrets', json=element)
        # then get list and compare
        rsp = self.client.get(f'/dataset/{self.dummy_oid}/secrets')
        self.assertEqual(rsp.status_code, 200)
        self.assertSetEqual(set(keys), set(rsp.json()))
        
        # then delete each secret
        for element in data:
            key = element['key']
            rsp = self.client.delete(f'/dataset/{self.dummy_oid}/secrets/{key}')

    # TODO test delete object, DO secrets disappear too? (currently they don't)