"""Render the rainbow jewel SVG to a PNG (used for the AppImage icon)."""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtGui import QGuiApplication, QImage, QPainter  # noqa: E402
from PySide6.QtSvg import QSvgRenderer  # noqa: E402


def main(source, target, size=256):
    app = QGuiApplication(sys.argv[:1])  # noqa: F841 - needed for painting
    image = QImage(size, size, QImage.Format_ARGB32)
    image.fill(Qt.transparent)
    painter = QPainter(image)
    QSvgRenderer(source).render(painter)
    painter.end()
    if not image.save(target):
        raise SystemExit(f"Could not write {target}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
