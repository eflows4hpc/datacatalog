from typing import Optional
from typing import Dict

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class LocationData(BaseModel):
    name: str
    url: str
    metadata: Optional[Dict[str, str]]

#### A NOTE ON IDS
# the id of a dataset is not yet defined, it could be simply generated, it could be based on some hash of the metadata or simple be the name, which would then need to be enforced to be unique
# this might change some outputs of the GET functions that list reistered elements, but will very likely not change any part of the actual API

#### A NOTE ON LOCATION TYPES
# currently each type would need to be hardcoded, together will all api calls. It might be better to either allow any type of location Data (meaning the path fully defines it), or to make the type a forced metadata attributs.None
# this does not rule out the possibility to only enable specific location types, by comparing the requests to an enum of allowed types, which would be much more extensible


# list types of data locations, currently datasets (will be provided by the pillars) and targets (possible storage locations for worklfow results or similar)
@app.get("/")
def get_types():
    return {"Datasets" : "/datasets", "Storage Targets" : "/targets"}

# list id and name of every registered dataset
@app.get("/datasets")
def list_datasets():
    return {"A" : "JSON", "of" : "Pairs", "Dataset id": "Dataset Name"}

# register a new dataset, the response will contain the new dataset and its id
@app.put("/datasets")
def add_dataset(dataset : LocationData):
    # pretend to create the new dataset and store it
    return "If this was working your dataset would now have been created with the id \"XXXXX\". The new dataset id would be provided in the response as a json (e.g. return \{dataset_id : dataset\})."

# returns all information about a specific dataset, identified by id
@app.get("/datasets/{dataset_id}")
def get_specific_dataset(dataset_id: int):
    return {"The JSON" : "of the dataset", "with the id" : dataset_id}

# update the information about a specific dataset, identified by id
@app.put("/datasets/{dataset_id}")
def update_specific_dataset(dataset_id: int, dataset : LocationData):
    return {"The Dataset" : "with the id", dataset_id : "has been upddated:", "name" : dataset.name, "url" : dataset.url, "metadata" : dataset.metadata}

# list id and name of every registered target
@app.get("/targets")
def list_targets():
    return {"A" : "JSON", "of" : "Pairs", "target id": "target URL"}

# register a new target, the response will contain the new target and its id
@app.put("/targets")
def add_target(target : LocationData):
    # pretend to create the new target and store it
    return "If thsi was working your target would now have been created with the id \"XXXXX\". The new target would be provided in the response as a json (e.g. return \{target_id : target\})."

# returns all information about a specific target, identified by id
@app.get("/targets/{target_id}")
def get_specific_target(target_id: int):
    return {"The JSON" : "of the target", "with the id" : target_id}

# update the information about a specific target, identified by id
@app.put("/targets/{target_id}")
def update_specific_target(target_id: int, target : LocationData):
    return {"The target" : "with the id", target_id : "has been upddated:", "name" : target.name, "url" : target.url, "metadata" : target.metadata}