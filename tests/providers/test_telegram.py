import json
from unittest.mock import MagicMock

import pytest
import respx
from httpx import Response

from socialconnector.core.exceptions import AuthenticationError, MessageError
from socialconnector.core.models import AdapterConfig
from socialconnector.providers.telegram import TelegramAdapter
from socialconnector.utils.http_client import HTTPClient


@pytest.fixture
def telegram_config():
    return AdapterConfig(
        provider="telegram",
        api_key="bot_token",
        extra={}
    )


@pytest.fixture
def mock_logger():
    return MagicMock()


@pytest.fixture
def http_client():
    return HTTPClient()


@pytest.mark.asyncio
@respx.mock
async def test_telegram_connect_success(telegram_config, mock_logger, http_client):
    respx.get("https://api.telegram.org/botbot_token/getMe").mock(
        return_value=Response(200, json={"ok": True, "result": {"id": 123, "username": "bot"}})
    )
    
    adapter = TelegramAdapter(telegram_config, http_client, mock_logger)
    await adapter.connect()
    assert True


@pytest.mark.asyncio
@respx.mock
async def test_telegram_connect_auth_error(telegram_config, mock_logger, http_client):
    respx.get("https://api.telegram.org/botbot_token/getMe").mock(return_value=Response(401))
    
    adapter = TelegramAdapter(telegram_config, http_client, mock_logger)
    with pytest.raises(AuthenticationError):
        await adapter.connect()


@pytest.mark.asyncio
@respx.mock
async def test_telegram_direct_message_success(telegram_config, mock_logger, http_client):
    respx.post("https://api.telegram.org/botbot_token/sendMessage").mock(
        return_value=Response(200, json={"ok": True, "result": {"message_id": 456}})
    )
    
    adapter = TelegramAdapter(telegram_config, http_client, mock_logger)
    response = await adapter.direct_message(chat_id="123", text="hello")
    
    assert response.success
    assert response.message_id == "456"


@pytest.mark.asyncio
@respx.mock
async def test_telegram_delete_message_success(telegram_config, mock_logger, http_client):
    respx.post("https://api.telegram.org/botbot_token/deleteMessage").mock(
        return_value=Response(200, json={"ok": True})
    )
    
    adapter = TelegramAdapter(telegram_config, http_client, mock_logger)
    success = await adapter.delete_message(chat_id="123", message_id="456")
    assert success is True


@pytest.mark.asyncio
@respx.mock
async def test_telegram_post_success(telegram_config, mock_logger, http_client):
    respx.post("https://api.telegram.org/botbot_token/sendMessage").mock(
        return_value=Response(200, json={"ok": True, "result": {"message_id": 789}})
    )
    
    adapter = TelegramAdapter(telegram_config, http_client, mock_logger)
    response = await adapter.post(text="publicish hello")
    
    assert response.success
    assert response.message_id == "789"
