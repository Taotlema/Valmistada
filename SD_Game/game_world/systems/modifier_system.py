# modifier_system: Applies loaded modifier data to scale per-stop demand weights at sim start.

from typing import List
from game_world.entities.station import Station


# ModifierSystem: Weights station base_demand using population density and land-use data.
class ModifierSystem:

    def __init__(self, modifier_loader):
        self._modifier = modifier_loader

    # apply: Adjust base_demand on every station using census and land-use data.
    def apply(self, stations: List[Station]):
        if not self._modifier:
            return

        # Scale all stations by the city's population density relative to 1M baseline
        density = self._modifier.density_factor()
        for s in stations:
            s.base_demand *= density

        # Further weight by residential parcel share to favour dense residential areas
        res_parcels   = self._modifier.land_use_counts.get("RESIDENT", 0)
        mixed_parcels = self._modifier.land_use_counts.get("MIXRES",   0)
        total_parcels = sum(self._modifier.land_use_counts.values()) or 1
        res_share     = (res_parcels + mixed_parcels) / total_parcels

        for s in stations:
            s.base_demand *= (0.8 + 0.4 * res_share)
