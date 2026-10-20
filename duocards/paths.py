"""Keep each checkout's data, preferences and desktop session together."""

import hashlib
import os
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
PROFILE_DIR = Path(
    os.environ.get("STUDYCARD_HOME") or PROJECT_DIR / ".studycard"
).expanduser().resolve()
DATA_DIR = PROFILE_DIR / "data"
CONFIG_DIR = PROFILE_DIR / "config"
CACHE_DIR = PROFILE_DIR / "cache"

# Separate profiles must not send window commands to one another.
_profile_id = hashlib.sha256(os.fsencode(PROFILE_DIR)).hexdigest()[:16]
APP_ID = f"studycard-{_profile_id}"
IPC_SOCKET_NAME = f"{APP_ID}-ipc"
