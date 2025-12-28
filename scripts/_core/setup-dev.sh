#!/bin/bash
# ⚠️ STARTERPACK CORE — DO NOT MODIFY. This file is managed by the starterpack.

ROOT_GIT=$(git rev-parse --show-toplevel)

# Install frontend dependencies
npm install --prefix=$ROOT_GIT/app/frontend

# Install backend dependencies
python3 -m venv $ROOT_GIT/venv
source $ROOT_GIT/venv/bin/activate
pip install -r $ROOT_GIT/app/backend/requirements.txt
source $ROOT_GIT/venv/bin/activate
