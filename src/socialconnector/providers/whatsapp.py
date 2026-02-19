"""
WhatsApp Cloud API Provider Adapter.
See: docs/providers/WHATSAPP.md
"""
from socialconnector.core.base_adapter import BaseAdapter
from socialconnector.core.registry import register_adapter

@register_adapter("whatsapp")
class WhatsAppAdapter(BaseAdapter):
    pass
