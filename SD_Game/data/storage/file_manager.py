"""
Filename: file_manager.py
Author: Ayemhenre Isikhuemhen
Description: General file-system helpers — copy, move, ensure directories exist.
Last Updated: March, 2026
"""

# Libraries
import os
import shutil
import logging

log = logging.getLogger(__name__)


# FileManager: Stateless utility class for common filesystem operations
class FileManager:

    # ensure_dir (path): Create directory (and parents) if absent
    @staticmethod
    def ensure_dir(path: str):
        os.makedirs(path, exist_ok=True)

    # copy_into (src, dest_dir): Copy a file into a destination folder
    @staticmethod
    def copy_into(src: str, dest_dir: str) -> str:
        FileManager.ensure_dir(dest_dir)
        dest = os.path.join(dest_dir, os.path.basename(src))
        shutil.copy2(src, dest)
        log.debug(f"Copied {src} → {dest}")
        return dest

    # list_dirs (parent): Return subdirectory names inside a folder
    @staticmethod
    def list_dirs(parent: str) -> list:
        if not os.path.isdir(parent):
            return []
        return sorted(d for d in os.listdir(parent)
                      if os.path.isdir(os.path.join(parent, d)))

    # next_trial_number (output_root): Return the next unused trial integer
    @staticmethod
    def next_trial_number(output_root: str) -> int:
        if not os.path.isdir(output_root):
            return 1
        existing = []
        for name in os.listdir(output_root):
            if name.lower().startswith("trial_"):
                try:
                    existing.append(int(name.split("_")[1]))
                except (IndexError, ValueError):
                    continue
        return max(existing, default=0) + 1