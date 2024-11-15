#!/bin/bash
set -e  # Exit on error

echo "Setting up Python virtual environment..."

# Remove existing venv if it exists
if [ -d ".venv" ]; then
    echo "Removing existing virtual environment..."
    rm -rf .venv
fi

# Create new virtual environment
echo "Creating new virtual environment..."
python3 -m venv .venv

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
python3 -m pip install --upgrade pip

# Install build tools
echo "Installing build tools..."
pip install pip-tools build hatchling

# Generate requirements.txt
echo "Generating requirements.txt..."
pip-compile --upgrade requirements.in

# Install dependencies
echo "Installing dependencies..."
pip install -e .
pip install -r requirements.txt

# Install pre-commit hooks
echo "Installing pre-commit hooks..."
pre-commit install

echo "Installing just using cargo (Rust's package manager)..."
# First install cargo if you don't have it
sudo apt update
sudo apt install cargo

# Then install just
cargo install just

# Add cargo binaries to your PATH (add this to your ~/.bashrc)
echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

echo "Just installed! Run 'just db-init' to initialize the database."
echo "Setup complete!"
