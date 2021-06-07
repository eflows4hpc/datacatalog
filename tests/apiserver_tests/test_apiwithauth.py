from fastapi.testclient import TestClient
from apiserver.main import app, my_user, my_auth
from unittest import TestCase
from apiserver.security.user import User

def myfunc():
    return User(username='foo', email='bar')

class UserTests(TestCase):

    def setUp(self):
        self.client = TestClient(app)
        app.dependency_overrides={}

    def tearDown(self):
        app.dependency_overrides={}
    
    def test_me(self):
       app.dependency_overrides[my_user] = myfunc
       
       resp = self.client.get('/me')
       self.assertEquals(resp.json(), {'username': 'foo', 'email': 'bar'})

    def test_token(self):
        app.dependency_overrides[my_auth] = myfunc
        rsp = self.client.post('/token').json()
        self.assertEqual(rsp["token_type"], "bearer")
        self.assertTrue('access_token' in rsp)

    def test_create(self):
        app.dependency_overrides[my_user] = myfunc
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

        self.client.delete(f'/dataset/{oid}')
