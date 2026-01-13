# 🌊 Marine Species ETL Pipeline

This system synchronizes marine biological observations into a unified database using **Django**, **GeoDjango**, and **PostGIS**. It aggregates data from **OBIS** and **GBIF**, utilizing the **WoRMS** API for taxonomic enrichment and common name mapping.

---

## 🛠 Pipeline Architecture

The ETL process follows a structured 4-step workflow to ensure data quality and uniqueness:

1.  **OBIS Sync**: Fetches global marine data, supporting both full history and incremental updates.
2.  **GBIF Sync**: Uses specialized spatial strategies (like Ocean Polygons) to fetch marine-specific records.
3.  **Deduplication**: Identifies records appearing in both providers by matching `occurrence_id` and merges them into a single entry.
4.  **Statistics**: Generates a health report of the database, including source breakdown and temporal coverage.

---

## 🛠 GBIF pipeline data

The GBIF extraction process is governed by a highly restrictive filtering strategy designed to balance data quality with operational efficiency. To bypass the GBIF API's record limits and minimize computational overhead, the pipeline first partitions queries into specific geographical polygons—such as the defined ocean regions. Within these regions, the system further narrows the scope by exclusively targeting observations that include depth parameters, ensuring the data is strictly relevant to marine environments. Once fetched, scientific names undergo a rigorous cleaning process before being validated against the WoRMS API; only records that achieve a verified taxonomic match are committed to the database. This strict multi-stage restriction is a deliberate architectural choice to minimize API costs and ensure that the resulting dataset is of the highest possible scientific integrity.

Suggestions for Enhancement :

  * Higher Resolution Polygons: Increasing the number and granularity of polygons (e.g., using Exclusive Economic Zones or specific marine ecoregions) would allow for more targeted data retrieval without hitting API caps.

  * Fuzzy Name Matching: Implementing a "fuzzy" logic threshold for the WoRMS matching step could help capture observations with minor typographical errors that are currently being rejected, without sacrificing taxonomic accuracy.

  * Asynchronous Processing: Moving the WoRMS validation and cleaning steps into a task queue (like Celery) could significantly speed up the initial ingestion from GBIF.

  * Temporal Chunking: In addition to spatial polygons, querying in smaller temporal chunks (e.g., month-by-month) would help ensure that high-density areas do not exceed the maximum record limit per request.

---

## 🚀 Execution Guide

All commands must be run inside the Docker environment.

### 1. Incremental Sync (Daily/Monthly)
This is the standard mode for keeping the database up to date with the latest observations.

**Using the bash script:**
```bash
docker-compose exec backend bash scripts/sync_incremental.sh
```

What this script does:

  * Syncs OBIS records for a specific date range.

  * Syncs GBIF records using the ocean_network strategy for the current year.

  * Merges duplicates, preferring OBIS metadata for shared records.

  * Outputs a final summary of total observations.

### 2. Full Historical Backfill
Used for initial setup or rebuilding a specific dataset from scratch.

-   **Full OBIS Refresh**
  ```bash
  docker-compose exec backend python manage.py refresh_obis_data --mode full
  ```
-   **Full GBIF Backfill (e.g., since 2015):**
  ```bash
  docker-compose exec backend python manage.py sync_gbif_full --year-start 2015 --clear-existing
  ```
---

## 🔧 Management Commands Reference

```bash
refresh_obis_data.py
```

Triggers the OBIS ETL process in a background thread to prevent timeouts.

-  --mode: Choose full or incremental.

-  --start-date / --end-date: Used in incremental mode (YYYY-MM-DD).

-  --max-pages: Limits the number of pages fetched per run.

```bash
sync_gbif_by_oceans.py
```

Optimized for GBIF's record limits by querying 8 specific ocean regions individually.

-  --year: Target year or comma-separated range (e.g., "2024").

-  --limit: Records per request per ocean (Default: 300).

```bash
deduplicate_observations.py
```

The "Glue" command that merges providers.

-  --prefer: Which source to prioritize during a merge (choices: OBIS, GBIF).

-  --dry-run: Shows potential merges without modifying the database.

---

## 📊 Monitoring & Data QualityTo check the current state of your data

```bash
docker-compose exec backend python manage.py species_stats
```

MetricDescriptionSource: BOTHRecords successfully merged from both OBIS and GBIF.Depth DataPercentage of records containing vertical distribution info.Deduplication HealthChecks for orphan duplicates that need merging.

---

## 📊 Monitoring & Data QualityTo check the current state of your data

-   **Docker & Docker Compose** : All commands are containerized.
-   **PostGIS** : Required for spatial queries and WKT polygon handling.
-   **Poetry** : Used for Python dependency management inside the container.
