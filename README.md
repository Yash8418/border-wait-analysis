# 🚗 Windsor–Detroit Border Wait Analysis

An analysis of traveller wait times at the two Windsor–Detroit crossings — the **Ambassador Bridge** and the **Detroit–Windsor Tunnel** — using open data published by the Canada Border Services Agency (CBSA).

> 🚧 Work in progress. This README will be expanded with findings and a live dashboard.

## Questions this project answers

- When are the crossings busiest — by hour of day, day of week, and month?
- How do long weekends and holidays affect waits?
- Is the Bridge or the Tunnel faster, and does that change by time of day?
- How did border traffic change before, during, and after COVID-19?

## Data

All data comes from the Government of Canada Open Data portal (Open Government Licence – Canada):

- [Historical Border Wait Times – Land Mode](https://open.canada.ca/data/en/dataset/000fe5aa-1d77-42d1-bfe7-458c51dacfef)

Raw files are downloaded automatically by a GitHub Actions workflow (`.github/workflows/fetch-data.yml`) using the portal's CKAN API, then filtered to the Windsor crossings.

## Project structure

```
├── scripts/fetch_data.py      # Downloads and filters the open data
├── data/raw/                  # Filtered raw data + manifest (generated)
├── src/border_wait/           # Cleaning and analysis code
└── tests/                     # Tests
```
