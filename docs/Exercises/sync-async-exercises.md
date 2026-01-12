# Sync vs Async Exercises

Practice problems to build intuition for when to use `def`, `async def`, threads, and workers.

For each exercise:
1. Read the scenario
2. Decide: `def` or `async def`? Why?
3. Implement the endpoint
4. Test with concurrent requests
5. Check your answer against the solution rationale

---

## Exercise A: Database Lookup (Blocking Driver)

### Scenario
You have a PostgreSQL database with user information. The database driver (`psycopg2`) is **synchronous** - it blocks while waiting for the query.

### Task
Create endpoint `GET /users/{user_id}` that:
- Simulates a database query taking 50ms
- Returns user info: `{"user_id": ..., "name": "User {id}", "email": "..."}`

### Hints
- `psycopg2` is blocking (not async-compatible)
- What happens if you use `async def` with blocking code?

### Test
```bash
time (for i in $(seq 1 10); do curl -s "http://localhost:8000/users/$i" & done; wait)
```

<details>
<summary>Solution Rationale (click after implementing)</summary>

**Use `def` (sync function)**

Why: The database driver is blocking. If you use `async def` with a blocking call, you freeze the event loop. With `def`, FastAPI runs it in the thread pool, allowing concurrent requests.

```python
@app.get("/users/{user_id}")
def get_user(user_id: int):
    time.sleep(0.05)  # Simulates blocking DB query
    return {"user_id": user_id, "name": f"User {user_id}", "email": f"user{user_id}@example.com"}
```

Expected: 10 requests in ~0.05-0.15s (thread pool concurrency)
</details>

---

## Exercise B: External API Call (Async HTTP Client)

### Scenario
Your service needs to fetch data from an external weather API. You're using `httpx` which supports async.

### Task
Create endpoint `GET /weather/{city}` that:
- Simulates calling an external API (200ms delay)
- Returns: `{"city": ..., "temperature": 22, "conditions": "sunny"}`

### Hints
- `httpx.AsyncClient` is async-compatible
- What's the right pattern for async I/O?

### Test
```bash
time (for i in $(seq 1 10); do curl -s "http://localhost:8000/weather/london" & done; wait)
```

<details>
<summary>Solution Rationale (click after implementing)</summary>

**Use `async def` with `await`**

Why: The HTTP client is async-compatible. Using `async def` + `await` allows the event loop to handle many concurrent requests efficiently without threads.

```python
@app.get("/weather/{city}")
async def get_weather(city: str):
    await asyncio.sleep(0.2)  # Simulates async API call
    return {"city": city, "temperature": 22, "conditions": "sunny"}
```

Expected: 10 requests in ~0.2s (true async concurrency)
</details>

---

## Exercise C: CPU-Heavy Computation

### Scenario
Your endpoint needs to compute a cryptographic hash of a large payload. This is **CPU-bound** work - no I/O waiting.

### Task
Create endpoint `POST /hash` that:
- Accepts `{"data": "some string"}`
- Simulates CPU-intensive hashing (100ms of computation)
- Returns: `{"hash": "abc123...", "algorithm": "sha256"}`

### Hints
- CPU-bound means the CPU is busy, not waiting
- What does the GIL do to CPU-bound threads?
- Think about what actually helps here

### Test
```bash
time (for i in $(seq 1 10); do curl -s -X POST "http://localhost:8000/hash" \
  -H "Content-Type: application/json" \
  -d '{"data": "test"}' & done; wait)
```

<details>
<summary>Solution Rationale (click after implementing)</summary>

**Use `def` (sync function) + multiple workers for true parallelism**

Why: CPU-bound work holds the GIL. Neither async nor threads help. You need multiple **processes** (workers) for parallelism.

```python
@app.post("/hash")
def compute_hash(payload: dict):
    # Simulate CPU-intensive work
    start = time.perf_counter()
    while time.perf_counter() - start < 0.1:  # Busy loop for 100ms
        pass
    return {"hash": "abc123fake", "algorithm": "sha256"}
```

With 1 worker: 10 requests ≈ 1.0s (sequential due to GIL)
With 4 workers: 10 requests ≈ 0.3s (parallel across processes)

Test with: `uvicorn app.main:app --workers 4`
</details>

---

## Exercise D: File Read (Blocking I/O)

### Scenario
Your endpoint reads a configuration file from disk. Standard Python file I/O is **blocking**.

### Task
Create endpoint `GET /config` that:
- Simulates reading a file (30ms)
- Returns: `{"setting_a": "value1", "setting_b": "value2"}`

### Hints
- `open()` and `file.read()` are blocking operations
- There's no `await open()` in standard Python

### Test
```bash
time (for i in $(seq 1 10); do curl -s "http://localhost:8000/config" & done; wait)
```

<details>
<summary>Solution Rationale (click after implementing)</summary>

**Use `def` (sync function)**

Why: Standard file I/O is blocking. Use `def` to let FastAPI's thread pool handle it. Alternative: use `aiofiles` library for async file I/O.

```python
@app.get("/config")
def get_config():
    time.sleep(0.03)  # Simulates blocking file read
    return {"setting_a": "value1", "setting_b": "value2"}
```

Expected: 10 requests in ~0.03-0.1s (thread pool concurrency)
</details>

---

## Exercise E: Cache Lookup (Async Redis)

### Scenario
Your service uses Redis for caching. The `redis.asyncio` client is async-compatible.

### Task
Create endpoint `GET /cache/{key}` that:
- Simulates async Redis lookup (10ms)
- Returns: `{"key": ..., "value": "cached_data", "hit": true}`

### Hints
- Redis async client uses `await`
- This is fast I/O (10ms)

### Test
```bash
time (for i in $(seq 1 100); do curl -s "http://localhost:8000/cache/key$i" & done; wait)
```

<details>
<summary>Solution Rationale (click after implementing)</summary>

**Use `async def` with `await`**

Why: Redis async client is async-compatible. For high-throughput cache lookups, async is ideal - you can handle thousands of concurrent requests on a single thread.

```python
@app.get("/cache/{key}")
async def get_cache(key: str):
    await asyncio.sleep(0.01)  # Simulates async Redis lookup
    return {"key": key, "value": "cached_data", "hit": True}
```

Expected: 100 requests in ~0.01-0.05s (highly concurrent)
</details>

---

## Exercise F: Mixed Workload - ML Preprocessing + Inference

### Scenario
Your ML endpoint does two things:
1. **Preprocessing**: Downloads an image from URL (I/O-bound, 100ms)
2. **Inference**: Runs ML model on image (CPU-bound, 100ms)

### Task
Create endpoint `POST /predict/image` that:
- Accepts `{"image_url": "http://..."}`
- Simulates downloading image (100ms I/O)
- Simulates ML inference (100ms CPU)
- Returns: `{"prediction": "cat", "confidence": 0.95}`

### Hints
- This has BOTH I/O and CPU components
- What's the best pattern for mixed workloads?

### Test
```bash
time (for i in $(seq 1 5); do curl -s -X POST "http://localhost:8000/predict/image" \
  -H "Content-Type: application/json" \
  -d '{"image_url": "http://example.com/img.jpg"}' & done; wait)
```

<details>
<summary>Solution Rationale (click after implementing)</summary>

**Use `def` (sync function) + multiple workers**

Why: The CPU-bound inference will block regardless. While you *could* do async download + sync inference, the complexity isn't worth it for this case. Let the thread pool handle the I/O, use workers for CPU parallelism.

```python
@app.post("/predict/image")
def predict_image(payload: dict):
    # I/O: Download image
    time.sleep(0.1)

    # CPU: Run inference (blocks GIL)
    start = time.perf_counter()
    while time.perf_counter() - start < 0.1:
        pass

    return {"prediction": "cat", "confidence": 0.95}
```

With 1 worker: 5 requests ≈ 1.0s
With 4 workers: 5 requests ≈ 0.4s

For production ML services, consider separating I/O and inference into different services.
</details>

---

## Exercise G: Fire-and-Forget Logging

### Scenario
Your endpoint needs to log analytics events to an external service, but you don't want to wait for the logging to complete before responding.

### Task
Create endpoint `POST /track` that:
- Accepts `{"event": "page_view", "user_id": 123}`
- Sends event to analytics service (simulated 200ms)
- Returns immediately: `{"status": "accepted"}`

### Hints
- User shouldn't wait for logging
- Look up `asyncio.create_task()` or FastAPI `BackgroundTasks`

### Test
```bash
time curl -s -X POST "http://localhost:8000/track" \
  -H "Content-Type: application/json" \
  -d '{"event": "page_view", "user_id": 123}'
```

<details>
<summary>Solution Rationale (click after implementing)</summary>

**Use `async def` with `BackgroundTasks`**

Why: The response should return immediately. Background tasks run after the response is sent.

```python
from fastapi import BackgroundTasks

async def send_to_analytics(event: dict):
    await asyncio.sleep(0.2)  # Simulates slow analytics API
    print(f"Logged: {event}")

@app.post("/track")
async def track_event(payload: dict, background_tasks: BackgroundTasks):
    background_tasks.add_task(send_to_analytics, payload)
    return {"status": "accepted"}
```

Expected: Response in ~0.001s (immediate), logging happens in background
</details>

---

## Exercise H: Batch Parallel Requests

### Scenario
Your endpoint needs to fetch data from 5 different microservices and combine the results.

### Task
Create endpoint `GET /dashboard` that:
- Fetches from 5 services in parallel (each takes 100ms)
- Combines results
- Returns: `{"service_1": ..., "service_2": ..., ...}`

### Hints
- Sequential: 5 × 100ms = 500ms
- Parallel: should be ~100ms
- Look up `asyncio.gather()`

### Test
```bash
time curl -s "http://localhost:8000/dashboard"
```

<details>
<summary>Solution Rationale (click after implementing)</summary>

**Use `async def` with `asyncio.gather()`**

Why: All 5 calls are independent I/O operations. `gather()` runs them concurrently.

```python
async def fetch_service(service_id: int):
    await asyncio.sleep(0.1)  # Simulates API call
    return {f"service_{service_id}": f"data_{service_id}"}

@app.get("/dashboard")
async def get_dashboard():
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
```

Expected: ~0.1s (all 5 run in parallel)
</details>

---

## Summary Decision Tree

After completing all exercises, you should internalize this:

```
Is the library/operation async-compatible?
│
├── YES (httpx, asyncpg, redis.asyncio, aiofiles)
│   │
│   └── Use `async def` + `await`
│       └── For parallel I/O: use `asyncio.gather()`
│       └── For fire-and-forget: use `BackgroundTasks`
│
├── NO (psycopg2, open(), requests, blocking libs)
│   │
│   └── Use `def` (FastAPI thread pool handles it)
│
└── CPU-BOUND (ML inference, hashing, image processing)
    │
    └── Use `def` + multiple workers (`--workers N`)
        └── For very heavy work: consider background queue (Celery)
```

---

## Scoring Your Understanding

| Exercises Correct | Level |
|-------------------|-------|
| 8/8 | Expert - ready for production MLOps |
| 6-7/8 | Solid - review the ones you missed |
| 4-5/8 | Getting there - re-read the docs |
| <4/8 | Review Part 6-7 of threading-fundamentals.md |

---

## Quick Reference: Pattern Summary

| Exercise | Scenario | Pattern | Why |
|----------|----------|---------|-----|
| **A** | Database (blocking driver) | `def` | Blocking lib → thread pool handles it |
| **B** | External API (async HTTP) | `async def` + `await` | Async lib → event loop handles it |
| **C** | CPU-heavy computation | `def` + `--workers N` | CPU-bound → need multiple processes to bypass GIL |
| **D** | File read (blocking I/O) | `def` | `open()` is blocking → thread pool |
| **E** | Cache lookup (async Redis) | `async def` + `await` | Async lib → high concurrency on event loop |
| **F** | Mixed I/O + CPU | `def` + `--workers N` | Simpler than mixing patterns; workers handle both |
| **G** | Fire-and-forget logging | `async def` + `BackgroundTasks` | Return immediately, work happens after response |
| **H** | Batch parallel requests | `async def` + `asyncio.gather()` | Run multiple async calls concurrently |

---

## The Golden Rules

1. **Blocking library?** → Use `def` (thread pool)
2. **Async library?** → Use `async def` + `await` (event loop)
3. **CPU-bound?** → Use `def` + multiple workers (processes)
4. **Need to return fast?** → Use `BackgroundTasks`
5. **Multiple independent I/O calls?** → Use `asyncio.gather()`
6. **Never mix `async def` with blocking code** → Freezes event loop
