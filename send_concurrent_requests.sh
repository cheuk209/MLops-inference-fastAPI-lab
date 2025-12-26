#!/bin/bash
set -e

CONCURRENT_REQUESTS=$1

LOCAL_ENDPOINT="http://127.0.0.1:8000/predict"

DATA='{"feature_1": 0.08, "feature_2": 0.30}'

time (
    for i in $(seq 1 $CONCURRENT_REQUESTS); do
        curl -X POST "$LOCAL_ENDPOINT" \
            -H "Content-Type: application/json" \
            -d "$DATA" &
    done
    echo "Waiting for all requests to complete"
    wait
)




echo "All $CONCURRENT_REQUESTS concurrent predictions received."
