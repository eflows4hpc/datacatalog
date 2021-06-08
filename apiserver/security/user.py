import logging
import abc
import json
import os
import warnings
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import HTTPException, status
from passlib.context import CryptContext
from pydantic import BaseModel

from apiserver.config import ApiserverSettings

with warnings.catch_warnings():
    warnings.filterwarnings('ignore', message='int_from_bytes is deprecated')
    from jose import JWTError, jwt


# to get a secure secret string run:
# openssl rand -hex 32
SECRET_KEY = "THIS IS NOT THE FINAL KEY; JUST FOR TESTING. IF FOUND IN PRODUCTION, ALERT THE SERVER ADMIN!"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRES_MINUTES = 60


class Token(BaseModel):
    access_token: str
    token_type: str


class User(BaseModel):
    username: str
    email: str = None


class UserInDB(User):
    hashed_password: str = None


class AbstractDBInterface(metaclass=abc.ABCMeta):
    @abc.abstractclassmethod
    def list(self) -> List:
        raise NotImplementedError()

    @abc.abstractclassmethod
    def get(self, username: str):
        raise NotImplementedError()

    @abc.abstractclassmethod
    def add(self, user: UserInDB):
        raise NotImplementedError()

    @abc.abstractclassmethod
    def delete(self, username: str):
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
        return list(data.keys())

    def get(self, username: str):
        data = self.__read_all()
        if username not in data:
            return None

        return UserInDB(**data[username])

    def add(self, user: UserInDB):
        data = self.__read_all()
        if user.username in data:
            raise Exception(f"User {user.username} already exists!")

        data[user.username] = user.dict()
        self.__save_all(data=data)

    def delete(self, username: str):
        data = self.__read_all()
        # idempotent? or return?
        _ = data.pop(username, None)

        self.__save_all(data)


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
