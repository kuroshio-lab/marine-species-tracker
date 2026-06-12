# Marine Occurrence Ingestion

How external species records (OBIS, GBIF) become curated observations on the
map. This context names the data shapes and modules of the ingestion pipeline.
It currently covers the backend ingestion path only; if other contexts get
documented later, promote this to a `CONTEXT-MAP.md`.

## Language

**Occurrence**:
A single species sighting as reported by an external origin (OBIS or GBIF),
keyed by a Darwin Core occurrenceID. The raw input to ingestion.
_Avoid_: record, row, sighting

**Curated observation**:
A persisted, deduplicated occurrence in our database (the `CuratedObservation`
model), ready to show on the map. The output of ingestion.
_Avoid_: result, entry

**Canonical occurrence**:
A source-agnostic occurrence after normalization — identical fields whether it
came from OBIS or GBIF. The value that crosses from `normalize` into dedup and
persist.
_Avoid_: cleaned record, DTO

**Occurrence ingestion**:
The deep module that turns raw occurrences into curated observations:
normalize → dedup → persist, driven page by page.
_Avoid_: ETL, pipeline, sync

**Source**:
The per-origin normalizer mapping one origin's raw occurrence to a canonical
occurrence (`OBISSource`, `GBIFSource`). Knows record shape, not how to page.
_Avoid_: client, API, provider

**Taxonomy resolver**:
The seam in front of WoRMS, answering three taxonomic questions — common name
from AphiaID, AphiaID from scientific name, accepted name from AphiaID. HTTP in
production, in-memory in tests.
_Avoid_: WoRMS client, enricher

**Traversal**:
The per-origin-and-strategy module that walks an origin's pages and decides when
to stop (`CursorTraversal`, `OffsetTraversal`, `OceanFanout`). Knows how to page,
not record shape.
_Avoid_: pager, strategy, loop

**Ocean fan-out**:
A GBIF traversal that queries each ocean polygon once instead of paging by
offset, tagging each page with its ocean label.
_Avoid_: ocean loop

**Deep-offset degradation**:
GBIF offset paging returning a page of mostly already-seen occurrences past a
large offset — the signal to stop that traversal.
_Avoid_: dupe wall

**Run budget**:
A cap on a single ingestion run — by saved occurrences (`max_records`, which
also shrinks the final page) or by page count (`max_pages`, which does not).
_Avoid_: limit
