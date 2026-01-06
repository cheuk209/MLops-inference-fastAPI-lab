#!/bin/bash
set -e

CONCURRENT_REQUESTS=${1:-10}

SYNC_ENDPOINT="http://127.0.0.1:8000/predict/sync"
ASYNC_ENDPOINT="http://127.0.0.1:8000/predict/async"

DATA='{"feature_1": 0.08, "feature_2": 0.30}'
  
echo "=== Testing SYNC endpoint ($CONCURRENT_REQUESTS requests) ==="
time (
    for i in $(seq 1 $CONCURRENT_REQUESTS); do
        curl -X POST "$SYNC_ENDPOINT" \
            -H "Content-Type: application/json" \
            -d "$DATA" &
    done
    echo "Waiting for all sync/blocking requests to complete"
    wait
)

echo "=== Testing SYNC endpoint ($CONCURRENT_REQUESTS requests) ==="
time (
    for i in $(seq 1 $CONCURRENT_REQUESTS); do
        curl -X POST "$ASYNC_ENDPOINT" \
            -H "Content-Type: application/json" \
            -d "$DATA" &
    done
    echo "Waiting for all sync/blocking requests to complete"
    wait
)

echo "=== Testing BROKEN endpoint (10 requests) ==="
time (
    for i in $(seq 1 $CONCURRENT_REQUESTS); do
        curl -s -X POST "http://127.0.0.1:8000/predict/broken" \
            -H "Content-Type: application/json" \
            -d "$DATA" &
    done
    wait
)

echo "All $CONCURRENT_REQUESTS concurrent predictions received."
