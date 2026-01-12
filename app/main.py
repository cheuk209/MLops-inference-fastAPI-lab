from fastapi import FastAPI, BackgroundTasks
from app.schemas import PredictRequest, PredictResponse
from app.middleware import add_process_time_header
import asyncio
import random
import time
import hashlib
from pydantic import BaseModel
import csv

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

@app.get("/users/{user_id}")
def get_user_id(user_id: int):
    time.sleep(0.05)
    user_data = {
        "User ID": user_id,
        "Name": f"User {user_id}",
        "email": f"user{user_id}@example.com"
    }
    return user_data

@app.get("/weather/{city}")
async def get_httpx_response(city: str):
    await asyncio.sleep(0.2)
    return {"city": city, "temperature": 22}


class LargePayload(BaseModel):
    data: str
    algorithm: str

@app.post("/hash")
def crypto_has_data(payload: LargePayload):
    payload_content = payload.data 
    hash = hashlib.sha256(b"{payload_content}").hexdigest()
    total = 0
    for i in range(10_000_000):
      total += i * i  # Math operations
    return {"hash": hash, "algorithm": "sha256"}

@app.get("/config")
def read_file():
    config = {}
    time.sleep(0.2)
    with open("app/exercise_config.csv", "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            config[row["Name"]] = row["Value"]

    return config

@app.get("/cache/{cache_key}")
async def get_redis_lookup(cache_key: str):
    await asyncio.sleep(0.1)
    return {"key": cache_key, "value": "cache_data"}

@app.post("/predict/image")
def predict_image():
    time.sleep(0.1) ## Letting threadpool handle it
    time.sleep(0.1) ## CPU inference 
    return {"prediction": "cat", "confidence": 0.5}

class TrackData(BaseModel):
    event: str
    user_id: int


async def send_to_analytics(event: dict):
    await asyncio.sleep(0.2)
    print(f"Logged: {event}")

@app.post("/track")
async def accept_track(payload: TrackData, background_tasks: BackgroundTasks):
    background_tasks.add_task(send_to_analytics, payload)
    return {"status": "accepted"}

@app.get("/dashboard")
async def get_dashboard():
    await asyncio.gather(
        asyncio.sleep(0.1),
        asyncio.sleep(0.1),
        asyncio.sleep(0.1),
        asyncio.sleep(0.1),
    )

    return {"service1": "blah", "service2": "blah", "service3": "blah","service4": "blah","service5": "blah" }