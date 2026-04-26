#!/usr/bin/env python3
"""Audio Recorder/Editor — entry point."""

import signal
import sys
import os

signal.signal(signal.SIGINT, signal.SIG_DFL)

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Recorder")
    app.setStyle("Fusion")

    # Dark palette
    from PyQt6.QtGui import QPalette, QColor
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(13, 27, 42))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(190, 200, 210))
    palette.setColor(QPalette.ColorRole.Base, QColor(10, 21, 32))
    palette.setColor(QPalette.ColorRole.Text, QColor(190, 200, 210))
    palette.setColor(QPalette.ColorRole.Button, QColor(18, 35, 53))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(190, 200, 210))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 180, 160))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
