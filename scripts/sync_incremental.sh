#!/bin/bash
# scripts/sync_incremental.sh

set -e  # Exit on error

echo "════════════════════════════════════════════════════"
echo "   🌊 Kuroshio-Lab Incremental Species Sync"
echo "   📅 Mode: Incremental (Recent Data Only)"
echo "════════════════════════════════════════════════════"
echo ""

# ============================================================
# CONFIGURATION
# ============================================================

# Date range for incremental sync (adjust as needed)
START_DATE="2024-01-01"
END_DATE="2024-12-31"
YEAR="2024"

# OBIS pagination limit for incremental (pages per sync)
OBIS_MAX_PAGES=10

# GBIF record limit for incremental
GBIF_MAX_RECORDS=50000

# ============================================================
# STEP 1: SYNC OBIS DATA (INCREMENTAL)
# ============================================================

echo "📡 Step 1/4: Syncing OBIS data (incremental)..."
echo "────────────────────────────────────────────────────"
echo "   Date Range: $START_DATE to $END_DATE"
echo "   Max Pages: $OBIS_MAX_PAGES"
echo "   Coverage: Worldwide (default)"
echo ""

docker-compose exec backend python manage.py refresh_obis_data \
    --mode incremental \
    --start-date "$START_DATE" \
    --end-date "$END_DATE" \
    --max-pages $OBIS_MAX_PAGES

echo ""
echo "✅ OBIS incremental sync complete"
echo ""

# ============================================================
# STEP 2: SYNC GBIF DATA (OCEAN STRATEGY, INCREMENTAL)
# ============================================================

echo "📡 Step 2/4: Syncing GBIF data (ocean polygons)..."
echo "────────────────────────────────────────────────────"
echo "   Year Filter: $YEAR"
echo "   Strategy: Ocean-based polygons (8 regions)"
echo "   Max Records: $GBIF_MAX_RECORDS"
echo ""

docker-compose exec backend python manage.py sync_gbif_by_oceans \
    --year "$YEAR" \
    --limit 200

echo ""
echo "✅ GBIF incremental sync complete"
echo ""

# ============================================================
# STEP 3: DEDUPLICATE OBSERVATIONS
# ============================================================

echo "🔄 Step 3/4: Deduplicating observations..."
echo "────────────────────────────────────────────────────"

docker-compose exec backend python manage.py deduplicate_observations \
    --prefer OBIS

echo ""
echo "✅ Deduplication complete"
echo ""

# ============================================================
# STEP 4: DISPLAY FINAL STATISTICS
# ============================================================

echo "📊 Step 4/4: Final Database Statistics"
echo "────────────────────────────────────────────────────"

docker-compose exec backend python manage.py species_stats

echo ""
echo "════════════════════════════════════════════════════"
echo "   ✅ Incremental sync pipeline complete!"
echo "════════════════════════════════════════════════════"
