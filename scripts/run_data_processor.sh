#!/bin/bash

# Navigate to your project directory
cd /home/ryan_aurite_ai/data_ops

# Activate your virtual environment
source venv/bin/activate

# Run the Python script
python data_processor.py --post_count 100

# Deactivate the virtual environment
deactivate
