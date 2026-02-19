import pytest

from socialconnector.core.base_adapter import BaseAdapter
from socialconnector.core.exceptions import ProviderNotFoundError
from socialconnector.core.registry import AdapterRegistry, register_adapter


class MockAdapter(BaseAdapter):
    def __init__(self, config, http_client, logger):
        super().__init__(config, http_client, logger)

    async def connect(self): pass
    async def disconnect(self): pass
    async def health_check(self): pass
    async def send_message(self, chat_id, text, *, reply_to=None): pass
    async def send_media(self, chat_id, media, *, caption=None): pass
    async def edit_message(self, chat_id, message_id, new_text): pass
    async def delete_message(self, chat_id, message_id): pass
    async def get_messages(self, chat_id, *, limit=50): pass
    async def get_user_info(self, user_id): pass
    async def set_webhook(self, config): pass
    async def start_polling(self): pass
    async def stop_polling(self): pass

def test_registry_registration():
    registry = AdapterRegistry()
    registry.register("mock", MockAdapter)

    assert registry.get("mock") == MockAdapter
    assert "mock" in registry.list()

def test_register_decorator():
    @register_adapter("decorated")
    class DecoratedAdapter(MockAdapter):
        pass

    assert AdapterRegistry().get("decorated") == DecoratedAdapter

def test_registry_not_found():
    with pytest.raises(ProviderNotFoundError):
        AdapterRegistry().get("non_existent")

def test_singleton():
    assert AdapterRegistry() is AdapterRegistry()

    # Check that clear/internal state is shared
    AdapterRegistry().register("shared", MockAdapter)
    assert AdapterRegistry().get("shared") == MockAdapter
