# file_manager: Stateless filesystem helpers used across the application.

import os
import shutil
import logging

log = logging.getLogger(__name__)


# FileManager: Static helpers for directory management and trial numbering.
class FileManager:

    # ensure_dir: Create a directory (and parents) if it does not already exist.
    @staticmethod
    def ensure_dir(path: str):
        os.makedirs(path, exist_ok=True)

    # copy_into: Copy a file into a destination folder and return the new path.
    @staticmethod
    def copy_into(src: str, dest_dir: str) -> str:
        FileManager.ensure_dir(dest_dir)
        dest = os.path.join(dest_dir, os.path.basename(src))
        shutil.copy2(src, dest)
        return dest

    # list_dirs: Return sorted subdirectory names inside a parent folder.
    @staticmethod
    def list_dirs(parent: str) -> list:
        if not os.path.isdir(parent):
            return []
        return sorted(
            d for d in os.listdir(parent)
            if os.path.isdir(os.path.join(parent, d))
        )

    # next_trial_number: Scan the output folder and return the next unused trial integer.
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
