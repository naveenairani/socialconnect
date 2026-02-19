"""
Aratai Provider Adapter.
See: docs/providers/ARATAI.md
"""
from socialconnector.core.base_adapter import BaseAdapter
from socialconnector.core.registry import register_adapter


@register_adapter("aratai")
class ArataiAdapter(BaseAdapter):
    pass
