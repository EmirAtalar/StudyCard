# Study Card

A vocabulary flashcard app for Linux and macOS, written in Python with PyQt6.
There is also a Java [Android app](android/README.md).

Create decks, review cards with spaced repetition, and practise by typing,
listening or matching words. You can make your own tables and games too.
Pronunciation, example sentences, study stats, a focus timer and a desktop
widget are included.

Cards and study history stay on your device. No account is needed.
The interface supports English, Turkish, German and Spanish.

## Install

Download or clone the repository and open a terminal in its folder.
Use Python 3.12 or newer. Install the packages for your system, then follow
the shared steps below.

### Arch Linux

```bash
sudo pacman -Syu --needed python python-pip mpv xcb-util-cursor libxkbcommon-x11
python -m venv .venv
```

### Fedora

```bash
sudo dnf install python3 python3-pip mpv xcb-util-cursor libxkbcommon-x11 mesa-libEGL
python3 -m venv .venv
```

### Ubuntu 24.04 or newer

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip mpv libegl1 libgl1 libxcb-cursor0 libxkbcommon-x11-0
python3 -m venv .venv
```

### macOS

Install [Homebrew](https://brew.sh/) first, following its
[system requirements](https://docs.brew.sh/Installation#macos-requirements). Then:

```bash
brew install python@3.13 mpv
"$(brew --prefix python@3.13)/bin/python3.13" -m venv .venv
```

Use macOS 14.4 or newer for the current
[Qt release](https://doc.qt.io/qt-6/macos.html#supported-configurations).

### Finish setup

These steps are the same on all four systems:

```bash
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
bash run.sh
```

After that, use `bash run.sh` to open the app. Online lookups and speech
services need an internet connection. Sound effects use the system audio
backend through Qt; pronunciation uses `mpv` or `ffplay`.

The app shortcut works while the window has focus on macOS. Linux global
shortcuts depend on the desktop environment; KDE registers a system shortcut.
Autostart uses a LaunchAgent on macOS and the desktop's autostart folder on Linux.
Background mode needs a system tray. Without one, closing the window exits the app.

## Saved data

The app stores its SQLite database, settings and audio cache in `.studycard/`
inside the project folder. This directory is ignored by Git. A new copy starts
with a few sample cards and no study history.

To keep your data somewhere else:

```bash
STUDYCARD_HOME="/path/to/your/profile" bash run.sh
```

Use the device backup option in Settings to save or restore a `.studycard`
backup. Restoring replaces the current library. CSV and JSON imports add cards
to it instead.

## Android

Open `android/` in Android Studio. See the [Android README](android/README.md)
for SDK requirements, build instructions and backup transfer between devices.

## Tests

```bash
bash scripts/test.sh
```

Tests use a temporary profile. With a JDK installed, they also check the Android
game logic and table speech order. Building the Android app requires the SDK.
The GitHub Actions workflow includes Ubuntu and macOS runners, plus Arch and
Fedora containers.
