# Development

## Table of Contents

- [Project Structure](#project-structure)
- [Environment Setup](#environment-setup-and-build)
- [Running Checks](#running-checks)
- [Running CI Locally](#running-ci-locally)
- [Documentation](#documentation)
- [Cleaning](#cleaning)
- [Windows](#windows-note)

## Project Structure

This project is a multi-package monorepo managed with [uv workspaces](https://docs.astral.sh/uv/concepts/workspaces/).

Each package under `packages/` and `apps/` has its own `pyproject.toml` and can be installed and run independently on separate devices or instances.

```
├── packages/          # Installable library packages
│   └── ...
├── apps/              # Runnable applications
│   └── ...
├── tests/
│   ├── unit/          # Per-package unit tests
│   └── integration/   # Cross-package integration tests
├── docs/              # Sphinx documentation
├── environment.yaml   # Micromamba environment (Python + system deps)
└── pyproject.toml     # Workspace root (uv config, dev tools, lint/mypy)
```

## Environment Setup and Build

Create and activate the environment:

```bash
micromamba create -f environment.yaml
micromamba activate behavior-similarity-search
```

Then install the project:

```bash
make build
```

To deactivate:

```bash
micromamba deactivate
```

## Running Checks

| Command                | Description                                      |
|------------------------|--------------------------------------------------|
| `make build`           | Install all workspace packages and dev dependencies |
| `make lint`            | Check for code quality issues with ruff          |
| `make check-codestyle` | Check formatting without making changes          |
| `make type-check`      | Run static type checking with mypy               |
| `make test`            | Run the test suite with pytest                   |
| `make docs`            | Build HTML documentation                         |
| `make format`          | Auto-fix lint and formatting issues (local only) |
| `make ci`              | Run all checks in sequence (mirrors CI)          |

## Cleaning

| Command            | Description                                    |
|--------------------|------------------------------------------------|
| `make clean`       | Remove all build, pyc, and test artifacts      |
| `make clean-build` | Remove build artifacts                         |
| `make clean-pyc`   | Remove compiled Python files and `__pycache__` |
| `make clean-test`  | Remove test and coverage artifacts             |
| `make clean-docs`  | Remove generated documentation                 |

## Running CI Locally

[`act`](https://github.com/nektos/act) runs GitHub Actions workflows locally using Docker. It is installed as part of the micromamba environment.

**Note:** Docker must be installed and running.

```bash
act
```

To run a specific workflow or job:

```bash
act -W .github/workflows/pre-merge.yaml
act -j build
```

If you hit missing dependencies in the default runner image, use the full image:

```bash
act -P ubuntu-latest=catthehacker/ubuntu:full-latest
```

## Documentation

Docs are built with [Sphinx](https://www.sphinx-doc.org/) using Google-style docstrings and the [Furo](https://pradyunsg.me/furo/) theme.

Build the HTML docs:

```bash
make docs
```

Output is written to `docs/_build/html/`. Open `docs/_build/html/index.html` in a browser to view.

To remove generated docs:

```bash
make clean-docs
```


## Windows Note

**Note:** This project uses `make` and bash tooling which are not natively available on Windows. The recommended approach is to use [WSL2](https://learn.microsoft.com/en-us/windows/wsl/install) (Windows Subsystem for Linux), which provides a full Linux environment.

Install WSL2 with Ubuntu from PowerShell:

```powershell
wsl --install
```

Then follow the rest of the setup instructions inside the WSL2 terminal.