#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ -z "${JAVA_HOME:-}" && -d /usr/lib/jvm/java-17-openjdk ]]; then
  export JAVA_HOME=/usr/lib/jvm/java-17-openjdk
fi
studycard_java_bin=${JAVA_HOME:+$JAVA_HOME/bin/}
studycard_java_version=$("${studycard_java_bin}java" -version 2>&1)
if [[ "$studycard_java_version" != *'version "17.'* ]]; then
  echo 'JDK 17 gerekli. Android Studio içindeki Gradle JDK ayarını 17 yapın veya JAVA_HOME tanımlayın.' >&2
  exit 1
fi
if [[ ! -f local.properties && -z "${ANDROID_HOME:-}" && -z "${ANDROID_SDK_ROOT:-}" ]]; then
  echo 'Android SDK bulunamadı. Android Studio ile android klasörünü açıp SDK Platform 35 ve Build Tools 35.0.0 kurun.' >&2
  exit 1
fi
./gradlew assembleDebug
printf '\nAPK hazır: %s/app/build/outputs/apk/debug/app-debug.apk\n' "$PWD"
