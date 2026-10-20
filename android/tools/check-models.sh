#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
studycard_test_dir=$(mktemp -d)
trap 'rm -rf "$studycard_test_dir"' EXIT
studycard_java_bin=${JAVA_HOME:+$JAVA_HOME/bin/}
"${studycard_java_bin}javac" --release 8 -d "$studycard_test_dir" \
  app/src/main/java/com/studycard/app/GameEngine.java \
  app/src/main/java/com/studycard/app/TableSpeechPlan.java tools/ModelTests.java
"${studycard_java_bin}java" -cp "$studycard_test_dir" com.studycard.app.ModelTests
