#!/bin/bash

TARGET_DIR="../iperf_client/"
SERVER_IP="node0"
FILE_NAME_PREFIX="iperf_client_report_"

echo "----------------------------"
echo "---- Creating directory: ---"
echo "----------------------------"

mkdir -p "$TARGET_DIR"
cd "$TARGET_DIR" || exit 1

echo "----------------------------"
echo "--- Starting experiment: ---"
echo "----------------------------"

for i in {1..10}; do
  BANDWIDTH=$((i * 100))

  for j in {1..10}; do
    echo "-----------------------------------"
    echo "--- Running for ${BANDWIDTH} M: ---"
    echo "-----------------------------------"

    iperf3 -c "$SERVER_IP" \
      -u \
      -b "${BANDWIDTH}M" \
      -t 10 \
      -J \
      > "${FILE_NAME_PREFIX}${BANDWIDTH}M_run_${j}.json"

    echo "-----------------------------------"
    echo "---- Ended for ${BANDWIDTH} M: ----"
    echo "-----------------------------------"
    done

done

echo "----------------------------"
echo "---- Ending experiment: ----"
echo "----------------------------"
