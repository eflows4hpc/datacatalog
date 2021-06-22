import json
import os
import uuid
from typing import List

from pydantic import BaseModel

from apiserver.config import ApiserverSettings

from .LocationStorage import (AbstractLocationDataStorageAdapter, LocationData,
                              LocationDataType)


class StoredData(BaseModel):
    actualData: LocationData
    users: List[str]

def load_object(path):
    return StoredData.parse_file(path)

def get_unique_id(path: str) -> str:
    oid = str(uuid.uuid4())
    while os.path.exists(os.path.join(path, oid)):
        oid = str(uuid.uuid4())
    return oid


def verify_oid(oid: str, version=4):
    """ Ensure thatthe oid is formatted as a valid oid (i.e. UUID v4).
    If it isn't, the corresponding request could theoretically be an attempted path traversal attack (or a regular typo).
    """
    try:
        uuid_obj = uuid.UUID(oid, version=version)
    except:
        return False
    return str(uuid_obj) == oid

class JsonFileStorageAdapter(AbstractLocationDataStorageAdapter):
    """ This stores LocationData via the StoredData Object as json files

    These Jsonfiles then contain the actualData, as well as the users with permissions
    for this LocationData all users have full permission to to anything with
    this dataobject, uncluding removing their own access (this might trigger a
    confirmation via the frontend, but this is not enforced via the api)

    IMPORTANT: The adapter does not check for authentication or authorization,
    it should only be invoked if the permissions have been checked
    """

    def __init__(self, settings: ApiserverSettings):
        AbstractLocationDataStorageAdapter.__init__(self)
        self.data_dir = settings.json_storage_path
        if not (os.path.exists(self.data_dir) and os.path.isdir(self.data_dir)):
            raise Exception(f"Data Directory {self.data_dir} does not exist.")

    def __setup_path(self, value: str) -> str:
        localpath = os.path.join(self.data_dir, value)
        if not os.path.isdir(localpath):
            os.mkdir(localpath)
        return localpath

    def __get_object_path(self, value: str, oid: str) -> str:
        localpath = os.path.join(self.data_dir, value)
        full_path = os.path.join(localpath, oid)
        common = os.path.commonprefix((os.path.realpath(full_path),os.path.realpath(self.data_dir)))
        if common != os.path.realpath(self.data_dir):
            print(f"Escaping the data dir! {common} {full_path}")
            raise FileNotFoundError()
            
        if not os.path.isfile(full_path):
            raise FileNotFoundError(
                f"The requested object ({oid}) {full_path} does not exist.")
        return full_path

    def get_list(self, n_type: LocationDataType) -> List:
        local_path = self.__setup_path(n_type.value)
        ret = []
        for f in os.listdir(local_path):
            p = os.path.join(local_path, f)
            if not os.path.isfile(p):
                continue
            data = load_object(p)
            ret.append((data.actualData.name, f))
        return ret

    def add_new(self, n_type: LocationDataType, data: LocationData, user_name: str):
        localpath = self.__setup_path(value=n_type.value)
        oid = get_unique_id(path=localpath)
        to_store = StoredData(users=[user_name], actualData=data)
        with open(os.path.join(localpath, oid), 'w') as json_file:
            json.dump(to_store.dict(), json_file)
        return (oid, data)

    def get_details(self, n_type: LocationDataType, oid: str):
        full_path = self.__get_object_path(value=n_type.value, oid=oid)
        obj = load_object(path=full_path)
        return obj.actualData

    def update_details(self, n_type: LocationDataType, oid: str, data: LocationData, usr: str):
        # TODO: usr is ignored here?
        full_path = self.__get_object_path(value=n_type.value, oid=oid)
        obj = load_object(path=full_path)
        obj.actualData = data

        with open(full_path, 'w') as f:
            json.dump(obj.dict(), f)

        return (oid, data)

    def delete(self, n_type: LocationDataType, oid: str, usr: str):
        full_path = self.__get_object_path(value=n_type.value, oid=oid)
        os.remove(full_path)

    def get_owner(self, n_type: LocationDataType, oid: str):
        raise NotImplementedError()

    def check_perm(self, n_type: LocationDataType, oid: str, usr: str):
        raise NotImplementedError()

    def add_perm(self, n_type: LocationDataType, oid: str, usr: str):
        """add user to file perm"""
        raise NotImplementedError()

    def rm_perm(self, n_type: LocationDataType, oid: str, usr: str):
        """remove user from file perm"""
        raise NotImplementedError()
