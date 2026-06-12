"""Source-agnostic data shapes and adapter protocols for occurrence ingestion.

These are the vocabulary of the seam: a ``Source`` normalizes a raw record into
a ``CanonicalOccurrence`` (or a ``Rejection``); a ``Traversal`` walks pages and
decides when to stop; ``IngestResult``/``IngestRun`` carry the counts the driver
reads back to make paging decisions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Protocol


@dataclass(frozen=True)
class PageContext:
    """Traversal-supplied facts a ``Source`` needs at normalize time.

    Today this is only the ocean label that ``OceanFanout`` stamps on each page
    (it becomes the ``location_name`` fallback). Keep it to named fields — do
    not widen into a general bag.
    """

    ocean_label: str | None = None


@dataclass(frozen=True)
class CanonicalOccurrence:
    """An occurrence after normalization — identical shape for every source.

    The required fields are the model's hard constraints; a ``Source`` returns
    a ``Rejection`` rather than a partial occurrence when one is missing.
    """

    occurrence_id: str
    species_name: str
    observation_date: date
    lon: float
    lat: float
    source: str
    common_name: str | None = None
    observation_datetime: datetime | None = None
    location_name: str | None = None
    machine_observation: str | None = None
    depth_min: float | None = None
    depth_max: float | None = None
    bathymetry: float | None = None
    temperature: float | None = None
    sex: str = "unknown"
    dataset_name: str = ""
    notes: str | None = None
    validated: str = "validated"


@dataclass(frozen=True)
class Rejection:
    """A raw record that cannot become a canonical occurrence."""

    reason: str


@dataclass
class Page:
    """One page of raw records plus the cursor to fetch the next one.

    ``next_cursor`` is ``None`` when the traversal is structurally exhausted —
    the driver keys end-of-run on the cursor, not on the record count, so a
    traversal may legitimately return a page filtered down to zero records while
    more pages remain.
    """

    records: list[dict]
    next_cursor: object | None = None
    context: PageContext = field(default_factory=PageContext)


@dataclass
class IngestResult:
    """Outcome of ingesting one page through the inner seam."""

    processed: int = 0
    saved: int = 0
    rejected: int = 0
    duplicates: int = 0


@dataclass
class IngestRun:
    """Accumulated outcome across a run.

    The driver reads this back between pages to decide whether to keep going —
    the run budget consumes ``saved``; deep-offset degradation consumes
    ``last``, ``last_requested``, and ``page_size`` (the unshrunk page size, so
    degradation can tell a full offset page from one shrunk to fit the budget).
    It is a read contract, not write-only.
    """

    processed: int = 0
    saved: int = 0
    rejected: int = 0
    duplicates: int = 0
    pages: int = 0
    last: IngestResult | None = None
    last_requested: int = 0
    page_size: int = 0

    def add(self, result: IngestResult, *, requested: int) -> None:
        self.processed += result.processed
        self.saved += result.saved
        self.rejected += result.rejected
        self.duplicates += result.duplicates
        self.pages += 1
        self.last = result
        self.last_requested = requested


class TaxonomyResolver(Protocol):
    """Three taxonomic questions; transport and response-selection hidden."""

    def common_name(self, aphia_id: int | None) -> str | None:
        """English common name for an AphiaID, or None."""

    def aphia_id(self, scientific_name: str | None) -> int | None:
        """AphiaID for a scientific name, or None."""

    def accepted_name(self, aphia_id: int | None) -> str | None:
        """Accepted scientific name for an AphiaID, or None."""


class Source(Protocol):
    """Maps one origin's raw record to a canonical occurrence."""

    name: str

    def identify(self, raw: dict) -> str | None:
        """The occurrence id this raw record will carry, before normalizing.

        Lets the inner seam dedup against ``seen`` without paying for
        normalization first — GBIF resolves taxonomy (a WoRMS call) inside
        ``normalize``, so an already-ingested record must be caught here, not
        after. Must agree with the ``occurrence_id`` ``normalize`` assigns.
        ``None`` when the raw record carries no stable id to dedup on; the
        record then falls through to ``normalize``.
        """

    def normalize(
        self,
        raw: dict,
        taxonomy: TaxonomyResolver,
        context: PageContext,
    ) -> CanonicalOccurrence | Rejection:
        """Turn one raw record into a canonical occurrence or a rejection."""


class Traversal(Protocol):
    """Walks an origin's pages and decides when to stop.

    ``should_stop`` is run-level: it receives the whole ``IngestRun`` so a
    source-specific stop (GBIF's deep-offset degradation) can read the last
    page's counts against the size that was requested.
    """

    def fetch_page(self, cursor: object | None, size: int) -> Page:
        """Fetch one page; ``next_cursor`` is None when exhausted."""

    def should_stop(self, run: IngestRun) -> bool:
        """True to end the run after the latest page (degradation)."""
