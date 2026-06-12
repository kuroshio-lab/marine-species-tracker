"""The outer seam: the paging driver.

Owns the page loop, the run accumulator, and every generic stop — structural
exhaustion and both run budgets. Source-specific stops live on the traversal
(``Traversal.should_stop``). Pairs one ``Source`` with one ``Traversal``.
"""

from __future__ import annotations

import logging

from species.models import CuratedObservation

from .records import ingest_records
from .types import IngestRun, Source, TaxonomyResolver, Traversal

logger = logging.getLogger(__name__)

DEFAULT_PAGE_SIZE = 300


def ingest_source(
    source: Source,
    traversal: Traversal,
    *,
    taxonomy: TaxonomyResolver,
    page_size: int = DEFAULT_PAGE_SIZE,
    max_records: int | None = None,
    max_pages: int | None = None,
) -> IngestRun:
    """Drive ``traversal`` through its pages, ingesting each via ``source``.

    Stops on structural exhaustion (``next_cursor is None``), on either run
    budget, or when the traversal reports deep-offset degradation.
    ``max_records`` also shrinks the final page so the run never overshoots its
    saved-record budget; ``max_pages`` only caps the page count and never
    shrinks a page.
    """
    run = IngestRun()
    cursor: object | None = None
    seen = set(
        CuratedObservation.objects.values_list("occurrence_id", flat=True)
    )

    while True:
        if max_records is not None and run.saved >= max_records:
            break
        if max_pages is not None and run.pages >= max_pages:
            break

        size = page_size
        if max_records is not None:
            size = min(size, max_records - run.saved)

        page = traversal.fetch_page(cursor, size)
        result = ingest_records(
            source,
            page.records,
            taxonomy=taxonomy,
            seen=seen,
            context=page.context,
        )
        run.add(result, requested=size)
        logger.info(
            f"{source.name} page {run.pages}: +{result.saved} saved, "
            f"{result.duplicates} dup, {result.rejected} rejected"
        )

        if page.next_cursor is None or traversal.should_stop(run):
            break
        cursor = page.next_cursor

    return run
