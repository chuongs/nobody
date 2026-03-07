#!/bin/bash
set -euo pipefail

# Reduce pip disk usage/noise in constrained CI builders.
export PIP_NO_CACHE_DIR=1
export PIP_DISABLE_PIP_VERSION_CHECK=1

python -m pip install --upgrade pip

# Ensure CPU-only PyTorch is used so GPU/CUDA wheels are not downloaded.
pip install --index-url https://download.pytorch.org/whl/cpu torch torchvision

# Install app dependencies.
pip install -r requirements.txt

# Keep dlib dependency resolution controlled by requirements.
pip install face-recognition --no-deps
