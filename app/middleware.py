import time
from fastapi import FastAPI, Request
from collections import deque

rolling_latency = deque(maxlen=1000)

async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    rolling_latency.append(process_time)
    response.headers["X-Process-Time"] = str(process_time)
    return response

def calculate_percentile(latency_samples: deque, target_latency_percentile: int):
    if len(latency_samples) == 0:
        return None
    sorted_samples = sorted(latency_samples)
    target_value = int((len(latency_samples) / 100) * target_latency_percentile)
    index = max(target_value - 1, 0)
    return sorted_samples[index]