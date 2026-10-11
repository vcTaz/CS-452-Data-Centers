#!/bin/bash
set -euo pipefail

export PATH="$HOME/bin:$PATH"

SERVER_NODE_0="node0"
SERVER_NODE_2="node2"

ATTACKER_HOSTNAME=$(hostname -s)
FILE_NAME_PREFIX="vegeta_multi_node_attack_${ATTACKER_HOSTNAME}_report_"

DURATION=30
REPETITIONS=10
COOLDOWN=5
CLIENT_COUNT=2

RATES=(2000 4000 6000 8000 10000
       12000 14000 16000 18000 20000
       24000 28000 32000 36000 38000)

BASE_DIR="$HOME/CS-452-Data-Centers/Assignments/1-Network-Web-Server-Performance"
TARGET_DIR="$BASE_DIR/vegeta-results-multi-node_${ATTACKER_HOSTNAME}/final_$(date +%Y%m%d_%H%M%S)"

mkdir -p "$TARGET_DIR"
cd "$TARGET_DIR"

for SERVER in "$SERVER_NODE_0" "$SERVER_NODE_2"; do
    ssh -o BatchMode=yes "$SERVER" '
        test "$(pgrep -fc "^nginx: worker process")" -eq 1
        command -v pidstat >/dev/null
    '
done

echo "--- Starting multi-node experiment ---"
echo "Attacker: $ATTACKER_HOSTNAME"
echo "Results: $TARGET_DIR"

for RATE in "${RATES[@]}"; do

    CLIENT_RATE=$((RATE / CLIENT_COUNT))

    for j in $(seq 1 "$REPETITIONS"); do

        PREFIX="${FILE_NAME_PREFIX}${RATE}_run_${j}"

        echo "-----------------------------------"
        echo "Aggregate target: ${RATE} RPS"
        echo "Client target: ${CLIENT_RATE} RPS"
        echo "Run: ${j}"
        echo "-----------------------------------"

        ssh -o BatchMode=yes "$SERVER_NODE_0" '
            PID=$(pgrep -f "^nginx: worker process")
            exec pidstat -u -p "$PID" 1 36
        ' > "${PREFIX}_node0_cpu.txt" &

        MONITOR_0_PID=$!

        ssh -o BatchMode=yes "$SERVER_NODE_2" '
            PID=$(pgrep -f "^nginx: worker process")
            exec pidstat -u -p "$PID" 1 36
        ' > "${PREFIX}_node2_cpu.txt" &

        MONITOR_2_PID=$!

        sleep 2

        printf 'GET http://%s/\nGET http://%s/\n' \
            "$SERVER_NODE_0" "$SERVER_NODE_2" |
            vegeta attack \
                -rate="$CLIENT_RATE" \
                -duration="${DURATION}s" \
                > "${PREFIX}.bin"

        wait "$MONITOR_0_PID"
        wait "$MONITOR_2_PID"

        vegeta report -type=json "${PREFIX}.bin" \
            > "${PREFIX}.json"

        vegeta report "${PREFIX}.bin"

        echo "Completed ${RATE} RPS - Run ${j}"

        sleep "$COOLDOWN"
    done
done

echo "--- Experiment completed ---"
echo "Results saved in: $TARGET_DIR"
