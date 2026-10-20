#!/usr/bin/env python3
"""Launch Study Card or bring the current profile's window to the front."""

import sys
import os

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
from duocards.main_window import MainWindow
from duocards.paths import APP_ID, IPC_SOCKET_NAME


def main():
    # Wayland / X11 uyumluluğu
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

    if sys.platform.startswith("linux"):
        try:
            import ctypes
            libc = ctypes.CDLL(None)
            libc.prctl(15, b"studycard\0", 0, 0, 0)
        except (AttributeError, OSError):
            pass
    try:
        import setproctitle
        setproctitle.setproctitle("studycard")
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setApplicationName("Study Card")
    app.setApplicationDisplayName("Study Card")
    app.setOrganizationName("StudyCard")
    app.setDesktopFileName(APP_ID)

    # 1. Zaten çalışan Study Card penceresi var mı kontrol et
    socket = QLocalSocket()
    socket.connectToServer(IPC_SOCKET_NAME)
    if socket.waitForConnected(400):
        # Uygulama zaten açık! Öne getirmesi için komut gönder ve anında çık
        socket.write(b"TOGGLE\n")
        socket.flush()
        socket.waitForBytesWritten(300)
        socket.disconnectFromServer()
        sys.exit(0)

    # 2. İlk çalışan ana instance - IPC sunucusunu başlat
    server = QLocalServer()
    server.removeServer(IPC_SOCKET_NAME)
    server.listen(IPC_SOCKET_NAME)

    # İkon ayarla (varsa)
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = MainWindow()
    if os.path.exists(icon_path):
        window.setWindowIcon(QIcon(icon_path))

    def on_new_connection():
        client = server.nextPendingConnection()
        if client:
            try:
                client.waitForReadyRead(200)
                client.readAll()
                client.disconnectFromServer()
            except Exception:
                pass
            window._toggle_window_focus()

    server.newConnection.connect(on_new_connection)

    if "--minimized" in sys.argv:
        window.showMinimized()
    else:
        window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
