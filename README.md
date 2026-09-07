# BehaviorSimilaritySearch

A computer vision system that detects whether specific behaviours are present in video segments.

**Vision**: Multi-modal stream from the edge → encoder → Valkey VSS → confidence score, to determine if a set of data contains known behaviours. Behaviour embeddings are pre-loaded to Valkey.

## Architecture

```
Edge device
├── bss-cli          CLI entry point
├── bss-encoder      ONNX Runtime inference (TensorRT / CUDA / CPU)
├── bss-data         Image loading
├── bss-valkey       Valkey client + vector similarity search
└── bss-core         Config loading, shared error types
```

Inference backend is abstracted behind an `Encoder` trait, enabling a future migration from embedded ONNX/TensorRT to a Triton Inference Server without changing application code.

## Prerequisites

- [Rust](https://rustup.rs/) stable (1.80+)
- [Docker](https://docs.docker.com/get-docker/) with Compose v2
- NVIDIA CUDA + TensorRT (optional, for GPU acceleration on Jetson/NVIDIA hardware)

## Installation

```bash
# Build all crates
make build

# Start Valkey
make up
```

## Usage

```bash
# Run the CLI
cargo run --bin bss-cli -- --help

# Bootstrap: initialize Valkey index, load images, encode, store vectors
cargo run --bin bss-cli -- bootstrap

# With custom paths
cargo run --bin bss-cli -- --env-config configs/local.env --data-path data/sample bootstrap
```

### CLI Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--env-config PATH` | Path to environment/connection config file | `configs/local.env` |
| `--data-path PATH` | Path to directory containing image data | `data/sample` |

### Subcommands

| Command | Description |
|---------|-------------|
| `bootstrap` | Initialize search backend, encode images, and store vectors |

## Model Setup

Models must be exported from PyTorch to ONNX before use. Example for YOLOv8:

```python
from ultralytics import YOLO
model = YOLO('yolov8n.pt')
model.export(format='onnx', dynamic=False, simplify=True)
# Copy the output to models/encoder.onnx
```

Place ONNX models in the `models/` directory. TensorRT engine files (`.engine`) are also supported.

## Development

| Command | Description |
|---------|-------------|
| `make build` | Compile all workspace crates |
| `make test` | Run the full test suite |
| `make lint` | Run clippy with warnings as errors |
| `make check-codestyle` | Check formatting without changes |
| `make format` | Auto-format all code |
| `make ci` | Run all checks (mirrors CI) |
| `make docs` | Build and open rustdoc |
| `make up` | Start Valkey via docker-compose |
| `make down` | Stop docker-compose services |
| `make clean` | Remove build artifacts |

## Configuration

Connection settings are loaded from a `.env` file. Defaults:

| Key | Default | Description |
|-----|---------|-------------|
| `VALKEY_HOST` | `127.0.0.1` | Valkey server hostname |
| `VALKEY_PORT` | `6379` | Valkey server port |
| `VALKEY_PING_MAX_RETRIES` | `5` | Ping retry attempts on startup |
| `VALKEY_PING_RETRY_DELAY` | `2` | Seconds between ping retries |

## Image Samples

Place `.jpg`, `.jpeg`, or `.png` files in `data/sample/` (flat directory, no subdirectory traversal).

## Deployment

For edge devices (Jetson, Raspberry Pi), build a release binary:

```bash
make release
# Binary at: target/release/bss-cli
```

The binary is self-contained. Copy it alongside `configs/` and `models/` to the target device.
