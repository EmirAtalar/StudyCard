"""
DuoCards Desktop - Özel Başlık Çubuğu (Custom Title Bar)
Uygulamaya özel çerçeve, pencere sürükleme, boyutlandırma ve pencere kontrol butonları.
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QSizePolicy
)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QIcon, QCursor
from duocards.ui_localization import ui_text, localize_tree , QLabel, QPushButton


class CustomTitleBar(QWidget):
    def __init__(self, parent_window):
        super().__init__(parent_window)
        self.parent_window = parent_window
        self.setObjectName("customTitleBar")
        self.setFixedHeight(38)
        self._drag_pos = None

        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 8, 0)
        layout.setSpacing(10)

        # Sol: İkon ve Başlık
        icon_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "assets", "icon.png"
        )
        from duocards.icons import get_icon
        self.lbl_icon = QLabel()
        if os.path.exists(icon_path):
            self.lbl_icon.setPixmap(QIcon(icon_path).pixmap(20, 20))
        else:
            self.lbl_icon.setPixmap(get_icon("study", 18).pixmap(18, 18))
        self.lbl_icon.setStyleSheet("background: transparent;")
        layout.addWidget(self.lbl_icon)

        self.lbl_title = QLabel(ui_text('Study Card', None))
        self.lbl_title.setStyleSheet("""
            color: #94a3b8;
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.3px;
            background: transparent;
        """)
        layout.addWidget(self.lbl_title)

        # Orta: Sürükleme alanı
        layout.addStretch(1)

        # Sağ: Pencere kontrol butonları (Simge durumu, Ekranı Kapla, Kapat)
        btn_style = """
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 6px;
                color: #94a3b8;
                font-size: 13px;
                font-weight: bold;
                width: 32px;
                height: 26px;
            }
            QPushButton:hover {
                background-color: #334155;
                color: #ffffff;
            }
        """

        self.btn_min = QPushButton("-")
        self.btn_min.setStyleSheet(btn_style)
        self.btn_min.setToolTip(ui_text('Minimize', None))
        self.btn_min.clicked.connect(self.parent_window.showMinimized)

        self.btn_max = QPushButton("□")
        self.btn_max.setStyleSheet(btn_style)
        self.btn_max.setToolTip(ui_text('Maximize / Restore', None))
        self.btn_max.clicked.connect(self._toggle_maximize)

        self.btn_close = QPushButton("X")
        self.btn_close.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 6px;
                color: #94a3b8;
                font-size: 13px;
                font-weight: bold;
                width: 34px;
                height: 26px;
            }
            QPushButton:hover {
                background-color: #ef4444;
                color: #ffffff;
            }
        """)
        self.btn_close.setToolTip(ui_text('Close', None))
        self.btn_close.clicked.connect(self.parent_window.close)

        layout.addWidget(self.btn_min)
        layout.addWidget(self.btn_max)
        layout.addWidget(self.btn_close)

    def _toggle_maximize(self):
        if self.parent_window.isMaximized():
            self.parent_window.showNormal()
            self.btn_max.setText("□")
        else:
            self.parent_window.showMaximized()
            self.btn_max.setText("[ ]")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            handle = self.parent_window.windowHandle()
            if not (handle and handle.startSystemMove()):
                self._drag_pos = event.globalPosition().toPoint() - self.parent_window.frameGeometry().topLeft()
            event.accept()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() == Qt.MouseButton.LeftButton:
            self.parent_window.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._toggle_maximize()
            event.accept()
        super().mouseDoubleClickEvent(event)
