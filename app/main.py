from fastapi import FastAPI
from app.schemas import PredictRequest, PredictResponse
from app.middleware import add_process_time_header
import asyncio
import random

app = FastAPI(
    title="MLOps Inference API",
    description="FastAPI service for ML inference with latency/throughput learning",
    version="1.0.0"
)

# Middleware
app.middleware("http")(add_process_time_header)

# ============================================================
# Include exercise router (comment out to disable)
# ============================================================
from app.routers.exercises import router as exercises_router
app.include_router(exercises_router)
# ============================================================


@app.get("/")
def read_root():
    return {"message": "MLOps Inference API", "docs": "/docs"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest):
    """Main prediction endpoint."""
    latency = 0.08 + random.random() * 0.04
    await asyncio.sleep(latency)

    prediction = (request.feature_1 * 0.3 + request.feature_2 * 0.7) / 10
    return PredictResponse(
        prediction=round(prediction, 2),
        model_version="1.0.0"
    )
