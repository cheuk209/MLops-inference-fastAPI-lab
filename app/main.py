from fastapi import FastAPI
from app.schemas import PredictRequest, PredictResponse
import time

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    time.sleep(0.3)
    return PredictResponse(prediction=0.85, model_version="1.0.0")