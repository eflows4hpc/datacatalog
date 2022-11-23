import logging
import abc
import json
import os
import warnings
import random
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import HTTPException, status
from passlib.context import CryptContext
from pydantic import BaseModel

from apiserver.config import ApiserverSettings

with warnings.catch_warnings():
    warnings.filterwarnings('ignore', message='int_from_bytes is deprecated')
    from jose import JWTError, jwt


# secret key is generated once on server startup, a server-restart therefore also invalidates all pre-existing tokens
SECRET_KEY = hex(random.SystemRandom().getrandbits(256))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRES_MINUTES = 1440 # 24 hours

log = logging.getLogger(__name__)


class Token(BaseModel):
    access_token: str
    token_type: str


class User(BaseModel):
    username: str
    email: str = None
    has_secrets_access: bool = False


class UserInDB(User):
    hashed_password: str = None

class Secret(BaseModel):
    key: str = None
    secret: str = None


class AbstractDBInterface(metaclass=abc.ABCMeta): # pragma: no cover
    @abc.abstractclassmethod
    def list(cls) -> List:
        raise NotImplementedError()

    @abc.abstractclassmethod
    def get(cls, username: str):
        raise NotImplementedError()

    @abc.abstractclassmethod
    def add(cls, user: UserInDB):
        raise NotImplementedError()

    @abc.abstractclassmethod
    def delete(cls, username: str):
        raise NotImplementedError()

    @abc.abstractclassmethod
    def add_external_auth_user(cls, username: str, email: str):
        raise NotImplementedError()


class JsonDBInterface(AbstractDBInterface):

    def __init__(self, settings: ApiserverSettings):
        logging.info("Recreating userdb %s", settings)
        self.file_path = settings.userdb_path
        if not (os.path.exists(self.file_path) and os.path.isfile(self.file_path)):
            # create empty json
            self.__save_all({})
        else:
            # if it exists, check if it is valid
            _ = self.__read_all()

    def __read_all(self):
        with open(self.file_path, 'r') as f:
            return json.load(f)

    def __save_all(self, data):
        with open(self.file_path, 'w') as f:
            json.dump(data, f)

    def list(self):
        data = self.__read_all()
        log.debug("Listing all users in userdb.")
        return list(data.keys())

    def get(self, username: str):
        data = self.__read_all()
        if username not in data:
            return None
        log.debug("Reading user %s from userdb.", username)
        return UserInDB(**data[username])

    def add(self, user: UserInDB):
        data = self.__read_all()
        if user.username in data:
            raise Exception(f"User {user.username} already exists!")

        data[user.username] = user.dict()
        self.__save_all(data=data)
        log.debug("Added user %s to userdb.", user.username)

    def delete(self, username: str):
        data = self.__read_all()
        # idempotent? or return?
        _ = data.pop(username, None)

        self.__save_all(data)
        log.debug("Deleted user %s from userdb.", username)

    def add_external_auth_user(cls, username: str, email: str):
        cls.add(UserInDB(username=username, email=email))


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def authenticate_user(userdb: AbstractDBInterface, username: str, password: str):
    user: UserInDB = userdb.get(username)
    if user and verify_password(password, user.hashed_password):
        return user
    return None


def create_access_token(data: dict, expires_delta: Optional[timedelta] = timedelta(minutes=15)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(token: str, userdb: AbstractDBInterface):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if (username is None) or ((user := userdb.get(username)) is None):
            raise credentials_exception

        return user
    except JWTError:
        raise credentials_exception from JWTError
