#!/bin/bash
# scripts/sync_full_refresh.sh

set -e  # Exit on error

echo "════════════════════════════════════════════════════"
echo "   🌊 Kuroshio-Lab FULL Species Data Refresh"
echo "   ⚠️  WARNING: This will DELETE and REBUILD all data"
echo "════════════════════════════════════════════════════"
echo ""

# Confirmation prompt
read -p "⚠️  Are you sure you want to run FULL REFRESH? Type 'yes' to continue: " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "❌ Aborted"
    exit 1
fi

echo ""
echo "Starting FULL REFRESH in 5 seconds... Press Ctrl+C to cancel"
sleep 5

# ============================================================
# CONFIGURATION
# ============================================================

# Year range for full historical sync
YEAR_START=2015
YEAR_END=2026

# ============================================================
# STEP 0: CLEAR EXISTING DATA
# ============================================================

echo ""
echo "🗑️  Step 0/4: Clearing existing data..."
echo "────────────────────────────────────────────────────"

# Clear OBIS data
docker-compose exec backend python -c "
from species.models import CuratedObservation
obis_count = CuratedObservation.objects.filter(source='OBIS').count()
deleted = CuratedObservation.objects.filter(source='OBIS').delete()
print(f'🗑️  Deleted {deleted[0]} OBIS records (was {obis_count})')
"

# Clear GBIF data
docker-compose exec backend python -c "
from species.models import CuratedObservation
gbif_count = CuratedObservation.objects.filter(source='GBIF').count()
deleted = CuratedObservation.objects.filter(source='GBIF').delete()
print(f'🗑️  Deleted {deleted[0]} GBIF records (was {gbif_count})')
"

# Clear BOTH (merged) data
docker-compose exec backend python -c "
from species.models import CuratedObservation
both_count = CuratedObservation.objects.filter(source='BOTH').count()
deleted = CuratedObservation.objects.filter(source='BOTH').delete()
print(f'🗑️  Deleted {deleted[0]} BOTH records (was {both_count})')
"

echo ""
echo "✅ All existing data cleared"
echo ""

# ============================================================
# STEP 1: FULL OBIS SYNC
# ============================================================

echo "📡 Step 1/4: Full OBIS data sync (all historical data)..."
echo "────────────────────────────────────────────────────"
echo "   Mode: FULL (no date filters, no page limit)"
echo "   Coverage: Worldwide (default)"
echo ""

docker-compose exec backend python manage.py refresh_obis_data \
    --mode full

echo ""
echo "✅ OBIS full sync complete"
echo ""

# ============================================================
# STEP 2: FULL GBIF SYNC (YEAR BY YEAR)
# ============================================================

echo "📡 Step 2/4: Full GBIF data sync (ocean polygons)..."
echo "────────────────────────────────────────────────────"
echo "   Year Range: $YEAR_START to $YEAR_END"
echo "   Strategy: Ocean-based polygons (8 regions)"
echo ""

# Sync year by year to avoid timeouts
for YEAR in $(seq $YEAR_START $YEAR_END); do
    echo ""
    echo "   📅 Processing year: $YEAR"
    echo "   ────────────────────────────────────"

    docker-compose exec backend python manage.py sync_gbif_by_oceans \
        --year "$YEAR" \
        --limit 200

    echo "   ✅ Year $YEAR complete"

    # Small delay between years to be respectful to GBIF API
    sleep 2
done

echo ""
echo "✅ GBIF full sync complete"
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
echo "   ✅ FULL REFRESH COMPLETE!"
echo "   💾 Database has been completely rebuilt"
echo "════════════════════════════════════════════════════"
