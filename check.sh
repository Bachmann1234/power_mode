#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'
poetry run black --check power_mode tests
poetry run isort --check power_mode tests
poetry run pyflakes power_mode tests
poetry run mypy --config-file pyproject.toml power_mode tests
poetry run pytest tests