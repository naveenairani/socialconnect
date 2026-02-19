"""
Slack Provider Adapter.
See: docs/providers/SLACK.md
"""
from socialconnector.core.base_adapter import BaseAdapter
from socialconnector.core.registry import register_adapter

@register_adapter("slack")
class SlackAdapter(BaseAdapter):
    pass
