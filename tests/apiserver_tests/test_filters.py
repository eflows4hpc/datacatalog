import unittest

from fastapi.testclient import TestClient

from context import apiserver, storage
from apiserver.security.user import User

# a properly formatted uuidv4 to ensure the proper errors are returned by the api; the exact value is irrelevant
proper_uuid = "3a33262e-276e-4de8-87bc-f2d5a0195faf"
def mynewfunc():
    return User(username='foo', email='bar')

def fill_with_elements(client, root=10):
    oids = []
    for i in range(root):
        for j in range(root):
            data = {
                'name' : f'Test Dataset {i} {j}', 
                'url' : f'placeholder{i}', 
                'metadata' : 
                {
                    'value for i' : f'{i}', 'value for j' : f'{j}'
                }
            }
            rsp = client.post('/dataset', json=data)
            oids.append(rsp.json()[0])
    return oids

def delete_entries(client, oids):
    for oid in oids:
        client.delete('/dataset/' + oid)

class FilterTests(unittest.TestCase):
    def setUp(self):
        apiserver.app.dependency_overrides[apiserver.main.my_auth] = mynewfunc
        apiserver.app.dependency_overrides[apiserver.main.my_user] = mynewfunc
        self.client = TestClient(apiserver.app)

    def tearDown(self):
        apiserver.app.dependency_overrides={}
        # clear all datasets in case of failure
        datasets = self.client.get('/dataset').json()
        for entry in datasets:
            self.client.delete('/dataset/' + entry[0])

    def test_root_count(self):
        rsp = self.client.get('/', params={'element_numbers' : True})
        self.assertEqual(rsp.status_code, 200, 'Should return 200')
        self.assertListEqual(rsp.json(), [{'dataset' : '0'}, {'storage_target' : '0'}, {'airflow_connections' : '0'}, {'template' : '0'}])

    def test_type_count(self):
        for location_type in storage.LocationDataType:
            rsp = self.client.get('/' + location_type.value, params={'element_numbers' : True})
            self.assertEqual(rsp.status_code, 200)
            self.assertEqual(rsp.json(), [[ location_type.value, '0']])

    def test_counting_with_elements_inserted(self):
        oids = fill_with_elements(self.client)
        
        rsp1 = self.client.get('/', params={'element_numbers' : True})
        rsp2 = self.client.get('/dataset', params={'element_numbers' : True})

        self.assertEqual(rsp1.status_code, 200, 'Should return 200')
        self.assertListEqual(rsp1.json(), [{'dataset' : '100'}, {'storage_target' : '0'}, {'airflow_connections' : '0'}, {'template' : '0'}])
        
        self.assertEqual(rsp2.status_code, 200, 'Should return 200')
        self.assertListEqual(rsp2.json(), [['dataset' , '100']])

        delete_entries(self.client, oids)

    def test_name_filter(self):
        oids = fill_with_elements(self.client, 4)
        
        rsp = self.client.get('/dataset', params={'element_numbers' : True, 'name' : '0'})
        self.assertEqual(rsp.json(), [['dataset', '7']])
        
        rsp = self.client.get('/dataset', params={'element_numbers' : True, 'name' : 'test'})
        self.assertEqual(rsp.json(), [['dataset', '16']])

        delete_entries(self.client, oids)

    
    def test_url_filter(self):
        oids = fill_with_elements(self.client, 4)
        
        rsp = self.client.get('/dataset', params={'element_numbers' : True, 'url' : '0'})
        self.assertEqual(rsp.json(), [['dataset', '4']])
        
        rsp = self.client.get('/dataset', params={'element_numbers' : True, 'url' : 'test'})
        self.assertEqual(rsp.json(), [['dataset', '0']])
        delete_entries(self.client, oids)

    def test_key_filter(self):
        oids = fill_with_elements(self.client, 4)
        
        rsp = self.client.get('/dataset', params={'element_numbers' : True, 'has_key' : 'value for i'})
        self.assertEqual(rsp.json(), [['dataset', '16']])
        
        rsp = self.client.get('/dataset', params={'element_numbers' : True, 'has_key' : 'test'})
        self.assertEqual(rsp.json(), [['dataset', '0']])
        delete_entries(self.client, oids)

    def test_search_filter(self):
        oids = fill_with_elements(self.client, 4)
        
        rsp = self.client.get('/dataset', params={'element_numbers' : True, 'search' : '0'})
        self.assertEqual(rsp.json(), [['dataset', '7']])
        
        rsp = self.client.get('/dataset', params={'element_numbers' : True, 'search' : 'test'})
        self.assertEqual(rsp.json(), [['dataset', '16']])
        
        rsp = self.client.get('/dataset', params={'element_numbers' : True, 'search' : 'place'})
        self.assertEqual(rsp.json(), [['dataset', '16']])
        
        rsp = self.client.get('/dataset', params={'element_numbers' : True, 'search' : 'value'})
        self.assertEqual(rsp.json(), [['dataset', '16']])

        delete_entries(self.client, oids)

    def test_paging_basic(self):
        oids = fill_with_elements(self.client, 15)

        rsp = self.client.get('/dataset', params={"page" : 1, "page_size" : 100})
        self.assertEqual(len(rsp.json()), 100)

        rsp = self.client.get('/dataset', params={"page" : 3, "page_size" : 100})
        self.assertEqual(len(rsp.json()), 25)

        rsp = self.client.get('/dataset', params={"page" : 7, "page_size" : 100})
        self.assertEqual(len(rsp.json()), 0)

        delete_entries(self.client, oids)