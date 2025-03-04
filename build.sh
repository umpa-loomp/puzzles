#!/bin/bash
set -e

# Make scripts executable
chmod +x deploy/build_docker.sh
chmod +x deploy/run_docker.sh
chmod +x deploy/start.sh
chmod +x build.sh

# Change to script directory
cd "$(dirname "$0")"

# Run build script
./deploy/build_docker.sh