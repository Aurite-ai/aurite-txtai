#!/bin/bash

# Source conda
. "/home/wilcoxr/miniconda3/etc/profile.d/conda.sh"

# Activate txtai environment
conda activate txtai

# Run tests with proper Python path
PYTHONPATH=${PYTHONPATH}:${PWD}/src pytest "$@"