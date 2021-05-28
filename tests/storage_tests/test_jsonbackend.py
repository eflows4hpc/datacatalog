import unittest

from apiserver.storage.JsonFileStorageAdapter import JsonFileStorageAdapter
from apiserver.storage import LocationDataType
from collections import namedtuple 
import os
import pathlib
import shutil


class SomeTests(unittest.TestCase):
    def setUp(self):

        Settings =  namedtuple('Settings',['json_storage_path'])
        self.test_config = Settings('/tmp/json_test/')
        pathlib.Path(self.test_config.json_storage_path).mkdir(parents=True, exist_ok=True)

        self.store = JsonFileStorageAdapter(self.test_config)
    
    def tearDown(self):
        if os.path.exists(self.test_config.json_storage_path):
            print('Paht exists. Removing')
            shutil.rmtree(self.test_config.json_storage_path)

    def test_getList(self):
        test_type = LocationDataType.DATASET
        lst = self.store.getList(type=test_type)
        self.assertEqual(lst, [],  'Id should not be none')
        