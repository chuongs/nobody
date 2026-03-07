#!/bin/bash
set -euo pipefail

python -m pip install --upgrade pip
pip install --no-cache-dir -r requirements.txt
# Install without pulling extra deps so dlib wheel selection stays controlled by requirements.
pip install --no-cache-dir face-recognition --no-deps
