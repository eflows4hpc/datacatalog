import os
import json
import uuid

from .LocationStorage import AbstractLocationDataStorageAdapter, LocationData, LocationDataType

from apiserver.config import ApiserverSettings

from typing import List

class StoredData:
    actualData: LocationData
    users: List[str]

    def toDict(self):
        return {'actualData' : self.actualData.__dict__, 'users' : self.users}


# This stores LocationData via the StoredData Object as json files
# These Jsonfiles then contain the actualData, as well as the users with permissions for this LocationData
# all users have full permission to to anything with this dataobject, uncluding removing their own access (this might trigger a confirmation via the frontend, but this is not enforced via the api)
# IMPORTANT: The adapter does not check for authentication or authorization, it should only be invoked if the permissions have been checked
class JsonFileStorageAdapter(AbstractLocationDataStorageAdapter):
    data_dir: str

    def __init__(self, settings: ApiserverSettings):
        AbstractLocationDataStorageAdapter.__init__(self)
        self.data_dir = settings.json_storage_path
        if not (os.path.exists(self.data_dir) and os.path.isdir(self.data_dir)):
            raise Exception('Data Directory \"' + self.data_dir + '\" does not exist.')

    def getList(self, type: LocationDataType) -> List:
        localpath = os.path.join(self.data_dir, type.value)
        if not (os.path.isdir(localpath)):
            # This type has apparently not yet been used at all, create its directory and return an empty json file
            os.mkdir(localpath)
            return []
        else:
            allFiles = [f for f in os.listdir(localpath) if os.path.isfile(os.path.join(localpath, f))]
            # now each file has to be checked for its filename (= id) and the LocationData name (which is inside the json)
            retList = []
            for f in allFiles:
                with open(os.path.join(localpath, f)) as file:
                    data = json.load(file)
                    retList.append({data['actualData']['name'] : f})
            return retList

    def addNew(self, type: LocationDataType, data: LocationData, usr: str):
        localpath = os.path.join(self.data_dir, type.value)
        if not (os.path.isdir(localpath)):
            # This type has apparently not yet been used at all, therefore we need to create its directory
            os.mkdir(localpath)
        # create a unique id, by randomly generating one, and re-choosing if it is already taken
        id = str(uuid.uuid4())
        while (os.path.exists(os.path.join(localpath, id))):
            id = str(uuid.uuid4())
        toStore = StoredData()
        toStore.users = [usr]
        toStore.actualData = data
        with open(os.path.join(localpath, id), 'w') as json_file:
            json.dump(toStore.toDict(), json_file)
        return {id : data}

    def getDetails(self, type: LocationDataType, id: str):
        localpath = os.path.join(self.data_dir, type.value)
        fullpath = os.path.join(localpath, id)
        if not os.path.isfile(fullpath):
            raise FileNotFoundError('The requested Object does not exist.')
        with open(fullpath) as file:
            data = json.load(file)
        return data['actualData']

    def updateDetails(self, type:LocationDataType, id:str, data: LocationData, usr: str):
        localpath = os.path.join(self.data_dir, type.value)
        fullpath = os.path.join(localpath, id)
        if not os.path.isfile(fullpath):
            raise FileNotFoundError('The requested Object does not exist.')
        
        toStore = StoredData()
        toStore.actualData = data

        # get permissions from old file
        with open(fullpath) as file:
            old_data = json.load(file)
            toStore.users = old_data['users']

        with open(fullpath, 'w') as file:
            json.dump(toStore.toDict(), file)
        return {id : data}

    def delete(self, type:LocationDataType, id:str, usr: str):
        localpath = os.path.join(self.data_dir, type.value)
        fullpath = os.path.join(localpath, id)
        
        if not os.path.isfile(fullpath):
            raise FileNotFoundError('The requested Object does not exist.')
        
        os.remove(fullpath)

    def getOwner(self, type: LocationDataType, id: str):
        raise NotImplementedError()

    def checkPerm(self, type: LocationDataType, id: str, usr: str):
        raise NotImplementedError()

    def addPerm(self, type: LocationDataType, id: str, authUsr: str, newUser: str):
        raise NotImplementedError()

    def rmPerm(self, type: LocationDataType, id: str, usr: str, rmUser: str):
        raise NotImplementedError()