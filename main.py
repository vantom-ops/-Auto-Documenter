from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os

app = FastAPI(title="Hardware Shop Data Tools")

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/")
def root():
    return {"message": "Hardware Shop Backend is running 🚀"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    # Save uploaded file
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # Read CSV
    df = pd.read_csv(file_path)

    # Example analytics for hardware shop
    result = {
        "message": "File processed successfully ✅",
        "total_items": df.shape[0],
        "columns_detected": df.shape[1],
        "missing_values": int(df.isnull().sum().sum()),
        "duplicate_products": int(df.duplicated().sum()),
        "categories": df['Category'].nunique() if 'Category' in df.columns else "N/A",
        "total_stock": int(df['Quantity'].sum()) if 'Quantity' in df.columns else "N/A"
    }

    return result
