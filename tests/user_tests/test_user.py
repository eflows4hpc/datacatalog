import unittest

from apiserver.security import User, JsonDBInterface, UserInDB
from apiserver.config import ApiserverSettings
from collections import namedtuple
import os
import pathlib
import shutil
import random


class UserTests(unittest.TestCase):
    def setUp(self):
        self.path = '/tmp/userstorage/'
        pathlib.Path(self.path).mkdir(parents=True, exist_ok=True)
        settings = ApiserverSettings(userdb_path=os.path.join(self.path, 'users.json'))
        self.a_user = UserInDB(username='test7', email='jo@go.com', hashed_password='42')
        self.b_user = UserInDB(username='8test', email='n@co.go', hashed_password='12121')

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
        
    def test_adding(self):
        
        self.userdb.add(user=self.a_user)

        lst = self.userdb.list()
        self.assertEquals(len(lst), 1, 'Should not be empty')

        g_user = self.userdb.get(username='test7')
        self.assertEqual(g_user.username, self.a_user.username)
        self.assertDictEqual(g_user.dict(), self.a_user.dict())

    def test_add_again(self):
        self.userdb.add(user=self.a_user)
        self.assertRaises(Exception, self.userdb.add, self.a_user)
        
    def test_delete(self):
        self.userdb.add(user=self.a_user)
        lst = self.userdb.list()
        self.assertEquals(len(lst), 1, 'Should not be empty')

        self.userdb.delete(username='test7')
        lst = self.userdb.list()
        self.assertEquals(len(lst), 0, 'Should be empty')

        self.userdb.add(user=self.a_user)
        self.userdb.add(user=self.b_user)
        self.assertEquals(len(self.userdb.list()), 2, 'Should not be empty')
        self.assertListEqual(self.userdb.list(), [self.a_user.username, self.b_user.username])
        
        self.userdb.delete(username='test7')
        self.assertListEqual(self.userdb.list(), [self.b_user.username])

        self.userdb.delete(username='test7')
        self.assertListEqual(self.userdb.list(), [self.b_user.username])
        
        self.userdb.delete(username=self.b_user.username)
        self.assertListEqual(self.userdb.list(), [])

    def test_massive_add(self):
        for n in range(0,25):
            self.userdb.add(UserInDB(username=f"user_{n}", email='jo@go.com', hashed_password=f"{random.randint(0,200)}"))
        self.assertEqual(len(self.userdb.list()), 25)



        

