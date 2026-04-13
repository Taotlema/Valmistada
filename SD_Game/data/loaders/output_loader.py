# output_loader: Scans the output/trials folder and returns metadata for each saved trial.

import os
import logging

log = logging.getLogger(__name__)


# TrialMeta: Lightweight descriptor for one saved trial folder.
class TrialMeta:

    def __init__(self, trial_number: int, trial_dir: str):
        self.trial_number = trial_number
        self.trial_dir    = trial_dir
        self.files: list  = []
        self._scan()

    # _scan: Populate the files list from disk.
    def _scan(self):
        if os.path.isdir(self.trial_dir):
            self.files = sorted(
                f for f in os.listdir(self.trial_dir)
                if os.path.isfile(os.path.join(self.trial_dir, f))
            )


# OutputLoader: Scans the trials directory and returns sorted TrialMeta objects.
class OutputLoader:

    def __init__(self, output_root: str):
        self.output_root = output_root

    # scan_trials: Return TrialMeta list sorted ascending by trial number.
    def scan_trials(self) -> list:
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
        log.info(f"Found {len(trials)} trial(s).")
        return trials
