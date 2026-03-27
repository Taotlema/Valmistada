"""
Filename: data_validator.py
Author: Ayemhenre Isikhuemhen
Description:
Last Updated: March, 2026
"""

# Libraries
import os
from typing import Tuple, List


# DataValidator: Checks completeness of an uploaded or default GTFS folder
class DataValidator:

    REQUIRED_FILES = ["routes.txt", "stops.txt", "trips.txt", "stop_times.txt"]
    RECOMMENDED_FILES = ["calendar.txt", "shapes.txt", "agency.txt"]

    # validate_gtfs_dir (directory): Return (is_valid, list_of_missing_required)
    @staticmethod
    def validate_gtfs_dir(directory: str) -> Tuple[bool, List[str]]:
        missing = []
        for fname in DataValidator.REQUIRED_FILES:
            if not os.path.exists(os.path.join(directory, fname)):
                missing.append(fname)
        return (len(missing) == 0, missing)

    # validate_modifier_dir (directory): Return True if ridership CSV is present
    @staticmethod
    def validate_modifier_dir(directory: str) -> bool:
        if not os.path.isdir(directory):
            return False
        for fname in os.listdir(directory):
            if "Ridership" in fname and fname.endswith(".csv"):
                return True
        return False