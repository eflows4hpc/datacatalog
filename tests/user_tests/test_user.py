import unittest

from apiserver.security import User, JsonDBInterface
from apiserver.config import ApiserverSettings
from collections import namedtuple
import os
import pathlib
import shutil


class UserTests(unittest.TestCase):
    def setUp(self):
        self.path = '/tmp/userstorage/'
        pathlib.Path(self.path).mkdir(parents=True, exist_ok=True)
        settings = ApiserverSettings(userdb_path=os.path.join(self.path, 'users.json'))

        self.userdb = JsonDBInterface(settings=settings)

    def tearDown(self):
        if os.path.exists(self.path):
            shutil.rmtree(self.path)

    def test_init(self):
        self.assertEquals(0,0)

    def test_list(self):
        lst = self.userdb.list()
        self.assertListEqual(lst, [], 'Should be empty')

    def test_empty_get(self):
        self.assertRaises(Exception, self.userdb.get, 'foo')
        