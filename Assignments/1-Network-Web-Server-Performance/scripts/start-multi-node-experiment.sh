#!/bin/bash
set -euo pipefail

BASE="$HOME/CS-452-Data-Centers/Assignments/1-Network-Web-Server-Performance"
SCRIPT="$BASE/scripts/run_vegeta_multi.sh"

START_AT=$(($(date +%s) + 20))

echo "=== Multi-node Nginx Experiment ==="
echo "Scheduled start: $(date -d "@$START_AT")"

# Verify local script exists
if [[ ! -f "$SCRIPT" ]]; then
    echo "ERROR: Local experiment script not found"
    exit 1
fi

# Verify SSH and remote script
ssh -o BatchMode=yes -o ConnectTimeout=5 node3 \
    "test -f '$SCRIPT'" || {
    echo "ERROR: Cannot access node3 or remote script"
    exit 1
}

# Create log directory
LOG_DIR="$BASE/logs/multi_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$LOG_DIR"

echo "Logs: $LOG_DIR"

# Start experiment on node3
ssh -o BatchMode=yes node3 \
    "DELAY=\$(( $START_AT - \$(date +%s) )); \
     if (( DELAY > 0 )); then sleep \$DELAY; fi; \
     bash '$SCRIPT'" \
    > "$LOG_DIR/node3.log" 2>&1 &

REMOTE_PID=$!

# Wait for scheduled start
DELAY=$((START_AT - $(date +%s)))
if (( DELAY > 0 )); then
    sleep "$DELAY"
fi

# Start experiment on node1
bash "$SCRIPT" > "$LOG_DIR/node1.log" 2>&1 &
LOCAL_PID=$!

# Wait for both experiments, even if one fails
REMOTE_STATUS=0
LOCAL_STATUS=0

wait "$REMOTE_PID" || REMOTE_STATUS=$?
wait "$LOCAL_PID" || LOCAL_STATUS=$?

echo "=============================="
echo "node1 exit status: $LOCAL_STATUS"
echo "node3 exit status: $REMOTE_STATUS"
echo "=============================="

if (( REMOTE_STATUS != 0 || LOCAL_STATUS != 0 )); then
    echo "ERROR: One or both experiments failed."
    echo "Check logs in: $LOG_DIR"
    exit 1
fi

echo "Both experiments completed successfully."
echo "Logs saved in: $LOG_DIR"

