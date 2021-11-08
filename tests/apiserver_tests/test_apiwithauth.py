from fastapi.testclient import TestClient
from context import apiserver, storage
#from apiserver import app, my_user, my_auth

from unittest import TestCase
from apiserver.security.user import User

# a properly formatted uuidv4 to ensure the proper errors are returned by the api; the exact value is irrelevant
proper_uuid = "3a33262e-276e-4de8-87bc-f2d5a0195faf"

def myfunc():
    return User(username='foo', email='bar')

class UserTests(TestCase):

    def setUp(self):
        apiserver.app.dependency_overrides[apiserver.main.my_auth] = myfunc
        apiserver.app.dependency_overrides[apiserver.main.my_user] = myfunc
        
        self.client = TestClient(apiserver.app)
        
    def tearDown(self):
        apiserver.app.dependency_overrides={}

    
    def test_me(self):
       
       resp = self.client.get('/me')
       self.assertEqual(resp.json(), {'username': 'foo', 'has_secrets_access' : False, 'email': 'bar'})

    def test_token(self):
        rsp = self.client.post('/token').json()
        self.assertEqual(rsp["token_type"], "bearer")
        self.assertTrue('access_token' in rsp)

    def test_create(self):
        my_data = {
            'name': 'some datase1t', 
            'url': 'http://loc.me/1', 
            'metadata': {'key': 'value'}
        }
        rsp = self.client.post('/dataset', json=my_data)
        self.assertEqual(rsp.status_code, 200)
        (oid, dty) = rsp.json()
        
        self.assertIsNotNone(oid)
        self.assertEqual(dty, my_data)

        self.client.delete(f"/dataset/{oid}")


    def test_delete(self):
        rsp = self.client.delete(f"/dataset/{proper_uuid}")
        self.assertEqual(rsp.status_code, 404, 'deleted called on non-existing')

        rsp = self.client.post('/dataset', json={
            'name': 'some dataset2', 
            'url': 'http://loc.me/1'}
            )
        self.assertEqual(rsp.status_code, 200)
        (oid, dty) = rsp.json()
        
        rsp = self.client.delete(f"/dataset/{oid}")
        self.assertEqual(rsp.status_code, 200)

    def test_delete_invalid_uuid(self):
        rsp = self.client.delete("/dataset/invalid-uuid")
        self.assertEqual(rsp.status_code, 422, 'deleted called on invalid uuid')



    def test_create_and_get(self):
        dss = [{'name': f"ds_{i}", 'url': f"http://www.o.com/{i}"} for i in range(5)]
        for d in dss:
            rsp = self.client.post('/dataset', json=d)
            self.assertEqual(rsp.status_code, 200)
            (oid, dty) = rsp.json()
            d['id'] = oid

        for d in dss:
            i = d['id']
            rsp = self.client.get(f"/dataset/{i}")
            self.assertEqual(rsp.status_code, 200)
            dty = rsp.json()
            self.assertEqual(d['name'], dty['name'])
            self.assertEqual(d['url'], dty['url'])

            self.client.delete(f"/dataset/{i}")

    def test_create_and_delete(self):
        lst = self.client.get('/dataset').json()
        self.assertEqual(len(lst), 0, f"{lst}")

        self.client.post('/dataset', json={
            'name': 'new_obj',
            'url': 'some_url'
        })

        lst = self.client.get('/dataset').json()
        self.assertEqual(len(lst), 1, 'Should be 1 now')

        for r in lst:
            (name, oid) = r
            rsp = self.client.delete(f"/dataset/{oid}")
            self.assertEqual(rsp.status_code, 200)

        lst = self.client.get('/dataset').json()
        self.assertEqual(len(lst), 0, 'Should be empty now')

    def test_update(self):

        rsp = self.client.post('/dataset', 
        json={
                'name': 'new_obj',
                'url': 'some_url'
            }
            )
        (oid, name) = rsp.json()

        rsp = self.client.put(f"/dataset/{oid}", json={
            'name': 'new_name',
            'url': 'new_url',
            'metadata': {
                'key': 'value'
            }
        }
        )
        self.assertEqual(rsp.status_code, 200)

        rsp2 = self.client.get(f"/dataset/{oid}")
        self.assertEqual(rsp2.status_code, 200)
        dd = rsp2.json()
        self.assertEqual(dd['name'], 'new_name')
        self.assertEqual(dd['url'], 'new_url')
        self.assertEqual(dd['metadata'], {'key': 'value'})

        self.client.delete(f"/dataset/{oid}")

    def test_update_invalid_uuid(self):
        oid = "invalid_uuid"
        rsp = self.client.put(f"/dataset/{oid}", json={
            'name': 'new_name',
            'url': 'new_url',
            'metadata': {
                'key': 'value'
            }
        }
        )
        self.assertEqual(rsp.status_code, 422)
