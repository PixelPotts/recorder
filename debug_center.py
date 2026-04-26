#!/usr/bin/env python3
"""Debug script to check window centering geometry."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

app = QApplication(sys.argv)

from ui.main_window import MainWindow
w = MainWindow()
w.show()

def dump():
    screen = w.screen()
    sg = screen.availableGeometry()
    fg = w.frameGeometry()
    g = w.geometry()
    print(f"Screen available: x={sg.x()} y={sg.y()} w={sg.width()} h={sg.height()}")
    print(f"Window geometry:  x={g.x()} y={g.y()} w={g.width()} h={g.height()}")
    print(f"Frame geometry:   x={fg.x()} y={fg.y()} w={fg.width()} h={fg.height()}")
    print(f"Window pos:       {w.pos().x()}, {w.pos().y()}")
    print(f"isMaximized={w.isMaximized()} isFullScreen={w.isFullScreen()}")

    # What centering should compute:
    cx = (sg.width() - w.width()) // 2 + sg.x()
    cy = (sg.height() - w.height()) // 2 + sg.y()
    print(f"Expected center:  x={cx} y={cy}")

    # Try forcing move now
    print(f"Forcing move to ({cx}, {cy})...")
    w.move(cx, cy)

    QTimer.singleShot(500, dump2)

def dump2():
    g = w.geometry()
    print(f"After force move: x={g.x()} y={g.y()} w={g.width()} h={g.height()}")
    print("Done. Close window to exit.")

QTimer.singleShot(200, dump)
app.exec()
