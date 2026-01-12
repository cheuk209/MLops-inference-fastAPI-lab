"""
Exercise endpoints for learning sync/async patterns.
These are isolated from the main application and can be disabled by
removing the router include in main.py.
"""
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
import asyncio
import csv
import hashlib
import time

router = APIRouter(prefix="/exercises", tags=["exercises"])


# ============================================================
# Exercise 1: Sync vs Async Comparison Endpoints
# ============================================================

class PredictRequest(BaseModel):
    feature_1: float
    feature_2: float

class PredictResponse(BaseModel):
    prediction: float
    model_version: str


@router.post("/predict/sync", response_model=PredictResponse)
def predict_sync(request: PredictRequest):
    """Exercise 1: Blocking endpoint - uses time.sleep(), runs in thread pool."""
    import random
    latency = 0.08 + random.random() * 0.04
    time.sleep(latency)

    prediction = (request.feature_1 * 0.3 + request.feature_2 * 0.7) / 10
    return PredictResponse(
        prediction=round(prediction, 2),
        model_version="1.0.0"
    )


@router.post("/predict/async", response_model=PredictResponse)
async def predict_async(request: PredictRequest):
    """Exercise 1: Non-blocking endpoint - uses asyncio.sleep(), runs on event loop."""
    import random
    latency = 0.08 + random.random() * 0.04
    await asyncio.sleep(latency)

    prediction = (request.feature_1 * 0.3 + request.feature_2 * 0.7) / 10
    return PredictResponse(
        prediction=round(prediction, 2),
        model_version="1.0.0"
    )


@router.post("/predict/broken", response_model=PredictResponse)
async def predict_broken(request: PredictRequest):
    """Exercise 1: BROKEN - async def with blocking time.sleep() freezes event loop!"""
    import random
    latency = 0.08 + random.random() * 0.04
    time.sleep(latency)  # BAD: blocking call inside async function

    prediction = (request.feature_1 * 0.3 + request.feature_2 * 0.7) / 10
    return PredictResponse(
        prediction=round(prediction, 2),
        model_version="1.0.0"
    )


# ============================================================
# Exercise A: Database Lookup (blocking driver)
# ============================================================

@router.get("/users/{user_id}")
def get_user_id(user_id: int):
    """Exercise A: Simulates blocking database query (psycopg2 style)."""
    time.sleep(0.05)
    return {
        "user_id": user_id,
        "name": f"User {user_id}",
        "email": f"user{user_id}@example.com"
    }


# ============================================================
# Exercise B: External API Call (async HTTP client)
# ============================================================

@router.get("/weather/{city}")
async def get_weather(city: str):
    """Exercise B: Simulates async HTTP client call (httpx style)."""
    await asyncio.sleep(0.2)
    return {"city": city, "temperature": 22, "conditions": "sunny"}


# ============================================================
# Exercise C: CPU-Heavy Computation
# ============================================================

class HashRequest(BaseModel):
    data: str
    algorithm: str


@router.post("/hash")
def compute_hash(payload: HashRequest):
    """Exercise C: CPU-bound work - needs multiple workers for parallelism."""
    # CPU-intensive work (simulate ML inference)
    total = 0
    for i in range(10_000_000):
        total += i * i

    hash_result = hashlib.sha256(payload.data.encode()).hexdigest()
    return {"hash": hash_result, "algorithm": "sha256"}


# ============================================================
# Exercise D: File Read (blocking I/O)
# ============================================================

@router.get("/config")
def read_config():
    """Exercise D: Blocking file I/O - thread pool handles it."""
    config = {}
    time.sleep(0.03)  # Simulate slow file read

    from pathlib import Path
    file_path = Path(__file__).parent.parent / "exercise_config.csv"

    with open(file_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            config[row["Name"]] = row["Value"]

    return config


# ============================================================
# Exercise E: Cache Lookup (async Redis)
# ============================================================

@router.get("/cache/{cache_key}")
async def get_cache(cache_key: str):
    """Exercise E: Simulates async Redis lookup."""
    await asyncio.sleep(0.1)
    return {"key": cache_key, "value": "cached_data", "hit": True}


# ============================================================
# Exercise F: Mixed Workload (I/O + CPU)
# ============================================================

@router.post("/predict/image")
def predict_image():
    """Exercise F: Mixed I/O and CPU - use def + workers."""
    time.sleep(0.1)  # I/O: download image (thread pool)
    time.sleep(0.1)  # CPU: inference (thread pool, workers for parallelism)
    return {"prediction": "cat", "confidence": 0.95}


# ============================================================
# Exercise G: Fire-and-Forget Logging
# ============================================================

class TrackData(BaseModel):
    event: str
    user_id: int


async def send_to_analytics(event: dict):
    """Background task that runs after response is sent."""
    await asyncio.sleep(0.2)
    print(f"[Analytics] Logged: {event}")


@router.post("/track")
async def track_event(payload: TrackData, background_tasks: BackgroundTasks):
    """Exercise G: Fire-and-forget with BackgroundTasks."""
    background_tasks.add_task(send_to_analytics, payload.model_dump())
    return {"status": "accepted"}


# ============================================================
# Exercise H: Batch Parallel Requests
# ============================================================

async def fetch_service(service_id: int) -> dict:
    """Simulates fetching from a microservice."""
    await asyncio.sleep(0.1)
    return {f"service_{service_id}": f"data_{service_id}"}


@router.get("/dashboard")
async def get_dashboard():
    """Exercise H: Parallel I/O with asyncio.gather()."""
    results = await asyncio.gather(
        fetch_service(1),
        fetch_service(2),
        fetch_service(3),
        fetch_service(4),
        fetch_service(5),
    )

    combined = {}
    for r in results:
        combined.update(r)
    return combined
