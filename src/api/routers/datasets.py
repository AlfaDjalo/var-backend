# from fastapi import FastAPI
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import os
import uuid
import shutil
from pydantic import BaseModel

from api.config import DATA_PATH
from var_engine.data_loader.csv_loader import CSVPriceLoader

# app = FastAPI()
router = APIRouter()

DATA_DIR = DATA_PATH
print("DATA_DIR: ", DATA_DIR)
# DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

@router.get("/datasets")
def list_sample_files():
    files = os.listdir(DATA_DIR)
    # Filter only CSV or allowed extensions, if needed
    sample_files = [f for f in files if f.endswith(".csv")]
    return {"files": sample_files}

@router.get("/datasets/{filename}")
def get_sample_file(filename: str):
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        return {"error": "File not found"}
    return FileResponse(filepath, media_type="text/csv", filename=filename)

@router.post("/datasets/upload")
def upload_dataset(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")

    unique_name = f"{uuid.uuid4().hex}_{file.filename}"
    target_path = os.path.join(DATA_DIR, unique_name)

    with open(target_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"filename": unique_name}

class InspectRequest(BaseModel):
    dataset_name: str

@router.post("/datasets/inspect")
def inspect_dataset(request: InspectRequest):
    file_path = f"{DATA_DIR}/{request.dataset_name}"
    print(file_path)

    try:
        loader = CSVPriceLoader(path=file_path)
        df = loader.load_prices()  # Use load_prices here to get prices, not returns
        if df.empty:
            raise HTTPException(status_code=400, detail="Price data is empty")

        asset_columns = [c for c in df.columns if c.lower() != "date"]

        # Get last available prices as dict
        spot_prices = df.iloc[-1].to_dict()

        return {
            "assets": asset_columns,
            "spot_prices": spot_prices,
        }

    except Exception as e:
        print(f"Error retrieving asset names and spot prices: {e}")
        raise HTTPException(status_code=400, detail=f"Data load failed: {str(e)}")


