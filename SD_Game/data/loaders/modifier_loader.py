"""
Filename: modifier_loader.py
Author: Ayemhenre Isikhuemhen
Description:
Last Updated: March, 2026
"""

# Libraries
import os
import pandas as pd
import logging

log = logging.getLogger(__name__)


# ModifierLoader: Reads the Modifier Data folder and builds lookup tables
class ModifierLoader:

    # __init__ (modifier_dir: path to San Francisco modifier folder)
    def __init__(self, modifier_dir: str):
        self.modifier_dir = modifier_dir
        self.ridership_df: pd.DataFrame = pd.DataFrame()
        self.population_total: int = 873_965     # 2020 Census SF default
        self.land_use_counts: dict = {}
        self.commute_workers: int = 1_104_249    # ACS 2024 default

    # _path (filename): Resolve a file within the modifier directory
    def _path(self, filename: str) -> str:
        return os.path.join(self.modifier_dir, filename)

    # load: Parse all available modifier files; silently skip missing ones
    def load(self):
        self._load_ridership()
        self._load_population()
        self._load_land_use()
        log.info("Modifier data loaded.")

    # _load_ridership: Reads the monthly ridership CSV for route-level baseline
    def _load_ridership(self):
        for fname in os.listdir(self.modifier_dir) if os.path.isdir(self.modifier_dir) else []:
            if "Ridership" in fname and fname.endswith(".csv"):
                fp = self._path(fname)
                df = pd.read_csv(fp, dtype=str, low_memory=False)
                df.columns = [c.strip() for c in df.columns]
                df["Average Daily Boardings"] = pd.to_numeric(
                    df["Average Daily Boardings"].astype(str).str.replace(",", "").str.strip(),
                    errors="coerce"
                )
                df["Month"] = pd.to_datetime(df["Month"], format="%B %Y", errors="coerce")
                self.ridership_df = df.dropna(subset=["Average Daily Boardings", "Month"])
                log.info(f"Ridership modifier loaded: {len(self.ridership_df):,} rows")
                return

    # _load_population: Parse Census population CSV for the total headcount
    def _load_population(self):
        for fname in os.listdir(self.modifier_dir) if os.path.isdir(self.modifier_dir) else []:
            if "DECENNIAL" in fname and fname.endswith(".csv"):
                fp = self._path(fname)
                df = pd.read_csv(fp, dtype=str, low_memory=False)
                df.columns = [c.strip() for c in df.columns]
                df.rename(columns={df.columns[0]: "label", df.columns[1]: "value"}, inplace=True)
                df["value"] = pd.to_numeric(df["value"].str.replace(",", "").str.strip(), errors="coerce")
                total_row = df[df["label"].str.contains("Total", na=False)]
                if not total_row.empty:
                    self.population_total = int(total_row["value"].iloc[0])
                log.info(f"Population modifier loaded: {self.population_total:,}")
                return

    # _load_land_use: Build a landuse-type → parcel-count lookup for density weighting
    def _load_land_use(self):
        for fname in os.listdir(self.modifier_dir) if os.path.isdir(self.modifier_dir) else []:
            if "Land_Use" in fname and fname.endswith(".csv"):
                fp = self._path(fname)
                df = pd.read_csv(fp, dtype=str, low_memory=False, usecols=lambda c: c != "the_geom")
                if "landuse" in df.columns:
                    self.land_use_counts = df["landuse"].value_counts().to_dict()
                log.info(f"Land use modifier loaded: {len(self.land_use_counts)} types")
                return

    # get_route_baseline (route_short_name, day_type): Median boardings for that route/day
    def get_route_baseline(self, route_short_name: str, day_type: str) -> float:
        if self.ridership_df.empty:
            return 3000.0
        mask = (
            (self.ridership_df["Route"].astype(str).str.strip() == str(route_short_name).strip()) &
            (self.ridership_df["Service Day of the Week"].str.strip() == day_type)
        )
        subset = self.ridership_df[mask]["Average Daily Boardings"].dropna()
        if subset.empty:
            return 3000.0
        return float(subset.median())

    # density_factor: Population-based multiplier relative to a 1M-person baseline city
    def density_factor(self) -> float:
        return min(self.population_total / 1_000_000, 2.0)