"""Occurrence ingestion — the deep module that turns raw OBIS/GBIF records
into curated observations.

Public interface:

- ``ingest_source(source, traversal, *, taxonomy, ...)`` — the paging driver
  (outer seam). Owns the loop, the run accumulator, and every generic stop.
- ``ingest_records(source, records, *, taxonomy, seen, context)`` — the
  collapse (inner seam): normalize -> dedup -> persist over one page.
- ``Source`` / ``Traversal`` / ``TaxonomyResolver`` — the adapter protocols.
- Concrete adapters: ``OBISSource`` + ``CursorTraversal`` (OBIS);
  ``GBIFSource`` + ``OffsetTraversal`` + ``OceanFanout`` (GBIF);
  ``WoRMSResolver`` (prod taxonomy) + ``DictResolver`` (test taxonomy).

See ``CONTEXT.md`` at the repo root for the domain language.
"""

from .driver import ingest_source
from .gbif import OCEAN_POLYGONS_WKT, GBIFSource, OceanFanout, OffsetTraversal
from .obis import CursorTraversal, OBISSource
from .records import ingest_records
from .taxonomy import DictResolver, WoRMSResolver
from .types import (
    CanonicalOccurrence,
    IngestResult,
    IngestRun,
    Page,
    PageContext,
    Rejection,
    Source,
    TaxonomyResolver,
    Traversal,
)

__all__ = [
    "ingest_source",
    "ingest_records",
    "Source",
    "Traversal",
    "TaxonomyResolver",
    "OBISSource",
    "CursorTraversal",
    "GBIFSource",
    "OffsetTraversal",
    "OceanFanout",
    "OCEAN_POLYGONS_WKT",
    "WoRMSResolver",
    "DictResolver",
    "CanonicalOccurrence",
    "Rejection",
    "PageContext",
    "Page",
    "IngestResult",
    "IngestRun",
]
