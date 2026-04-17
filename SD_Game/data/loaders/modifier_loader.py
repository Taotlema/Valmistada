# modifier_loader: Reads modifier CSV files and exposes lookup methods for the simulation.
# Updated: year-segmented ridership (sim_year only), ACS commute_df, LODES commute_workers.

import os
import pandas as pd
import logging

log = logging.getLogger(__name__)


# ModifierLoader: Loads historical ridership, census, and land-use data for demand weighting.
class ModifierLoader:

    def __init__(self, modifier_dir: str, sim_year: int = 2019):
        self.modifier_dir     = modifier_dir
        self.sim_year         = sim_year          # year used to segment ridership data

        self.ridership_df:     pd.DataFrame = pd.DataFrame()
        self.ridership_full_df: pd.DataFrame = pd.DataFrame()  # unfiltered, for diagnostics

        # Default population keeps things reasonable if the census file is missing
        self.population_total: int          = 873_965
        self.land_use_counts:  dict         = {}
        self.commute_workers:  int          = 500_000   # LODES total jobs used by RB2

        # ACS commute departure table — consumed by RB2 _build_acs_hour_weights
        self.commute_df: pd.DataFrame = pd.DataFrame()

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
        self._load_commute_times()
        self._load_lodes()
        log.info(
            f"Modifier data loaded for sim_year={self.sim_year}. "
            f"Ridership rows (full): {len(self.ridership_full_df):,} | "
            f"Ridership rows ({self.sim_year}): {len(self.ridership_df):,}"
        )

    # _load_ridership: Build the per-route historical baseline DataFrame.
    # ridership_df is filtered to sim_year; ridership_full_df retains all years.
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
                df = df.dropna(subset=["Average Daily Boardings", "Month"])

                self.ridership_full_df = df.copy()

                # Year-segment: keep only the sim_year for calibration
                year_df = df[df["Month"].dt.year == self.sim_year].copy()

                if year_df.empty:
                    log.warning(
                        f"No ridership data found for sim_year={self.sim_year}. "
                        f"Available years: {sorted(df['Month'].dt.year.unique().tolist())}. "
                        f"Falling back to full dataset."
                    )
                    self.ridership_df = df
                else:
                    self.ridership_df = year_df
                    log.info(
                        f"Ridership segmented to {self.sim_year}: "
                        f"{len(self.ridership_df):,} rows "
                        f"({len(df):,} total across all years)"
                    )
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

    # _load_commute_times: Load ACS commute departure time table for RB2.
    def _load_commute_times(self):
        for fname in os.listdir(self.modifier_dir):
            if fname.endswith(".csv") and ("C08132" in fname or "commute" in fname.lower()):
                try:
                    df = pd.read_csv(self._path(fname), dtype=str, low_memory=False)
                    df.columns = [c.strip() for c in df.columns]

                    # Normalise to three columns: label, estimate, margin_of_error
                    if len(df.columns) >= 2:
                        df = df.rename(columns={
                            df.columns[0]: "label",
                            df.columns[1]: "estimate",
                        })
                        df["estimate"] = pd.to_numeric(
                            df["estimate"].astype(str)
                                .str.replace(",", "").str.strip(),
                            errors="coerce",
                        )
                        df = df.dropna(subset=["estimate"])
                        df = df[df["estimate"] > 0]

                        if not df.empty:
                            self.commute_df = df
                            log.info(f"ACS commute departure loaded: {len(df)} rows from {fname}")
                            return
                except Exception:
                    log.exception(f"Failed to load ACS commute file: {fname}")

    # _load_lodes: Extract total commute worker count from the LODES origin-destination file.
    def _load_lodes(self):
        for fname in os.listdir(self.modifier_dir):
            if fname.endswith(".csv") and ("_od_" in fname or "lodes" in fname.lower()):
                try:
                    # S000 is the total jobs column — read only that to keep memory low
                    df = pd.read_csv(
                        self._path(fname), dtype=str, low_memory=False,
                        usecols=lambda c: c in ("S000", "s000"),
                    )
                    col = "S000" if "S000" in df.columns else "s000"
                    if col in df.columns:
                        total = pd.to_numeric(
                            df[col].astype(str).str.strip(), errors="coerce"
                        ).sum()
                        if total > 0:
                            self.commute_workers = int(total)
                            log.info(f"LODES commute workers loaded: {self.commute_workers:,}")
                            return
                except Exception:
                    log.exception(f"Failed to load LODES file: {fname}")

    # ---------------------------------------------------------------- helpers --

    # get_route_baseline: Year-segmented median historical boardings for a route/day-type pair.
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

    # get_route_baseline_full: Baseline from all years (used by non-RB2 systems if desired).
    def get_route_baseline_full(self, route_short_name: str, day_type: str) -> float:
        if self.ridership_full_df.empty:
            return self.get_route_baseline(route_short_name, day_type)
        mask = (
            (self.ridership_full_df["Route"].astype(str).str.strip()
             == str(route_short_name).strip())
            & (self.ridership_full_df["Service Day of the Week"].str.strip() == day_type)
        )
        subset = self.ridership_full_df[mask]["Average Daily Boardings"].dropna()
        return float(subset.median()) if not subset.empty else 3_000.0

    # density_factor: Population-based demand scalar relative to a 1M-person city.
    def density_factor(self) -> float:
        return min(self.population_total / 1_000_000, 2.0)
