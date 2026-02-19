"""
X (Twitter) Provider package.
"""

from socialconnector.core.registry import register_adapter

from .adapter import XAdapter

# Re-register with the registry
register_adapter("x")(XAdapter)
register_adapter("twitter")(XAdapter)

__all__ = ["XAdapter"]
