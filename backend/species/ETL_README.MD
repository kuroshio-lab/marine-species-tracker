# Marine Species ETL Pipeline

This system synchronizes marine biological observations into a unified database using **Django**, **GeoDjango**, and **PostGIS**. It aggregates data from **OBIS** and **GBIF**, utilizing the **WoRMS** API for taxonomic enrichment and common name mapping.

---

## Pipeline Architecture

The ETL process follows a structured 4-step workflow to ensure data quality and uniqueness:

1. **OBIS Sync**: Fetches global marine data, supporting both full history and incremental updates.
2. **GBIF Sync**: Uses specialized spatial strategies (like Ocean Polygons) to fetch marine-specific records.
3. **Deduplication**: Identifies records appearing in both providers by matching `occurrence_id` and merges them into a single entry.
4. **Statistics**: Generates a health report of the database, including source breakdown and temporal coverage.

---

## GBIF Pipeline Data

The GBIF extraction process is governed by a highly restrictive filtering strategy designed to balance data quality with operational efficiency. To bypass the GBIF API's record limits and minimize computational overhead, the pipeline first partitions queries into specific geographical polygons—such as the defined ocean regions. Within these regions, the system further narrows the scope by exclusively targeting observations that include depth parameters, ensuring the data is strictly relevant to marine environments. Once fetched, scientific names undergo a rigorous cleaning process before being validated against the WoRMS API; only records that achieve a verified taxonomic match are committed to the database. This strict multi-stage restriction is a deliberate architectural choice to minimize API costs and ensure that the resulting dataset is of the highest possible scientific integrity.

**Suggestions for Enhancement:**

- **Higher Resolution Polygons**: Increasing the number and granularity of polygons (e.g., using Exclusive Economic Zones or specific marine ecoregions) would allow for more targeted data retrieval without hitting API caps.
- **Fuzzy Name Matching**: Implementing a "fuzzy" logic threshold for the WoRMS matching step could help capture observations with minor typographical errors that are currently being rejected, without sacrificing taxonomic accuracy.
- **Asynchronous Processing**: Moving the WoRMS validation and cleaning steps into a task queue (like Celery) could significantly speed up the initial ingestion from GBIF.
- **Temporal Chunking**: In addition to spatial polygons, querying in smaller temporal chunks (e.g., month-by-month) would help ensure that high-density areas do not exceed the maximum record limit per request.

---

## Execution Guide

All commands must be run inside the Docker environment.

### 1. Incremental Sync (Daily/Monthly)

This is the standard mode for keeping the database up to date with the latest observations.

**OBIS incremental sync (last 30 days by default):**
```bash
docker-compose exec backend python manage.py refresh_obis_data --mode incremental
```

**GBIF incremental sync (ocean-based strategy, current year by default):**
```bash
docker-compose exec backend python manage.py sync_gbif_incremental
```

**Then deduplicate:**
```bash
docker-compose exec backend python manage.py deduplicate_observations
```

What the incremental pipeline does:
- Syncs OBIS records for a specific date range (defaults to last 30 days).
- Syncs GBIF records using the `oceans` strategy for the current year.
- Merges duplicates, preferring OBIS metadata for shared records.

### 2. Full Historical Backfill

Used for initial setup or rebuilding a specific dataset from scratch.

**Full OBIS Refresh:**
```bash
docker-compose exec backend python manage.py refresh_obis_data --mode full
```

**Full GBIF Backfill (e.g., since 2015, using ocean polygon strategy):**
```bash
docker-compose exec backend python manage.py sync_gbif_by_oceans --year 2015 --clear-existing
```

**Or using the legacy full-refresh command (iterates year by year):**
```bash
docker-compose exec backend python manage.py sync_gbif_full --year-start 2015 --clear-existing
```

---

## Management Commands Reference

### `refresh_obis_data`

Triggers the OBIS ETL process in a background thread to prevent timeouts.

| Argument | Description | Default |
|---|---|---|
| `--mode` | `full` (all data, dynamic pagination) or `incremental` (date-range) | `incremental` |
| `--start-date` | Start date (`YYYY-MM-DD`). Incremental only. | 30 days ago |
| `--end-date` | End date (`YYYY-MM-DD`). Incremental only. | Today |
| `--max-pages` | Limit number of pages fetched per run. | Settings default |
| `--geometry` | WKT polygon to restrict the OBIS spatial query. | Global bounding box |
| `--taxonid` | Filter by a specific OBIS taxon ID. | None |

---

### `sync_gbif_by_oceans`

Optimized for GBIF's record limits by querying 8 specific ocean regions individually.

| Argument | Description | Default |
|---|---|---|
| `--year` | Target year or comma-separated range (e.g., `"2024"` or `"2023,2024"`) | **Required** |
| `--limit` | Records per request per ocean. | `300` |
| `--clear-existing` | Delete all existing GBIF records before sync (full mode). | Off |

---

### `sync_gbif_incremental`

Fetches recent GBIF observations using a configurable spatial strategy.

| Argument | Description | Default |
|---|---|---|
| `--year` | Year or range (e.g., `"2024"` or `"2023,2024"`) | Current year |
| `--strategy` | `oceans`, `obis_network`, or `marine_geographic` | `oceans` |
| `--geometry` | WKT polygon (used with `marine_geographic` strategy) | None |
| `--max-records` | Stop after this many records saved. | `10000` |

---

### `sync_gbif_full`

Full GBIF historical backfill — iterates year by year. Use sparingly (slow, high API usage).

| Argument | Description | Default |
|---|---|---|
| `--year-start` | Start year for historical data. | `2015` |
| `--year-end` | End year. | Current year |
| `--strategy` | `obis_network` or `marine_geographic` | `obis_network` |
| `--geometry` | WKT polygon (used with `marine_geographic` strategy) | None |
| `--clear-existing` | Delete existing GBIF records before sync. | Off |

---

### `deduplicate_observations`

The "Glue" command that merges records that appear in both OBIS and GBIF.

| Argument | Description | Default |
|---|---|---|
| `--prefer` | Which source to prioritize during a merge (`OBIS` or `GBIF`). | `OBIS` |
| `--dry-run` | Show potential merges without modifying the database. | Off |

---

## Monitoring & Data Quality

To check the current state of your data:

```bash
docker-compose exec backend python manage.py species_stats
```

This command outputs a full health report including:

| Metric | Description |
|---|---|
| **Total Observations** | Total record count across all sources. |
| **Source Breakdown** | Count and percentage of OBIS-only, GBIF-only, and merged (BOTH) records. |
| **Temporal Coverage** | Oldest and newest observation dates in the database. |
| **Depth Data** | Percentage of records containing depth/bathymetry information. |
| **Common Names** | Percentage of records with a WoRMS-verified common name. |
| **Deduplication Health** | Count of occurrence IDs with remaining duplicates. |
| **Top 10 Species** | Most-observed species by record count, with common names. |

---

## Prerequisites

- **Docker & Docker Compose**: All commands are containerized.
- **PostGIS**: Required for spatial queries and WKT polygon handling.
- **Poetry**: Used for Python dependency management inside the container.
