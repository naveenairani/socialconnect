from unittest.mock import MagicMock

import pytest
import respx
from httpx import Response

from socialconnector.core.exceptions import AuthenticationError
from socialconnector.core.models import AdapterConfig
from socialconnector.providers.x import XAdapter
from socialconnector.utils.http_client import HTTPClient


@pytest.fixture
def twitter_config():
    return AdapterConfig(
        provider="x",
        api_key="consumer_key",
        api_secret="consumer_secret",
        extra={
            "access_token": "token",
            "access_token_secret": "token_secret"
        }
    )


@pytest.fixture
def mock_logger():
    return MagicMock()


@pytest.fixture
def http_client():
    return HTTPClient()


@pytest.mark.asyncio
@respx.mock
async def test_twitter_connect_success(twitter_config, mock_logger, http_client):
    respx.get("https://api.x.com/2/users/me").mock(return_value=Response(200, json={"data": {"id": "123"}}))

    adapter = XAdapter(twitter_config, http_client, mock_logger)
    await adapter.connect()
    assert True  # Should not raise


@pytest.mark.asyncio
@respx.mock
async def test_twitter_connect_auth_error(twitter_config, mock_logger, http_client):
    respx.get("https://api.x.com/2/users/me").mock(return_value=Response(401))

    adapter = XAdapter(twitter_config, http_client, mock_logger)
    with pytest.raises(AuthenticationError):
        await adapter.connect()


@pytest.mark.asyncio
@respx.mock
async def test_twitter_post_success(twitter_config, mock_logger, http_client):
    respx.post("https://api.x.com/2/tweets").mock(
        return_value=Response(201, json={"data": {"id": "tweet_123", "text": "test"}})
    )

    adapter = XAdapter(twitter_config, http_client, mock_logger)
    response = await adapter.post(text="test")

    assert response.success
    assert response.message_id == "tweet_123"


@pytest.mark.asyncio
async def test_twitter_direct_message_not_implemented(twitter_config, mock_logger, http_client):
    adapter = XAdapter(twitter_config, http_client, mock_logger)
    with pytest.raises(NotImplementedError):
        await adapter.direct_message(chat_id="123", text="hello")


@pytest.mark.asyncio
@respx.mock
async def test_twitter_delete_message_success(twitter_config, mock_logger, http_client):
    respx.delete("https://api.x.com/2/tweets/tweet_123").mock(return_value=Response(200))

    adapter = XAdapter(twitter_config, http_client, mock_logger)
    success = await adapter.delete_message(chat_id="none", message_id="tweet_123")
    assert success is True
