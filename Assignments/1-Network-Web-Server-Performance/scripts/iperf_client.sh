#!/bin/bash

TARGET_DIR="../iperf_client/"
SERVER_IP="node0"
FILE_NAME_PREFIX="iperf_client_report_"

echo "--- Creating directory: ---"

mkdir -p "$TARGET_DIR"
cd "$TARGET_DIR" || exit 1

echo "--- Starting experiment: ---"

for i in {1..10}; do
  BANDWIDTH=$((i * 100))

  for j in {1..10}; do
    echo "--- Running for ${BANDWIDTH} M: ---"

    iperf3 -c "$SERVER_IP" \
      -u \
      -b "${BANDWIDTH}M" \
      -t 10 \
      -J \
      > "${FILE_NAME_PREFIX}${BANDWIDTH}M_run_${j}.json"

    echo "--- Ended for ${BANDWIDTH} M: ---"
    done

done

echo "--- Ending experiment: ---"
