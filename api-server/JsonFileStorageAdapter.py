import os
import json
import uuid

from LocationStorage import AbstractLocationDataStorageAdapter, LocationData, LocationDataType


DEFAULT_JSON_FILEPATH: str = "./app/data"

class JsonFileStorageAdapter(AbstractLocationDataStorageAdapter):
    data_dir: str

    def __init__(self, data_directory: str = DEFAULT_JSON_FILEPATH):
        AbstractLocationDataStorageAdapter.__init__(self)
        self.data_dir = data_directory
        if not (os.path.exists(self.data_dir) and os.path.isdir(self.data_dir)):
            raise Exception('Data Directory \"' + self.data_dir + '\" does not exist.')

    def getList(self, type: LocationDataType):
        localpath = os.path.join(self.data_dir, type.value)
        if not (os.path.isdir(localpath)):
            # This type has apparently not yet been used at all, create its directory and return an empty json file
            os.mkdir(localpath)
            return {}
        else:
            allFiles = [f for f in os.listdir(localpath) if os.path.isfile(os.path.join(localpath, f))]
            # now each file has to be checked for its filename (= id) and the LocationData name (which is inside the json)
            retList = []
            for f in allFiles:
                with open(os.path.join(localpath, f)) as file:
                    data = json.load(file)
                    retList.append({data['name'] : f})
            return retList

    def addNew(self, type: LocationDataType, data: LocationData):
        localpath = os.path.join(self.data_dir, type.value)
        if not (os.path.isdir(localpath)):
            # This type has apparently not yet been used at all, therefore we need to create its directory
            os.mkdir(localpath)
        # create a unique id, by randomly generating one, and re-choosing if it is already taken
        id = str(uuid.uuid4())
        while (os.path.exists(os.path.join(localpath, id))):
            id = str(uuid.uuid4())
        with open(os.path.join(localpath, id), 'w') as json_file:
            json.dump(data.__dict__, json_file)
        return {id : data}

    def getDetails(self, type: LocationDataType, id: str):
        localpath = os.path.join(self.data_dir, type.value)
        fullpath = os.path.join(localpath, id)
        if not os.path.isfile(fullpath):
            raise FileNotFoundError('The requested Object does not exist.')
        with open(fullpath) as file:
            data = json.load(file)
        return data

    def updateDetails(self, type:LocationDataType, id:str, data: LocationData):
        localpath = os.path.join(self.data_dir, type.value)
        fullpath = os.path.join(localpath, id)
        if not os.path.isfile(fullpath):
            raise FileNotFoundError('The requested Object does not exist.')
        with open(fullpath, 'w') as file:
            json.dump(data.__dict__, file)
        return {id : data}
