"""Content extraction utilities used by the analyze layer.

Re-exports the canonical trafilatura wrapper from ``signals_core.extract``.
The per-package copy is gone; a single implementation now serves every
layer.
"""

from signals_core.extract import ExtractedContent, extract_from_html

__all__ = ["ExtractedContent", "extract_from_html"]
