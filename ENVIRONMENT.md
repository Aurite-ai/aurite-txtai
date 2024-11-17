# txtai Service Environment Setup

## Overview

This project uses a combination of Conda and pip to manage dependencies. The setup is organized into several configuration files, each serving a specific purpose in our development workflow.

## Key Files

### 1. environment.yml

The main Conda environment configuration:

```yaml
name: txtai
channels:

- conda-forge
  - defaults
    dependencies:
  - python=3.11
  - pip
  - pip:
      - -r requirements.txt
      - -r requirements.dev.txt
```

This file creates our Conda environment and installs all required dependencies.

### 2. pyproject.toml

Defines core package dependencies:

```toml
[project]
dependencies = [
  "txtai[ann,pipeline]>=6.0.0",
  "fastapi>=0.109.0",
  "uvicorn>=0.27.0",
  "python-dotenv>=1.0.0",
  "pydantic>=2.0.0",
  "google-cloud-storage>=2.14.0"
]
```

These are the minimum requirements for the package to function.

### 3. requirements.txt

Production dependencies including:

```plaintext
- Core dependencies from pyproject.toml
- ML/AI libraries needed for txtai functionality
- Production server components
```

### 4. requirements.dev.txt

Development-only dependencies including:

```plaintext
- Testing tools (pytest)
- Code formatting (black)
- Jupyter notebook development tools
```

## Getting Started

1. Install Miniconda if not already installed:

   ```bash
   wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh

   bash Miniconda3-latest-Linux-x86_64.sh
   ```

2. Create the environment:

   ```bash
   conda env create -f environment.yml
   ```

3. Activate the environment:

   ```bash
   conda activate txtai
   ```

4. Install the package in development mode:

   ```bash
   pip install -e .
   ```

**Note:** Always activate the Conda environment before working on the project:

```bash
conda activate txtai
```

## Dependency Management

The dependency hierarchy works as follows:

- **pyproject.toml** - Core package requirements
- **requirements.txt** - Production environment
- **requirements.dev.txt** - Development tools
- **environment.yml** - Complete environment setup

## Common Tasks

### Update all dependencies

```bash
conda env update -f environment.yml
```

### Add a new production dependency

1. Add to requirements.txt

2. Run:

```bash
pip install -r requirements.txt
```

### Add a new development dependency

1. Add to requirements.dev.txt

2. Run:

```bash
pip install -r requirements.dev.txt
```
