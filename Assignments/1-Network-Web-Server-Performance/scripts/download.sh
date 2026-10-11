#!/bin/bash
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive

echo "Updating package lists"
sudo apt-get update

echo "Installing dependencies"
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
    iputils-ping \
    iperf3 \
    nginx \
    curl \
    git \
    openssh-server \
    vim \
    wget \
    ca-certificates\
    sysstat

echo "Installing Vegeta"

VERSION="12.12.0"
ARCHIVE="vegeta_${VERSION}_linux_amd64.tar.gz"
URL="https://github.com/tsenart/vegeta/releases/download/v${VERSION}/${ARCHIVE}"

TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

wget -q --show-progress -O "$TMP_DIR/$ARCHIVE" "$URL"

tar -xzf "$TMP_DIR/$ARCHIVE" -C "$TMP_DIR" vegeta

mkdir -p "$HOME/bin"
install -m 755 "$TMP_DIR/vegeta" "$HOME/bin/vegeta"

export PATH="$HOME/bin:$PATH"

if ! grep -Fqx 'export PATH="$HOME/bin:$PATH"' "$HOME/.bashrc"; then
    echo 'export PATH="$HOME/bin:$PATH"' >> "$HOME/.bashrc"
fi

echo "Verifying installation"

iperf3 --version | head -n 1
nginx -v
vegeta -version

echo "Installation completed."

