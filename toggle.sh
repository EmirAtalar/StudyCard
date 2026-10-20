#!/usr/bin/env bash
STUDYCARD_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec "$STUDYCARD_DIR/run.sh" "$@"
