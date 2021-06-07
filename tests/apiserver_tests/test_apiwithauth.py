from fastapi.testclient import TestClient
from context import apiserver, storage
#from apiserver import app, my_user, my_auth

from unittest import TestCase
from apiserver.security.user import User

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
       self.assertEqual(resp.json(), {'username': 'foo', 'email': 'bar'})

    def test_token(self):
        rsp = self.client.post('/token').json()
        self.assertEqual(rsp["token_type"], "bearer")
        self.assertTrue('access_token' in rsp)

    def test_create(self):
        my_data = {
            'name': 'some dataset', 
            'url': 'http://loc.me/1', 
            'metadata': {'key': 'value'}
        }
        rsp = self.client.post('/dataset', json=my_data)
        print(rsp.content)
        self.assertEqual(rsp.status_code, 200)
        print(rsp.content)
        (oid, dty) = rsp.json()
        
        self.assertIsNotNone(oid)
        self.assertEqual(dty, my_data)

        self.client.delete(f"/dataset/{oid}")


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
