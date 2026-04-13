# modifier_loader: Reads modifier CSV files and exposes lookup methods for the simulation.

import os
import pandas as pd
import logging

log = logging.getLogger(__name__)


# ModifierLoader: Loads historical ridership, census, and land-use data for demand weighting.
class ModifierLoader:

    def __init__(self, modifier_dir: str):
        self.modifier_dir     = modifier_dir
        self.ridership_df:     pd.DataFrame = pd.DataFrame()
        # Default population keeps things reasonable if the census file is missing
        self.population_total: int          = 873_965
        self.land_use_counts:  dict         = {}
        self.commute_workers:  int          = 1_104_249

    # _path: Resolve a filename inside the modifier directory.
    def _path(self, filename: str) -> str:
        return os.path.join(self.modifier_dir, filename)

    # load: Parse all available modifier files; skip silently if any are missing.
    def load(self):
        if not os.path.isdir(self.modifier_dir):
            log.warning(f"Modifier directory not found: {self.modifier_dir}")
            return
        self._load_ridership()
        self._load_population()
        self._load_land_use()
        log.info("Modifier data loaded.")

    # _load_ridership: Build the per-route historical baseline DataFrame.
    def _load_ridership(self):
        for fname in os.listdir(self.modifier_dir):
            if "Ridership" in fname and fname.endswith(".csv"):
                df = pd.read_csv(self._path(fname), dtype=str, low_memory=False)
                df.columns = [c.strip() for c in df.columns]
                # Normalise the boarding column — remove commas and coerce
                df["Average Daily Boardings"] = pd.to_numeric(
                    df["Average Daily Boardings"]
                    .astype(str).str.replace(",", "").str.strip(),
                    errors="coerce",
                )
                df["Month"] = pd.to_datetime(df["Month"], format="%B %Y", errors="coerce")
                self.ridership_df = df.dropna(subset=["Average Daily Boardings", "Month"])
                log.info(f"Ridership loaded: {len(self.ridership_df):,} rows")
                return

    # _load_population: Extract total population from the Decennial Census file.
    def _load_population(self):
        for fname in os.listdir(self.modifier_dir):
            if "DECENNIAL" in fname and fname.endswith(".csv"):
                df = pd.read_csv(self._path(fname), dtype=str, low_memory=False)
                df.columns = [c.strip() for c in df.columns]
                df.rename(
                    columns={df.columns[0]: "label", df.columns[1]: "value"},
                    inplace=True,
                )
                df["value"] = pd.to_numeric(
                    df["value"].str.replace(",", "").str.strip(), errors="coerce"
                )
                total_row = df[df["label"].str.contains("Total", na=False)]
                if not total_row.empty:
                    self.population_total = int(total_row["value"].iloc[0])
                log.info(f"Population loaded: {self.population_total:,}")
                return

    # _load_land_use: Build a landuse-type to parcel-count dict for demand weighting.
    def _load_land_use(self):
        for fname in os.listdir(self.modifier_dir):
            if "Land_Use" in fname and fname.endswith(".csv"):
                df = pd.read_csv(
                    self._path(fname), dtype=str, low_memory=False,
                    usecols=lambda c: c != "the_geom",
                )
                if "landuse" in df.columns:
                    self.land_use_counts = df["landuse"].value_counts().to_dict()
                log.info(f"Land use loaded: {len(self.land_use_counts)} types")
                return

    # get_route_baseline: Median historical boardings for a route and day-type pair.
    def get_route_baseline(self, route_short_name: str, day_type: str) -> float:
        if self.ridership_df.empty:
            return 3_000.0
        mask = (
            (self.ridership_df["Route"].astype(str).str.strip()
             == str(route_short_name).strip())
            & (self.ridership_df["Service Day of the Week"].str.strip() == day_type)
        )
        subset = self.ridership_df[mask]["Average Daily Boardings"].dropna()
        return float(subset.median()) if not subset.empty else 3_000.0

    # density_factor: Population-based demand scalar relative to a 1M-person city.
    def density_factor(self) -> float:
        return min(self.population_total / 1_000_000, 2.0)
