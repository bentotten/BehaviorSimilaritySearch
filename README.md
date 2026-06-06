# BehaviorSimilaritySearch
A computer vision project to detect if specific behaviours are present in video segments.

## Table of Contents

- [Prerequisites](#prerequisites)
    - [Note for Windows users](#note-for-windows-users)
    - [micromamba](#micromamba)
    - [Docker](#docker)
- [Installation](#installation)
- [Deploying Packages Independently](#deploying-packages-independently)

## Prerequisites


### Note for Windows users

This project uses `make` and bash tooling which are not natively available on Windows. The recommended approach is to use [WSL2](https://learn.microsoft.com/en-us/windows/wsl/install) (Windows Subsystem for Linux), which provides a full Linux environment.

Install WSL2 with Ubuntu from PowerShell:

```powershell
wsl --install
```

Then follow the standard Linux setup instructions inside the WSL2 terminal.

### micromamba

This project uses [micromamba](https://mamba.readthedocs.io/en/latest/installation/micromamba-installation.html) to manage the environment.

**Linux, macOS, or Git Bash on Windows:**

```bash
"${SHELL}" <(curl -L micro.mamba.pm/install.sh)
```

**macOS (Homebrew):**

```bash
brew install micromamba
```

**Windows (PowerShell):**

```powershell
Invoke-Expression ((Invoke-WebRequest -Uri https://micro.mamba.pm/install.ps1 -UseBasicParsing).Content)
```

Once installed, micromamba can be updated at any time with:

```bash
micromamba self-update
```

### Docker

This project uses Docker and the Compose v2 plugin to run local infrastructure.

**Linux:**

```bash
sudo apt install docker.io docker-compose-v2
```

**macOS (Homebrew):**

```bash
brew install --cask docker
```

**Windows:**

Install [Docker Desktop](https://www.docker.com/products/docker-desktop/), which includes Compose v2.

## Installation

Create and activate the environment:

```bash
micromamba create -f environment.yaml
micromamba activate behavior-similarity-search
```

Then install the project:

```bash
make build
```

Spin up infrastructure:

```bash
make up
```

To run:

```bash
bss
```

To clean up local infrastructure:

```bash
make down
```

To deactivate:

```bash
micromamba deactivate
```

## Deploying Packages Independently

Each sub-package has its own `pyproject.toml` and can be installed on its own, without pulling in the entire repository. This allows different parts of the project to run on different devices or instances with only the dependencies they need.

Examples: 

```bash
# Commandline interface
uv pip install -e "apps/bss_cli"

# Core library only (e.g. on an edge device)
uv pip install -e "packages/bss_core"
```
