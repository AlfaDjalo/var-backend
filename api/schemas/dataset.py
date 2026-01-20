from pydantic import BaseModel
from typing import List

class DatasetListResponse(BaseModel):
    datasets: List[str]

class DatasetInspectRequest(BaseModel):
    dataset_name: str

class DatasetInspectResponse(BaseModel):
    assets: List[str]
