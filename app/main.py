from fastapi import FastAPI
from app.schemas import PredictRequest, PredictResponse
import time, random, asyncio

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest):
    latency = 0.08 + random.random() * 0.04
    asyncio.sleep(latency)

    prediction = (request.feature_1 * 0.3 + request.feature_2 * 0.7) / 10
    return PredictResponse(
        prediction=round(prediction, 2),
        model_version="1.0.0"
    )