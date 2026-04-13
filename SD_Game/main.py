# main: Entry point — boots Qt, loads YAML config, hands off to AppController.

import sys
import os
import yaml
import logging

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

from app_controller.app import AppController

# _setup_logging: Configure file and stdout handlers for the session.
def _setup_logging(log_path: str):
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(name)s - %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


# _load_settings: Parse settings.yaml and return the dict.
def _load_settings(path: str) -> dict:
    if not os.path.exists(path):
        raise FileNotFoundError(f"settings.yaml not found at '{path}'.")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# main: Bootstrap the application.
def main():
    # Run from the repo root so all relative data paths resolve correctly
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(os.path.dirname(project_root))

    settings_path = os.path.join(project_root, "config", "settings.yaml")
    settings = _load_settings(settings_path)

    _setup_logging(settings["paths"]["logs"])
    log = logging.getLogger(__name__)
    log.info(f"Starting {settings['app']['title']} v{settings['app']['version']}")

    app = QApplication(sys.argv)
    app.setApplicationName(settings["app"]["title"])
    app.setApplicationVersion(settings["app"]["version"])

    icon_path = os.path.join(project_root, "assets", "icons", "app_icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # Override the Qt default font with Courier New globally
    app.setStyleSheet("* { font-family: 'Courier New', monospace; }")

    window = AppController(settings)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
