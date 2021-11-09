import unittest

from apiserver.storage.JsonFileStorageAdapter import JsonFileStorageAdapter, StoredData, verify_oid, get_unique_id
from apiserver.storage import LocationDataType, LocationData
from collections import namedtuple
import os
import pathlib
import shutil
import json
from fastapi.exceptions import HTTPException

class SomeTests(unittest.TestCase):
    def setUp(self):
        Settings = namedtuple('Settings', ['json_storage_path'])
        self.test_config = Settings('/tmp/json_test/')
        pathlib.Path(self.test_config.json_storage_path).mkdir(
            parents=True, exist_ok=True)

        self.store = JsonFileStorageAdapter(self.test_config)
        self.secret_type = LocationDataType.DATASET
        self.secret_oid = "secrets-testing-oid"

    def tearDown(self):
        if os.path.exists(self.test_config.json_storage_path):
            print('Path exists. Removing')
            shutil.rmtree(self.test_config.json_storage_path)

    def test_get_emptyList(self):
        test_type = LocationDataType.DATASET
        lst = self.store.get_list(n_type=test_type)
        self.assertEqual(lst, [],  'Id should not be none')

    def test_not_path(self):
        Settings = namedtuple('Settings', ['json_storage_path'])
        test_config = Settings('/tmp/json_test/blah/')
        self.assertRaises(Exception, JsonFileStorageAdapter, test_config)

    def test_add_new(self):
        d = LocationData(name='bla', url='local')
        (oid, data) = self.store.add_new(
            n_type=LocationDataType.DATASET, data=d, user_name='test_user')
        self.assertEqual(d, data, "Data should be equal")
        self.assertIsNotNone(oid)

    def test_add_and_read(self):
        l_data = LocationData(name='test1', url='http://n.go', metadata=[])
        (oid, data) = self.store.add_new(
            n_type=LocationDataType.DATASET, data=l_data, user_name='test_user')
        self.assertEqual(l_data, data, "Data should be equal")
        self.assertIsNotNone(oid)

        lst = self.store.get_list(n_type=LocationDataType.DATASET)
        self.assertEqual(len(lst), 1,  'One should be there')
        (n_name, n_o) = lst[0]
        self.assertEqual(n_name, l_data.name)
        self.assertEqual(n_o, oid)

    def test_get_details(self):
        # get_details(self, n_type: LocationDataType, oid: str):
        l_data = LocationData(name='test1', url='http://n.go', metadata=[])
        (oid, data) = self.store.add_new(
            n_type=LocationDataType.DATASET, data=l_data, user_name='test_user')
        self.assertEqual(l_data, data, "Data should be equal")
        self.assertIsNotNone(oid)

        details = self.store.get_details(
            n_type=LocationDataType.DATASET, oid=oid)
        self.assertEqual(l_data, details)

    def test_nonexisting_details(self):
        self.assertRaises(FileNotFoundError, self.store.get_details,
                          LocationDataType.DATASET, '42')

    def test_update_details(self):
        l_data = LocationData(name='test1', url='http://n.go', metadata=[])
        new_data = LocationData(
            name='test2', url='http://go.n', metadata={'key': 'value'})
        (oid, data) = self.store.add_new(
            n_type=LocationDataType.DATASET, data=l_data, user_name='test_user')
        self.assertEqual(l_data, data, "Data should be equal")
        self.assertIsNotNone(oid)

        (oid2, r) = self.store.update_details(n_type=LocationDataType.DATASET, oid=oid,
                                              data=new_data, usr='tst2')
        self.assertEqual(new_data, r)
        self.assertEqual(oid, oid2)


    def test_path_traversal(self):
        l_data = LocationData(name='test1', url='http://n.go', metadata=[])

        with open('/tmp/hackme', 'w+') as f:
            json.dump({'secret': 'data', 'users': [], 'actualData': {'name': 'some', 'url': 'oo'}}, f)

        (oid, data) = self.store.add_new(n_type=LocationDataType.DATASET, data=l_data, user_name='test_user')
        details = None
        try: 
            details = self.store.get_details(n_type=LocationDataType.DATASET, oid='../../../tmp/hackme')
        except:
            pass 
        
        print(details)
        self.assertIsNone(details)

    def test_oid_veirfication(self):
        oid = get_unique_id(path='/tmp/')
        self.assertTrue(verify_oid(oid=oid))
        self.assertTrue(verify_oid(oid=oid.replace('5', '7')))
        self.assertFalse(verify_oid(oid='random strawberry'))
        self.assertFalse(verify_oid(oid=None))
        self.assertFalse(verify_oid(oid=1))

    def test_secrets_list_empty(self):
        self.secret_oid = self.store.add_new(self.secret_type, LocationData(name="secrets_test", url="secrets_url"), "")[0]
        secrets = self.store.list_secrets(self.secret_type, self.secret_oid, "")
        self.assertEqual(len(secrets), 0)
        self.store.delete(self.secret_type, self.secret_oid, "")
    
    def test_secrets_add_get_delete(self):
        self.secret_oid = self.store.add_new(self.secret_type, LocationData(name="secrets_test", url="secrets_url"), "")[0]
        key = "secretkey"
        val = "secretvalue"
        val2 = "othersecretvalue"
        self.store.add_update_secret(self.secret_type, self.secret_oid, key, val, "")
        secrets = self.store.list_secrets(self.secret_type, self.secret_oid, "")
        self.assertEqual(len(secrets), 1)

        get_val = self.store.get_secret(self.secret_type, self.secret_oid, key, "")
        self.assertEqual(val, get_val)

        self.store.add_update_secret(self.secret_type, self.secret_oid, key, val2, "")
        get_val2 = self.store.get_secret(self.secret_type, self.secret_oid, key, "")
        self.assertEqual(val2, get_val2)
        
        
        self.store.delete_secret(self.secret_type, self.secret_oid, key, "")
        secrets = self.store.list_secrets(self.secret_type, self.secret_oid, "")
        self.assertEqual(len(secrets), 0)
        self.store.delete(self.secret_type, self.secret_oid, "")

    def test_secrets_add_list_multiple(self):
        self.secret_oid = self.store.add_new(self.secret_type, LocationData(name="secrets_test", url="secrets_url"), "")[0]
        size = 10
        secret_touples = [(f'key_{i}', f'secret_{i}') for i in range(size)]

        for secret in secret_touples:
            self.store.add_update_secret(self.secret_type, self.secret_oid, secret[0], secret[1], "")

        secrets = self.store.list_secrets(self.secret_type, self.secret_oid, "")
        self.assertEqual(len(secrets), size)

        for secret in secret_touples:
            val = self.store.delete_secret(self.secret_type, self.secret_oid, secret[0], "")
            self.assertEqual(val, secret[1])
        
        self.store.delete(self.secret_type, self.secret_oid, "")

    def test_secrets_delete_nonexistent(self):
        self.secret_oid = self.store.add_new(self.secret_type, LocationData(name="secrets_test", url="secrets_url"), "")[0]
        self.assertRaises(HTTPException, self.store.delete_secret, self.secret_type, self.secret_oid, "somekey", "")
        self.store.delete(self.secret_type, self.secret_oid, "")