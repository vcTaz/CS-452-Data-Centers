#!/bin/bash
set -euo pipefail

export PATH="$HOME/bin:$PATH"

SERVER_IP="node0"
FILE_NAME_PREFIX="vegeta_attack_report_"

DURATION=30
REPETITIONS=10
COOLDOWN=5

RATES=(1000 2000 3000 4000 5000 6000 7000 8000 9000 10000
       12000 14000 16000 18000 19000 20000)

BASE_DIR="$HOME/CS-452-Data-Centers/Assignments/1-Network-Web-Server-Performance"
TARGET_DIR="$BASE_DIR/vegeta-results/final_$(date +%Y%m%d_%H%M%S)"

mkdir -p "$TARGET_DIR"
cd "$TARGET_DIR"

ssh -o BatchMode=yes "$SERVER_IP" '
    test "$(pgrep -fc "^nginx: worker process")" -eq 1
    command -v pidstat >/dev/null
'

echo "--- Starting experiment ---"
echo "Results directory: $TARGET_DIR"

for RATE in "${RATES[@]}"; do

    for j in $(seq 1 "$REPETITIONS"); do

        PREFIX="${FILE_NAME_PREFIX}${RATE}_run_${j}"

        echo "-----------------------------------"
        echo "Running ${RATE} RPS - Run ${j}"
        echo "-----------------------------------"

        ssh -o BatchMode=yes "$SERVER_IP" '
            PID=$(pgrep -f "^nginx: worker process")
            exec pidstat -u -p "$PID" 1 36
        ' > "${PREFIX}_cpu.txt" &

        MONITOR_PID=$!

        sleep 2

        echo "GET http://${SERVER_IP}/" |
            vegeta attack \
                -rate="$RATE" \
                -duration="${DURATION}s" \
                > "${PREFIX}.bin"

        wait "$MONITOR_PID"

        vegeta report -type=json "${PREFIX}.bin" \
            > "${PREFIX}.json"

        vegeta report "${PREFIX}.bin"

        echo "Completed ${RATE} RPS - Run ${j}"

        sleep "$COOLDOWN"

    done
done

echo "--- Experiment completed ---"
echo "Results saved in: $TARGET_DIR"

