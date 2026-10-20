#!/usr/bin/env bash
set -euo pipefail

STUDYCARD_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
STUDYCARD_TEST_DIR="$(mktemp -d)"
trap 'rm -rf -- "$STUDYCARD_TEST_DIR"' EXIT

export STUDYCARD_HOME="$STUDYCARD_TEST_DIR/profile"
export XDG_CONFIG_HOME="$STUDYCARD_TEST_DIR/config"
export XDG_DATA_HOME="$STUDYCARD_TEST_DIR/data"
export XDG_CACHE_HOME="$STUDYCARD_TEST_DIR/cache"
export QT_QPA_PLATFORM=offscreen
export PYTHONDONTWRITEBYTECODE=1

STUDYCARD_PYTHON=python3
if [[ -x "$STUDYCARD_DIR/.venv/bin/python" ]]; then
    STUDYCARD_PYTHON="$STUDYCARD_DIR/.venv/bin/python"
fi

cd -- "$STUDYCARD_DIR"
"$STUDYCARD_PYTHON" -m unittest discover -s tests -v "$@"
