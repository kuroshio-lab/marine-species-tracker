#!/bin/bash
# scripts/sync_all_species.sh

set -e

# ============================================================
# USAGE
# ============================================================

usage() {
    echo "Usage: $0 [MODE]"
    echo ""
    echo "Modes:"
    echo "  incremental  - Sync recent data only (default)"
    echo "  full        - Complete database rebuild (deletes all data)"
    echo ""
    echo "Examples:"
    echo "  $0 incremental"
    echo "  $0 full"
    echo ""
    echo "Note: This script must be run from the project root:"
    echo "  cd /path/to/marine-species-tracker"
    echo "  ./scripts/sync_all_species.sh incremental"
    exit 1
}

# ============================================================
# CHECK DOCKER COMPOSE
# ============================================================

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Error: docker-compose not found"
    echo "Please install docker-compose first"
    exit 1
fi

# Check if backend service is running
if ! docker-compose ps | grep -q "backend.*Up"; then
    echo "❌ Error: Backend container is not running"
    echo "Please start your services first:"
    echo "  docker-compose up -d"
    exit 1
fi

# ============================================================
# PARSE ARGUMENTS
# ============================================================

MODE="${1:-incremental}"

if [ "$MODE" != "incremental" ] && [ "$MODE" != "full" ]; then
    echo "❌ Error: Invalid mode '$MODE'"
    echo ""
    usage
fi

# ============================================================
# EXECUTE APPROPRIATE SCRIPT
# ============================================================

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if [ "$MODE" = "incremental" ]; then
    echo "🔄 Running INCREMENTAL sync..."
    bash "$SCRIPT_DIR/sync_incremental.sh"
else
    echo "⚠️  Running FULL REFRESH..."
    bash "$SCRIPT_DIR/sync_full_refresh.sh"
fi
