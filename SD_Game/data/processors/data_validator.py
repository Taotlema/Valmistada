# data_validator: Validates GTFS and modifier directories for required files.

import os
from typing import Tuple, List


# DataValidator: Stateless helper that checks directory contents before loading.
class DataValidator:

    REQUIRED_FILES    = ["routes.txt", "stops.txt", "trips.txt", "stop_times.txt"]
    RECOMMENDED_FILES = ["calendar.txt", "shapes.txt", "agency.txt"]

    # validate_gtfs_dir: Return (is_valid, list_of_missing_required_files).
    @staticmethod
    def validate_gtfs_dir(directory: str) -> Tuple[bool, List[str]]:
        missing = [
            f for f in DataValidator.REQUIRED_FILES
            if not os.path.exists(os.path.join(directory, f))
        ]
        return (len(missing) == 0, missing)

    # validate_modifier_dir: True if at least one Ridership CSV is present.
    @staticmethod
    def validate_modifier_dir(directory: str) -> bool:
        if not os.path.isdir(directory):
            return False
        return any(
            "Ridership" in f and f.endswith(".csv")
            for f in os.listdir(directory)
        )
