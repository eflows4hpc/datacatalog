from pydantic import BaseModel

from typing import Optional

import os
import json

from fastapi import Depends, HTTPException, status

from datetime import datetime, timedelta

from passlib.context import CryptContext

from jose import JWTError, jwt

from apiserver.config import ApiserverSettings

# to get a secure secret string run:
# openssl rand -hex 32
SECRET_KEY = "THIS IS NOT THE FINAL KEY; JUST FOR TESTING. IF FOUND IN PRODUCTION, ALERT THE SERVER ADMIN!"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRES_MINUTES = 60

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    username: str
    email: str = None

class UserInDB(User):
    hashed_password: str = None

class AbstractDBInterface:
    def list():
        raise NotImplementedError()

    def get(username: str):
        raise NotImplementedError()

    def add(user: UserInDB):
        raise NotImplementedError()

    def delete(username: str):
        raise NotImplementedError()

class JsonDBInterface(AbstractDBInterface):
    filePath: str = None
    # format ist a dict/ json containing "username" : UserInDB pairs
    def __init__(self, settings: ApiserverSettings):
        self.filePath = settings.userdb_path
        if not (os.path.exists(self.filePath) and os.path.isfile(self.filePath)):
            with open(self.filePath, 'w') as json_file:
                json.dump({}, json_file) # create empty json
        # if it exists, check if it is valid
        else:
            with open(self.filePath) as file:
                data = json.load(file) # if this raises no exception, the file must at least be proper json; the entries will not be manually checked
    
    def list(self):
        with open(self.filePath) as file:
            data = json.load(file)
            return data.keys()

    def get(self, username: str):
        with open(self.filePath) as file:
            data = json.load(file)
            return UserInDB(**data[username])

    def add(self, user: UserInDB):
        with open(self.filePath, 'r+') as file:
            data = json.load(file)
            file.seek(0)
            if not user.username in data.keys():
                data[user.username] = user.__dict__
            else:
                raise Exception("User " + user.username + " already exists!")
            json.dump(data, file)

    def delete(self, username: str): 
        with open(self.filePath, 'r+') as file:
            data = json.load(file)
            file.seek(0)
            if data[username] != None:
                del data[username]
            else:
                raise Exception("User " + username + " does not exists!")
            json.dump(data, file)


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def authenticate_user(userdb: AbstractDBInterface, username: str, password: str):
    user: UserInDB = get_user(userdb, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_user(db: AbstractDBInterface, username: str):
    return db.get(username)

def get_current_user(token: str, userdb: AbstractDBInterface):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(userdb, token_data.username)
    if user is None:
        raise credentials_exception
    return user
