# Default recipe (lists available commands)
default:
    @just --list

# Check conda installation and setup Python environment
check-python:
    #!/usr/bin/env bash
    if ! command -v conda &> /dev/null; then
        echo "Conda not found. Please install Miniconda first:"
        echo "wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh"
        echo "bash Miniconda3-latest-Linux-x86_64.sh"
        exit 1
    fi
    if ! conda env list | grep -q txtai; then
        echo "Creating conda environment 'txtai' with Python 3.11..."
        conda env create --file=environment.yml
    fi

# Setup development environment
setup: check-python
    #!/usr/bin/env bash
    sudo apt-get install libomp-dev
    # Create symlink if it doesn't exist
    sudo ln -sf /usr/lib/x86_64-linux-gnu/libgomp.so.1 /home/wilcoxr/miniconda3/envs/txtai/lib/libgomp.so.1
    # Set environment variables for OpenMP
    export CC=$(which gcc)
    export CXX=$(which g++)
    export CFLAGS="-fopenmp"
    export CXXFLAGS="-fopenmp"
    echo "Please run: conda activate txtai"
    echo "Then run: just install"

# Install dependencies in development mode
install:
    CFLAGS="-fopenmp" CXXFLAGS="-fopenmp" pip install -e .
    pip install -r requirements.dev.txt

# Update conda environment
update:
    conda env update --file=environment.yml

# Run tests
test:
    pytest -v

test-embeddings:
    pytest -v test/embeddings/

# Start API server
serve:
    python scripts/start_api.py

# Run API server in development mode
dev:
    # Kill any existing process on port 8000
    -lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Check GCP authentication
check-auth:
    python scripts/check_gcp_auth.py

# Initialize test data
init-data:
    python scripts/init_search.py


# Clean up Python cache files
clean:
    find . -type d -name "__pycache__" -exec rm -r {} +
    find . -type f -name "*.pyc" -delete
    find . -type f -name "*.pyo" -delete
    find . -type f -name "*.pyd" -delete
    find . -type d -name "*.egg-info" -exec rm -r {} +
    find . -type d -name "*.egg" -exec rm -r {} +
    find . -type d -name ".pytest_cache" -exec rm -r {} +
    find . -type d -name ".coverage" -exec rm -r {} +
    find . -type f -name ".coverage" -delete