from fastapi import FastAPI
from app.schemas import PredictRequest, PredictResponse
from app.middleware import add_process_time_header
import asyncio
import random
import time

app = FastAPI()
app.middleware("http")(add_process_time_header)


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/predict/sync", response_model=PredictResponse)
def predict_sync(request: PredictRequest):
    """Blocking endpoint - uses time.sleep(), runs in thread pool."""
    latency = 0.08 + random.random() * 0.04
    time.sleep(latency)

    prediction = (request.feature_1 * 0.3 + request.feature_2 * 0.7) / 10
    return PredictResponse(
        prediction=round(prediction, 2),
        model_version="1.0.0"
    )


@app.post("/predict/async", response_model=PredictResponse)
async def predict_async(request: PredictRequest):
    """Non-blocking endpoint - uses asyncio.sleep(), runs on event loop."""
    latency = 0.08 + random.random() * 0.04
    await asyncio.sleep(latency)

    prediction = (request.feature_1 * 0.3 + request.feature_2 * 0.7) / 10
    return PredictResponse(
        prediction=round(prediction, 2),
        model_version="1.0.0"
    )


@app.post("/predict/broken", response_model=PredictResponse)
async def predict_broken(request: PredictRequest):
    """BROKEN: async def with blocking time.sleep() - freezes event loop!"""
    latency = 0.08 + random.random() * 0.04
    time.sleep(latency)  # BAD: blocking call inside async function

    prediction = (request.feature_1 * 0.3 + request.feature_2 * 0.7) / 10
    return PredictResponse(
        prediction=round(prediction, 2),
        model_version="1.0.0"
    )