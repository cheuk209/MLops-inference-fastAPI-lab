# Latency Monitoring in MLOps

Notes from implementing Exercise 2.4, 2.5, and 2.6 - storing latency samples, calculating percentiles, and exposing metrics.

---

## Why Percentiles Over Averages

**Key insight from Chip Huyen's MLOps guidance**: Never rely on mean latency. Averages hide tail latencies.

| Metric | What it tells you |
|--------|-------------------|
| Mean | Misleading - one slow request is hidden by many fast ones |
| P50 (median) | Typical user experience |
| P95 | "Most users" experience - where problems start showing |
| P99 | Tail latency - critical for SLOs |

**Real example from our implementation:**

| Percentile | Fast endpoints only | After /predict requests |
|------------|---------------------|------------------------|
| P50 | ~0.25ms | ~0.26ms |
| P95 | ~0.41ms | **~104ms** |
| P99 | ~0.58ms | **~117ms** |

P50 looked fine, but P95/P99 revealed that 5-15% of users experienced 100ms+ latency.

---

## The Storage Problem

You can't store every latency sample forever. Constraints:
- **Bounded memory** - fixed upper limit regardless of traffic
- **Fast insertion** - O(1), can't slow down request handling
- **Fast percentile queries** - need real-time monitoring

### Production Approaches

| Approach | Memory | Accuracy | Use Case |
|----------|--------|----------|----------|
| `collections.deque(maxlen=N)` | O(N) | Exact | Learning, small-scale |
| NumPy ring buffer | O(N) | Exact | Fast numerical ops |
| **HDR Histogram** | O(1) fixed | Near-exact | **Production standard** |
| **T-Digest** | O(1) fixed | Approximate | Streaming, distributed |
| Prometheus histogram | O(buckets) | Approximate | Already using Prometheus |

---

## Python Implementation

### Representing a Latency Sample

Keep it simple - a `float` (seconds) is sufficient:

```python
process_time = 0.0832  # seconds
```

### Bounded Storage with `collections.deque`

```python
from collections import deque

rolling_latency = deque(maxlen=1000)  # Module-level, persists across requests
```

**Key properties:**
- Fixed size with `maxlen`
- O(1) append
- Auto-evicts oldest when full
- No manual bookkeeping

### Calculating Percentiles

`deque` has no `.sort()` method. Use `sorted()` which works on any iterable:

```python
def calculate_percentile(latency_samples: deque, target_latency_percentile: int):
    # Guard: empty deque
    if len(latency_samples) == 0:
        return None

    sorted_samples = sorted(latency_samples)
    target_value = int((len(latency_samples) / 100) * target_latency_percentile)

    # Guard: ensure index is never negative
    index = max(target_value - 1, 0)

    return sorted_samples[index]
```

---

## Pythonic Best Practices Learned

### 1. Variable Scope Matters

**Wrong** - creates new deque every request:
```python
async def middleware(request, call_next):
    rolling_latency = deque(maxlen=1000)  # Inside function!
    ...
```

**Correct** - module-level persists:
```python
rolling_latency = deque(maxlen=1000)  # Outside function!

async def middleware(request, call_next):
    rolling_latency.append(process_time)
```

### 2. Name Collisions

**Wrong** - function shadows the variable:
```python
rolling_latency = deque(maxlen=1000)

def rolling_latency():  # Same name - shadows the deque!
    ...
```

**Correct** - distinct names:
```python
rolling_latency = deque(maxlen=1000)

def calculate_percentile():  # Different name
    ...
```

### 3. Edge Case Handling

Always guard against:
- Empty collections (`len() == 0`)
- Index bounds (`max(value, 0)` to prevent negative indices)

```python
# Early return for invalid state
if len(latency_samples) == 0:
    return None

# Clamp values to valid range
index = max(target_value - 1, 0)
```

### 4. Use Built-in Functions

- `sorted(iterable)` works on any iterable (list, deque, tuple)
- Returns a new list, doesn't modify original
- Don't try `.sort()` on deque - it doesn't exist

---

## Middleware Registration Patterns

Three ways to register middleware in FastAPI:

| Pattern | Example | Best for |
|---------|---------|----------|
| Decorator | `@app.middleware("http")` | Single-file apps |
| Functional | `app.middleware("http")(fn)` | Separate modules |
| Class-based | `app.add_middleware(Class)` | Configurable middleware |

All three are equivalent under the hood.

---

## Exposing Metrics via Endpoint

### The /metrics Endpoint Pattern

A good metrics endpoint returns **pre-calculated, actionable data** - not raw samples:

```python
@app.get("/metrics")
def get_latency_metrics():
    return {
        "latency": {
            "p50": calculate_percentile(rolling_latency, 50),
            "p95": calculate_percentile(rolling_latency, 95),
            "p99": calculate_percentile(rolling_latency, 99)
        },
        "sample_count": len(rolling_latency)
    }
```

| Approach | Returns | Useful? |
|----------|---------|---------|
| Raw deque dump | 1000 floats | No - too much data |
| **Calculated percentiles** | P50, P95, P99 | Yes - actionable |
| Plus metadata | sample_count | Yes - provides context |

### Explicit vs Implicit Dependencies

**Question**: Should utility functions access global state directly or receive it as a parameter?

| Aspect | Import directly | Pass as parameter |
|--------|-----------------|-------------------|
| Simplicity | Less boilerplate | More verbose |
| Testability | Hard to mock | Easy to inject test data |
| Explicitness | Hidden dependency | Clear what function needs |
| Reusability | Tied to one data source | Works with any data source |

**Best practice:**

| Function type | Recommendation |
|---------------|----------------|
| Utility/helper functions | Pass as parameter (testable) |
| FastAPI endpoints | Import global OR use `Depends()` |

Example - `calculate_percentile` is correctly parameterized:

```python
def calculate_percentile(latency_samples: deque, percentile: int):  # Testable!
    ...
```

---

## Key Takeaways

1. **P95/P99 matter more than averages** for user experience
2. **Bounded storage** is essential - use `deque(maxlen=N)` or HDR Histogram
3. **Module-level variables** persist across requests
4. **Edge cases** will bite you - always guard empty/boundary conditions
5. **Middleware** is the right place for cross-cutting concerns like timing
6. **Metrics endpoints** should return calculated values, not raw data
7. **Parameterize utility functions** for testability; endpoints can use globals

---

## Phase 2 Complete!

- [x] Exercise 2.4: Store latency samples with bounded memory
- [x] Exercise 2.5: Calculate percentiles (P50, P95, P99)
- [x] Exercise 2.6: Create `/metrics` endpoint

## Future Improvements

- [ ] Consider HDR Histogram for production (fixed memory, high accuracy)
- [ ] Add endpoint-specific latency tracking (per-route metrics)
- [ ] Integrate with Prometheus for production monitoring
