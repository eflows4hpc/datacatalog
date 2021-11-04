#! /usr/bin/python3
import os, json, argparse, abc

from pydantic import BaseModel
from typing import List, Optional
from passlib.context import CryptContext



class User(BaseModel):
    username: str
    email: str = None
    has_secrets_access: Optional[bool] = False


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

    def __init__(self, filepath):
        self.file_path = filepath
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


__pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return __pwd_context.hash(password)

def main(args):
    userdb = JsonDBInterface(args.userdb_path)

    if 'hash' in args.operation:
        if not args.password:
            raise ValueError("Password is not set!")
        print(get_password_hash(args.password))
    elif 'ls' in args.operation:
        for user in userdb.list():
            print(user)
    elif 'add' in args.operation:
        if not args.username:
            raise ValueError("Username is not set!")
        if not args.mail:
            raise ValueError("Mail is not set!")
        hash = args.bcrypt_hash
        if not args.bcrypt_hash:
            if  not args.password:
                raise ValueError("No Password or hash given!")
            hash = get_password_hash(args.password)
        
        user = UserInDB(username=args.username, email=args.mail, hashed_password=hash, has_secrets_access=args.secret_access)
        userdb.add(user)
        print("new User added:")
        print(user)
    elif 'show' in args.operation:
        if not args.username:
            raise ValueError("Username is not set!")
        user = userdb.get(args.username)
        print(user)
    elif 'rm' in args.operation:
        if not args.username:
            raise ValueError("Username is not set!")
        user = userdb.get(args.username)
        print("Deleting the following user:")
        print(user)
        userdb.delete(args.username)
    elif 'give_secret' in args.operation:
        user = userdb.get(args.username)
        user.has_secrets_access = True
        userdb.delete(args.username)
        userdb.add(user)
    elif 'remove_secret' in args.operation:
        user = userdb.get(args.username)
        user.has_secrets_access = False
        userdb.delete(args.username)
        userdb.add(user)


if __name__ == "__main__":
    parser = argparse.ArgumentParser("userdb-cli.py", description="CLI for a userdb.json for the datacatalog-apiserver.", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("operation", type=str, nargs=1, help="\
hash \tReturn a bcrypt hash for the given password. Requires -p. \n\
ls \tLists all Users in the userdb. \n\
add \tAdds a new user to the userdb. Requires -u, -m and either -p or -b. -s is optional.\n\
show \tShows a single user from the userdb. Requires -u. \n\
give_secret \tGives the given user access to secrets. Requires -u. \n\
remove_secret \tRemove the given users access to secrets. Requires -u. \n\
rm \tDeletes a single user from the userdb. Requires -u. \
")
    parser.add_argument("-u", "--username", help="The username that should be modified")
    parser.add_argument("-m", "--mail", help="The email of a newly created user.")
    parser.add_argument("-p", "--password", help="The password of a newly created user.")
    parser.add_argument("-b", "--bcrypt-hash", help="The bcrypt password-hash of a newly created user.")
    parser.add_argument("-s", "--secret-access", action="store_true", help="Give the new user access to secrets.")
    parser.add_argument("userdb_path", type=str, nargs='?', help="The path to the userdb to be modified or created.", default="./userdb.json")
    args = parser.parse_args()
    main(args)