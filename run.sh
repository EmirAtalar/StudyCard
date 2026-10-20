#!/usr/bin/env bash
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do
  DIR="$(cd -P "$(dirname "$SOURCE")" && pwd)"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
DIR="$(cd -P "$(dirname "$SOURCE")" && pwd)"
export PYTHONPATH="$DIR${PYTHONPATH:+:$PYTHONPATH}"
STUDYCARD_PYTHON=python3
if [ -x "$DIR/.venv/bin/python" ]; then
  STUDYCARD_PYTHON="$DIR/.venv/bin/python"
fi
exec "$STUDYCARD_PYTHON" "$DIR/main.py" "$@"
