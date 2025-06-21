# Development Guide

This document covers everything you need to know to set up and contribute to the Doggo project.

## Prerequisites

- **Python 3.11+**: Doggo requires Python 3.11 or higher
- **uv**: Modern Python package manager and project tool

## Environment Setup

### 1. Install uv

First, install `uv` if you haven't already:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Clone and Setup Project

```bash
# Clone the repository
git clone https://github.com/0nsh/doggo
cd doggo

# Create virtual environment and install dependencies
uv venv --python 3.11.10

# Install dependencies
uv sync --all-extras --all-groups

# Activate the virtual environment
source .venv/bin/activate  # On Unix/macOS
# or
.venv\Scripts\activate     # On Windows
```


## Testing Commands

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_cli.py
```

## Local Installation

To install Doggo locally for development:

```bash
# Install in editable mode (recommended for development)
uv pip install -e .
```

After installation, you can use the `doggo` command from anywhere:

```bash
# Test the CLI
doggo --help
doggo init
```

## Building and Distribution

```bash
# Build the package
uv run build

# Check the built package
uv run twine check dist/*

# Upload to PyPI (if you have access)
uv run twine upload dist/*
```
