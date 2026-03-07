#!/bin/bash
set -euo pipefail

# Reduce pip disk usage/noise in constrained CI builders.
export PIP_NO_CACHE_DIR=1
export PIP_DISABLE_PIP_VERSION_CHECK=1

python -m pip install --upgrade pip

# Install app dependencies (includes CPU-only torch pins from requirements.txt).
pip install --no-cache-dir -r requirements.txt

# Keep dlib dependency resolution controlled by requirements.
pip install --no-cache-dir face-recognition --no-deps
