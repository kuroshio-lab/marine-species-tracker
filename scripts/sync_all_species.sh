#!/bin/bash
# scripts/sync_all_species.sh

set -e  # Exit on error

echo "════════════════════════════════════════════════════"
echo "   🌊 Kuroshio-Lab Species Data Sync Pipeline"
echo "════════════════════════════════════════════════════"
echo ""

# Configuration
YEAR="2024,2025"
GEOMETRY="POLYGON((127.15 26.10, 127.50 26.10, 127.50 26.35, 127.15 26.35, 127.15 26.10))"

# Step 1: Sync OBIS
echo "📡 Step 1/4: Syncing OBIS data..."
echo "────────────────────────────────────────────────────"
python manage.py refresh_obis_data \
    --mode=incremental \
    --start-date=2024-01-01 \
    --end-date=2025-12-31 \
    --geometry="$GEOMETRY"

echo ""
echo "✅ OBIS sync complete"
echo ""

# Step 2: Sync GBIF (OBIS network)
echo "📡 Step 2/4: Syncing GBIF data (OBIS network)..."
echo "────────────────────────────────────────────────────"
python manage.py sync_gbif_incremental \
    --year="$YEAR" \
    --strategy=obis_network \
    --max-records=50000

echo ""
echo "✅ GBIF sync complete"
echo ""

# Step 3: Deduplicate
echo "🔄 Step 3/4: Deduplicating observations..."
echo "────────────────────────────────────────────────────"
python manage.py deduplicate_observations --prefer=OBIS

echo ""
echo "✅ Deduplication complete"
echo ""

# Step 4: Show stats
echo "📊 Step 4/4: Final Statistics"
echo "────────────────────────────────────────────────────"
python manage.py species_stats

echo ""
echo "════════════════════════════════════════════════════"
echo "   ✅ Sync pipeline complete!"
echo "════════════════════════════════════════════════════"
