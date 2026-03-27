"""
Filename: output_loader.py
Author: Ayemhenre Isikhuemhen
Description:
Last Updated: March, 2026
"""
"""
Filename: output_loader.py
Author: Ayemhenre Isikhuemhen
Description: Scans the output/trials folder and returns available trial metadata.
Last Updated: March, 2026
"""

# Libraries
import os
import logging

log = logging.getLogger(__name__)


# TrialMeta: Lightweight descriptor for a saved trial folder
class TrialMeta:
    def __init__(self, trial_number: int, trial_dir: str):
        self.trial_number = trial_number
        self.trial_dir = trial_dir
        self.files: list[str] = []
        self._scan()

    # _scan: Populate the list of files in this trial's folder
    def _scan(self):
        if os.path.isdir(self.trial_dir):
            self.files = sorted(f for f in os.listdir(self.trial_dir)
                                if os.path.isfile(os.path.join(self.trial_dir, f)))


# OutputLoader: Discovers all trial folders under the output root
class OutputLoader:

    # __init__ (output_root: path to output/trials/)
    def __init__(self, output_root: str):
        self.output_root = output_root

    # scan_trials: Return a list of TrialMeta objects sorted by trial number
    def scan_trials(self) -> list[TrialMeta]:
        if not os.path.isdir(self.output_root):
            return []
        trials = []
        for entry in sorted(os.listdir(self.output_root)):
            full = os.path.join(self.output_root, entry)
            if os.path.isdir(full) and entry.lower().startswith("trial_"):
                try:
                    num = int(entry.split("_")[1])
                    trials.append(TrialMeta(num, full))
                except (IndexError, ValueError):
                    continue
        log.info(f"Found {len(trials)} trial(s) in output folder.")
        return trials