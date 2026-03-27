"""
==============================================
==               Valmistada v.1.0           ==
==============================================
Filename: main.py
Author: Ayemhenre Isikhuemhen
Description: This is the main file for the application.
Last Updated: March, 2026
"""
# Libraries
import sys
import os
import yaml
import logging

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

# Modules
from app_controller.app import AppController


def _setup_logging(log_path: str):
    """Configure root logger to write to both file and stdout."""
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def _load_settings(path: str) -> dict:
    """Parse settings.yaml; raise clearly if it's missing."""
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"settings.yaml not found at '{path}'. "
            "Ensure you are launching from the project root."
        )
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    # Resolve project root so relative paths work regardless of CWD
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(os.path.dirname(project_root))   # move up to repo root

    settings_path = os.path.join(project_root, "config", "settings.yaml")
    settings      = _load_settings(settings_path)

    _setup_logging(settings["paths"]["logs"])
    log = logging.getLogger(__name__)
    log.info("=" * 60)
    log.info(f"  {settings['app']['title']}  v{settings['app']['version']}")
    log.info("=" * 60)

    app = QApplication(sys.argv)
    app.setApplicationName(settings["app"]["title"])
    app.setApplicationVersion(settings["app"]["version"])

    # Optional window icon
    icon_path = os.path.join(project_root, "assets", "icons", "app_icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # Global stylesheet — font and scrollbar defaults
    app.setStyleSheet("""
        * {
            font-family: 'Segoe UI', 'Arial', sans-serif;
        }
        QToolTip {
            background-color: #16213E;
            color: #E0E0E0;
            border: 1px solid #0F3460;
            padding: 4px;
            border-radius: 4px;
        }
    """)

    window = AppController(settings)
    window.show()

    log.info("Qt event loop started.")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()