import json
import os
import uuid
from typing import List

from apiserver.config import ApiserverSettings

from .LocationStorage import (AbstractLocationDataStorageAdapter, LocationData,
                              LocationDataType)


class StoredData:
    actualData: LocationData
    users: List[str]

    def toDict(self):
        return {'actualData': self.actualData.__dict__, 'users': self.users}


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

    def __setup_path(self, value):
        localpath = os.path.join(self.data_dir, value)
        if not (os.path.isdir(localpath)):
            # This type has apparently not yet been used at all, 
            # create its directory and return an empty json file
            os.mkdir(localpath)
        return localpath


    def get_list(self, n_type: LocationDataType) -> List:
        local_path = self.__setup_path(n_type.value)
        allFiles = [f for f in os.listdir(
            local_path) if os.path.isfile(os.path.join(local_path, f))]
        # now each file has to be checked for its filename (= oid) 
        # and the LocationData name (which is inside the json)
        retList = []
        for f in allFiles:
            with open(os.path.join(local_path, f)) as file:
                data = json.load(file)
                retList.append({data['actualData']['name']: f})
        return retList

    def add_new(self, n_type: LocationDataType, data: LocationData, usr: str):
        localpath = self.__setup_path(value=n_type.value)
        # create a unique oid, by randomly generating one, 
        # and re-choosing if it is already taken
        oid = str(uuid.uuid4())
        while (os.path.exists(os.path.join(localpath, oid))):
            oid = str(uuid.uuid4())
        toStore = StoredData()
        toStore.users = [usr]
        toStore.actualData = data
        with open(os.path.join(localpath, oid), 'w') as json_file:
            json.dump(toStore.toDict(), json_file)
        return {oid: data}

    def get_details(self, type: LocationDataType, oid: str):
        localpath = os.path.join(self.data_dir, type.value)
        fullpath = os.path.join(localpath, oid)
        if not os.path.isfile(fullpath):
            raise FileNotFoundError(f"The requested object ({oid}) does not exist.")
        with open(fullpath) as file:
            data = json.load(file)
        return data['actualData']

    def update_details(self, type: LocationDataType, oid: str, data: LocationData, usr: str):
        localpath = os.path.join(self.data_dir, type.value)
        fullpath = os.path.join(localpath, oid)
        if not os.path.isfile(fullpath):
            raise FileNotFoundError(f"The requested object ({oid}) does not exist.")

        toStore = StoredData()
        toStore.actualData = data

        # get permissions from old file
        with open(fullpath) as file:
            old_data = json.load(file)
            toStore.users = old_data['users']

        with open(fullpath, 'w') as file:
            json.dump(toStore.toDict(), file)
        return {oid: data}

    def delete(self, type: LocationDataType, oid: str, usr: str):
        localpath = os.path.join(self.data_dir, type.value)
        fullpath = os.path.join(localpath, oid)

        if not os.path.isfile(fullpath):
            raise FileNotFoundError(f"The requested object {oid} does not exist.")

        os.remove(fullpath)

    def get_owner(self, type: LocationDataType, oid: str):
        raise NotImplementedError()

    def check_perm(self, type: LocationDataType, oid: str, usr: str):
        raise NotImplementedError()

    def add_perm(self, type: LocationDataType, oid: str, authUsr: str, newUser: str):
        raise NotImplementedError()

    def rm_perm(self, type: LocationDataType, oid: str, usr: str, rmUser: str):
        raise NotImplementedError()
