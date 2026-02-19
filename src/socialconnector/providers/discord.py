"""
Discord Provider Adapter.
See: docs/providers/DISCORD.md
"""
from socialconnector.core.base_adapter import BaseAdapter
from socialconnector.core.registry import register_adapter


@register_adapter("discord")
class DiscordAdapter(BaseAdapter):
    pass
