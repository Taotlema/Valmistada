# Valmistada: Synthetic Data Research

Valmistada is an undergraduate research project investigating whether rule-governed simulation can generate synthetic transit ridership data that reliably reflects real-world behavior. The central question is whether a simulation grounded in the universal rules of a real transit system can produce data useful enough to substitute for observed data in AI and planning applications.

The project builds a PyQt6 desktop simulation of the San Francisco MUNI network using real GTFS schedule data, SFMTA historical ridership, U.S. Census demographics, LODES employment flows, and SF land-use parcel data. Four generation models of increasing complexity {Deterministic, High-Fidelity, Rule-Based v1, and Rule-Based v2} each produce synthetic average daily boardings by route, month, service category, and day type across a simulated 2019 year. The resulting synthetic trials are benchmarked against the original 2019 SFMTA ridership data and an ML regression ceiling to measure distributional fidelity.

The findings show the simulation correctly reproduces the structural properties of the MUNI network but produces boardings below real-world scale, with the gap traceable to uncalibrated base demand rather than a flaw in the generative architecture.

## Colaborators
### Ayemhenre Isikhuemhen
**Computer Science Student** at University of North Carolina at Charlotte | Class of 2026<br>
Contacts: aisikhue@charlotte.edu | github.com/Taotlema

### Aileen Benedict
**CCI Professor** at University of North Carolina at Charlotte | Class of 2026<br>
Contacts: abenedi3@charlotte.edu | github.com/jelloh

## Referencess
List of reasources used for creating this project.

**Data Sources**
- SFMTA Ridership by Route — https://www.sfmta.com/reports/ridership-statistics
- SFMTA GTFS Feed — https://www.sfmta.com/reports/gtfs-transit-data
- ACS Table C08132 (Commute Departure Times) — https://data.census.gov/table/ACSDT1Y2024.C08132
- LODES Origin-Destination Employment Statistics — https://lehd.ces.census.gov/data/
- Decennial Census PL 94-171 — https://www.census.gov/programs-surveys/decennial-census/about/rdo/summary-files.html
- SF Land Use Dataset — https://data.sfgov.org/Housing-and-Buildings/Land-Use/us3s-fp9q

**Simulation Framework**
- PyQt6 — https://www.riverbankcomputing.com/software/pyqt/
- Qt6 — https://www.qt.io/
- PyYAML — https://yaml.org/  
= Python 3 — https://www.python.org/

**Analysis Libraries**
- NumPy — https://numpy.org/
- Pandas — https://pandas.pydata.org/
- Matplotlib — https://matplotlib.org/
- Seaborn — https://seaborn.pydata.org/
- SciPy — https://scipy.org/
- Scikit-learn — https://scikit-learn.org/
- NetworkX — https://networkx.org/

**Standards and Specifications**
- GTFS Reference — https://gtfs.org/schedule/reference/
- GTFS Validator — https://gtfs-validator.mobilitydata.org/
- National Transit Database — https://www.transit.dot.gov/ntd
