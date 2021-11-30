import os
import pathlib
import shutil
import unittest
from collections import namedtuple

from cryptography.fernet import Fernet
from fastapi.exceptions import HTTPException

from apiserver.storage import LocationData, LocationDataType
from apiserver.storage.EncryptedJsonFileStorageAdapter import \
    EncryptedJsonFileStorageAdapter


class EncruptedTests(unittest.TestCase):
    def setUp(self):
        Settings = namedtuple('Settings', ['json_storage_path', 'encryption_key'])
        self.test_config = Settings(json_storage_path='/tmp/json_test/', encryption_key=Fernet.generate_key())
        pathlib.Path(self.test_config.json_storage_path).mkdir(
            parents=True, exist_ok=True)

        self.store = EncryptedJsonFileStorageAdapter(self.test_config)
        d = LocationData(name='bla', url='local')
        (oid, _) = self.store.add_new(
            n_type=LocationDataType.DATASET, data=d, user_name='test_user')
        self.oid = oid

    def tearDown(self):
        if os.path.exists(self.test_config.json_storage_path):
            print('Path exists. Removing')
            shutil.rmtree(self.test_config.json_storage_path)

    def test_encrypt(self):
        enc = self.store.encrypt('bar')
        dec = self.store.decrypt(enc)
        self.assertEqual(dec, 'bar')

    def test_create_get(self):
        self.store.add_update_secret(n_type=LocationDataType.DATASET, oid=self.oid, key='foo',value='bar', usr='tester')
        secrets = self.store.get_secret_values(n_type=LocationDataType.DATASET, oid=self.oid, usr='tester')
        self.assertEqual(len(secrets), 1)
        self.assertDictEqual({'foo':'bar'}, secrets)

        var = self.store.get_secret(n_type=LocationDataType.DATASET, oid=self.oid, key='foo', usr='tester')
        self.assertEqual(var, 'bar')

        deleted_var = self.store.delete_secret(n_type=LocationDataType.DATASET, oid=self.oid, key='foo', usr='tester')
        self.assertEqual(deleted_var, 'bar')

    def test_get_nonexisting(self):
        self.assertRaises(HTTPException, self.store.get_secret, LocationDataType.DATASET, self.oid, 'nonexisting', 'tester')
