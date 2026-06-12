"""Content extraction utilities.

Re-exports the canonical trafilatura wrapper from ``signals_core.extract``.
The implementation moved there so signals_analyze can consume the same
helper without taking a dependency on signals_ingest.
"""

from signals_core.extract import ExtractedContent, extract_from_html

__all__ = ["ExtractedContent", "extract_from_html"]
