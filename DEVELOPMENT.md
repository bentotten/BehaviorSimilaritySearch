# Development

## Table of Contents

- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Running Checks](#running-checks)
- [Running Tests](#running-tests)
- [Documentation](#documentation)
- [Infrastructure](#infrastructure)
- [Model Setup](#model-setup)

## Project Structure

```
├── crates/
│   ├── bss-core/                   # Config loading, shared error types
│   ├── bss-data/                   # Image loading
│   ├── bss-encoder/                # Encoder trait + ONNX Runtime implementation
│   ├── bss-valkey/                 # Valkey client + vector similarity search
│   ├── bss-cli/                    # CLI binary
│   └── bss-integration-tests/      # Workspace-level integration tests
├── configs/                        # Environment/connection config files
├── data/                           # Sample images for development
├── models/                         # ML Models
├── .github/workflows/              
├── Cargo.toml                      
├── docker-compose.yaml             # Local Valkey infrastructure
└── Makefile                        
```

## Prerequisites

- [Rust](https://rustup.rs/) stable (1.80+)
- [cargo-nextest](https://nexte.st/)
- [Docker](https://docs.docker.com/get-docker/) with Compose v2
- NVIDIA CUDA + TensorRT (optional — required for GPU acceleration)

Install Rust via rustup:

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

Install cargo-nextest:

```bash
cargo install cargo-nextest --locked
```

## Environment Setup

Build all workspace crates:

```bash
make build
```

Start local infrastructure (Valkey):

```bash
make up
```

To stop infrastructure:

```bash
make down
```

## Running Checks

| Command | Description |
|---------|-------------|
| `make type-check` | Fast type checking without producing binaries (`cargo check`) |
| `make lint` | Clippy static analysis, warnings treated as errors |
| `make check-codestyle` | Verify formatting without making changes |
| `make format` | Auto-format all code |
| `make ci` | Run all checks in sequence — mirrors CI (`type-check`, `lint`, `check-codestyle`, `test`) |

## Running Tests

```bash
# Run all tests
make test

# Run tests for a specific crate
cargo nextest run --package bss-core
```


## Documentation

Build and open rustdoc in a browser:

```bash
make docs
```

Doc comments follow standard Rust conventions (`///` for public items, `//!` for module-level docs).

## Infrastructure

```bash
make up    # Start Valkey via docker compose file
make down  # Stop Valkey
```

Default connection settings (see `configs/local.env`):

## Model Setup

ONNX models must be exported from PyTorch before use. Example for YOLOv8:

```python
from ultralytics import YOLO
model = YOLO('yolov8n.pt')
model.export(format='onnx', dynamic=False, simplify=True)
```

Copy the exported `.onnx` file to `models/encoder.onnx`. TensorRT engine files (`.engine`) are also supported and will be preferred on NVIDIA hardware.

Models are gitignored — they must be exported and placed locally before running `bootstrap`.
