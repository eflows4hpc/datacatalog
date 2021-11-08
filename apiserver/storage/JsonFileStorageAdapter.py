import json
import os
import uuid
from typing import Dict, List, Optional
import logging

from pydantic import BaseModel

from apiserver.config import ApiserverSettings

from .LocationStorage import (AbstractLocationDataStorageAdapter, LocationData,
                              LocationDataType)


log = logging.getLogger(__name__)

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
    If it isn't, the corresponding request could theoretically be
    an attempted path traversal attack (or a regular typo).
    """
    try:
        uuid_obj = uuid.UUID(oid, version=version)
        return str(uuid_obj) == oid
    except:
        return False

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
        log.info("Initializing JsonFileStorageAdapter.")
        if not (os.path.exists(self.data_dir) and os.path.isdir(self.data_dir)):
            raise Exception(f"Data Directory {self.data_dir} does not exist.")

    def __setup_path(self, value: str) -> str:
        localpath = os.path.join(self.data_dir, value)
        if not os.path.isdir(localpath):
            os.mkdir(localpath)
        return localpath

    def __get_object_path(self, value: str, oid: str) -> str:
        localpath = os.path.join(self.data_dir, value)
        full_path = os.path.join(localpath, str(oid))
        common = os.path.commonprefix((os.path.realpath(full_path),os.path.realpath(self.data_dir)))
        if common != os.path.realpath(self.data_dir):
            log.error(f"Escaping the data dir! {common} {full_path}")
            raise FileNotFoundError()

        if not os.path.isfile(full_path):
            log.error("Requsted object (%s) %s does not exist.", oid, full_path)
            raise FileNotFoundError(
                f"The requested object ({oid}) {full_path} does not exist.")
        return full_path

    def __get_secrets_path(self, value: str, oid: str) -> str:
        return self.__get_object_path(value, oid) + ".secrets"

    def __load_secrets(self, path: str) -> Dict[str, str]:
        if not os.path.isfile(path):
            return {}
        with open(path, "r") as file:
            dict = json.load(file)
        return dict

    def __store_secrets(self, path: str, secrets: Dict[str, str]):
        with open(path, "w") as file:
            json.dump(secrets, file)

    def get_list(self, n_type: LocationDataType) -> List:
        local_path = self.__setup_path(n_type.value)
        ret = []
        for f in os.listdir(local_path):
            p = os.path.join(local_path, f)
            if not os.path.isfile(p):
                continue
            if p.endswith('secrets'):
                continue
            data = load_object(p)
            ret.append((data.actualData.name, f))
        log.debug("Listing all objects ob type %s.", n_type.value)
        return ret

    def add_new(self, n_type: LocationDataType, data: LocationData, user_name: str):
        localpath = self.__setup_path(value=n_type.value)
        oid = get_unique_id(path=localpath)
        to_store = StoredData(users=[user_name], actualData=data)
        with open(os.path.join(localpath, oid), 'w') as json_file:
            json.dump(to_store.dict(), json_file)
        log.debug("Added new object with oid %s by user '%s'.", oid, user_name)
        return (oid, data)

    def get_details(self, n_type: LocationDataType, oid: str):
        full_path = self.__get_object_path(value=n_type.value, oid=oid)
        obj = load_object(path=full_path)
        log.debug("Returned object %s.", oid)
        return obj.actualData

    def update_details(self, n_type: LocationDataType, oid: str, data: LocationData, usr: str):
        full_path = self.__get_object_path(value=n_type.value, oid=oid)
        obj = load_object(path=full_path)
        obj.actualData = data

        with open(full_path, 'w') as f:
            json.dump(obj.dict(), f)

        log.debug("Updated  object with oid %s by user '%s'.", oid, usr)
        return (oid, data)

    def delete(self, n_type: LocationDataType, oid: str, usr: str):
        full_path = self.__get_object_path(value=n_type.value, oid=oid)
        log.debug("Deleted object %s by user '%s'.", oid, usr)
        os.remove(full_path)
        
    def list_secrets(self, n_type: LocationDataType, oid:str, usr: str):
        """ list all available secrets for this object"""
        secrets_path = self.__get_secrets_path(value=n_type.value, oid=oid)
        secrets = self.__load_secrets(secrets_path)
        return list(secrets.keys())

    def add_update_secret(self, n_type: LocationDataType, oid:str, key: str, value: str, usr: str):
        """ add new secrets to an existing object"""
        secrets_path = self.__get_secrets_path(value=n_type.value, oid=oid)
        secrets = self.__load_secrets(secrets_path)
        secrets[key] = value
        # TODO log
        self.__store_secrets(secrets_path, secrets)

    def get_secret(self, n_type: LocationDataType, oid:str, key: str, usr: str):
        """ return the value of the requested secret for the given object"""
        secrets_path = self.__get_secrets_path(value=n_type.value, oid=oid)
        secrets = self.__load_secrets(secrets_path)
        # TODO log
        return secrets[key]

    def delete_secret(self, n_type: LocationDataType, oid:str, key: str, usr: str):
        """ delete and return the value of the requested secret for the given object"""
        secrets_path = self.__get_secrets_path(value=n_type.value, oid=oid)
        secrets = self.__load_secrets(secrets_path)
        val = secrets.pop(key, None)
        # TODO log
        self.__store_secrets(secrets_path, secrets)
        return val 
