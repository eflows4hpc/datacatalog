import unittest

from apiserver.security import User
from collections import namedtuple
import os
import pathlib
import shutil


class UserTests(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_init(self):
        self.assertEquals(0,0)