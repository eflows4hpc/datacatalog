import unittest

from apiserver.security import User, JsonDBInterface, UserInDB, authenticate_user, get_current_user
from apiserver.config import ApiserverSettings
from fastapi import HTTPException
from collections import namedtuple
import os
import pathlib
import shutil
import random
from unittest.mock import Mock, patch


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
        self.assertEqual(0,0)

    def test_list(self):
        lst = self.userdb.list()
        self.assertListEqual(lst, [], 'Should be empty')

    def test_empty_get(self):
        #self.assertRaises(Exception, self.userdb.get, 'foo')
        self.assertIsNone(self.userdb.get('foo'))
        
    def test_adding(self):
        
        self.userdb.add(user=self.a_user)

        lst = self.userdb.list()
        self.assertEqual(len(lst), 1, 'Should not be empty')

        g_user = self.userdb.get(username='test7')
        self.assertEqual(g_user.username, self.a_user.username)
        self.assertDictEqual(g_user.dict(), self.a_user.dict())

    def test_add_again(self):
        self.userdb.add(user=self.a_user)
        self.assertRaises(Exception, self.userdb.add, self.a_user)
        
    def test_delete(self):
        self.userdb.add(user=self.a_user)
        lst = self.userdb.list()
        self.assertEqual(len(lst), 1, 'Should not be empty')

        self.userdb.delete(username='test7')
        lst = self.userdb.list()
        self.assertEqual(len(lst), 0, 'Should be empty')

        self.userdb.add(user=self.a_user)
        self.userdb.add(user=self.b_user)
        self.assertEqual(len(self.userdb.list()), 2, 'Should not be empty')
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

    def test_not_authenticate_user(self):
        mock = Mock(spec=JsonDBInterface)
        mock.get.return_value = None
        user = authenticate_user(userdb=mock, username='foo', password='pass')
        self.assertIsNone(user)
        mock.get.assert_called_with('foo')

    def test_authenticate_user(self):
        mock = Mock(spec=JsonDBInterface)
        mock.get.return_value(UserInDB(username='foo', email='bar@o.w', hashed_password='passed'))
        with patch('apiserver.security.user.verify_password') as vp:
            user = authenticate_user(userdb=mock, username='foo', password='passed')
            self.assertIsNotNone(user)
            vp.assert_called_once()
            mock.get.assert_called_once()
            mock.get.assert_called_with('foo')

    def test_current_user(self):
        self.assertRaises(HTTPException, get_current_user, 'falsetoken', Mock(spec=JsonDBInterface))