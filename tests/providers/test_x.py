import logging

import pytest
import respx
from httpx import AsyncClient, Response

from pydantic import SecretStr

from socialconnector.core.exceptions import AuthenticationError, RateLimitError
from socialconnector.core.models import AdapterConfig
from socialconnector.providers.x import XAdapter
from socialconnector.providers.x._auth import BearerTokenManager


@pytest.fixture
def x_config():
    return AdapterConfig(
        provider="x",
        api_key="consumer_key",
        api_secret="consumer_secret",
        extra={"access_token": "token", "access_token_secret": "token_secret"},
    )


@pytest.fixture
def mock_logger():
    return logging.getLogger("test")


@pytest.fixture
def http_client():
    return AsyncClient()


@pytest.fixture(autouse=True)
def mock_x_token():
    with respx.mock:
        # Corrected URL per Bug #1
        respx.post("https://api.x.com/oauth2/token").mock(
            return_value=Response(200, json={"access_token": "mock_bearer_token"})
        )
        yield


@pytest.mark.asyncio
@respx.mock
async def test_x_connect_success(x_config, mock_logger, http_client):
    respx.get("https://api.x.com/2/users/me").mock(return_value=Response(200, json={"data": {"id": "123"}}))

    adapter = XAdapter(x_config, http_client, mock_logger)
    await adapter.connect()
    assert adapter.auth_strategy == "oauth1"


@pytest.mark.asyncio
@respx.mock
async def test_x_connect_auth_error(x_config, mock_logger, http_client):
    respx.get("https://api.x.com/2/users/me").mock(return_value=Response(401))

    adapter = XAdapter(x_config, http_client, mock_logger)
    with pytest.raises(AuthenticationError):
        await adapter.connect()


@pytest.mark.asyncio
@respx.mock
async def test_x_post_success(x_config, mock_logger, http_client):
    respx.post("https://api.x.com/2/tweets").mock(
        return_value=Response(201, json={"data": {"id": "tweet_123", "text": "test"}})
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    response = await adapter.post(text="test")

    assert response.success
    assert response.message_id == "tweet_123"


@pytest.mark.asyncio
@respx.mock
async def test_x_post_with_reply_and_quote(x_config, http_client, mock_logger):
    respx.post("https://api.x.com/2/tweets").mock(
        return_value=Response(201, json={"data": {"id": "12345", "text": "Hello world"}})
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    res = await adapter.post("Hello world", reply_to_id="67890", quote_tweet_id="11223")

    assert res.success is True
    assert res.message_id == "12345"


@pytest.mark.asyncio
@respx.mock
async def test_x_delete_message_success(x_config, mock_logger, http_client):
    respx.delete("https://api.x.com/2/tweets/tweet_123").mock(return_value=Response(200))

    adapter = XAdapter(x_config, http_client, mock_logger)
    success = await adapter.delete_message(chat_id="none", message_id="tweet_123")
    assert success is True


@pytest.mark.asyncio
@respx.mock
async def test_x_get_tweet(x_config, http_client, mock_logger):
    respx.get("https://api.x.com/2/tweets/12345").mock(
        return_value=Response(
            200,
            json={
                "data": {
                    "id": "12345",
                    "text": "Existing tweet",
                    "author_id": "999",
                    "created_at": "2023-01-01T00:00:00Z",
                }
            },
        )
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    tweet = await adapter.get_tweet("12345")
    assert tweet.id == "12345"
    assert tweet.author_id == "999"


@pytest.mark.asyncio
@respx.mock
async def test_x_direct_message_user(x_config, http_client, mock_logger):
    # Tests that direct_message always routes to "with/{user_id}"
    respx.post("https://api.x.com/2/dm_conversations/with/user123/messages").mock(
        return_value=Response(201, json={"data": {"id": "dm999"}})
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    res = await adapter.direct_message("user123", "Hello DM")
    assert res.success is True
    assert res.message_id == "dm999"


@pytest.mark.asyncio
@respx.mock
async def test_x_send_to_conversation(x_config, http_client, mock_logger):
    # Tests the new send_to_conversation method
    respx.post("https://api.x.com/2/dm_conversations/conv123/messages").mock(
        return_value=Response(201, json={"data": {"id": "dm888"}})
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    res = await adapter.send_to_conversation("conv123", "Hello Conv")
    assert res.success is True
    assert res.message_id == "dm888"


@pytest.mark.asyncio
@respx.mock
async def test_x_likes_and_follows(x_config, http_client, mock_logger):
    respx.post("https://api.x.com/2/users/user1/likes").mock(return_value=Response(200, json={"data": {"liked": True}}))
    respx.post("https://api.x.com/2/users/user1/following").mock(
        return_value=Response(200, json={"data": {"following": True}})
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    success = await adapter.like_tweet("user1", "tweet1")
    assert success is True

    followed = await adapter.follow_user("user1", "target2")
    assert followed is True


@pytest.mark.asyncio
@respx.mock
async def test_x_rate_limit_handling(x_config, http_client, mock_logger):
    respx.get("https://api.x.com/2/tweets/rate_limited").mock(
        return_value=Response(429, headers={"x-rate-limit-reset": "1672531200"}, text="Too Many Requests")
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    with pytest.raises(RateLimitError) as excinfo:
        await adapter._request("GET", "tweets/rate_limited")

    assert excinfo.value.retry_after == 1672531200


@pytest.mark.asyncio
@respx.mock
async def test_x_bookmarks(x_config, http_client, mock_logger):
    # Verify Bug #4: bookmarks require OAuth1
    respx.post("https://api.x.com/2/users/u1/bookmarks").mock(
        return_value=Response(200, json={"data": {"bookmarked": True}})
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    res = await adapter.bookmark_tweet("u1", "t1")
    assert res is True


@pytest.mark.asyncio
@respx.mock
async def test_x_media_upload_v2(x_config, http_client, mock_logger):
    # Verify Bug #3: Media upload uses v2 URL and response parsing
    from socialconnector.core.models import Media, MediaType

    # INIT
    respx.post("https://api.x.com/2/media/upload?command=INIT&total_bytes=10&media_type=image%2Fjpeg").mock(
        return_value=Response(200, json={"data": {"id": "media_v2_123"}})
    )
    # APPEND
    respx.post("https://api.x.com/2/media/upload?command=APPEND&media_id=media_v2_123&segment_index=0").mock(
        return_value=Response(200)
    )
    # FINALIZE
    respx.post("https://api.x.com/2/media/upload?command=FINALIZE&media_id=media_v2_123").mock(
        return_value=Response(200, json={"data": {"id": "media_v2_123"}})
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    media = Media(type=MediaType.IMAGE, file_bytes=b"0123456789", mime_type="image/jpeg")

    media_id = await adapter._upload_media(media)
    assert media_id == "media_v2_123"


@pytest.mark.asyncio
@respx.mock
async def test_x_bearer_token_fetching(mock_logger, http_client):
    # Verify Bug #1: Bearer token URL
    from socialconnector.core.models import AdapterConfig

    config = AdapterConfig(provider="x", api_key="k", api_secret="s")

    route = respx.post("https://api.x.com/oauth2/token").mock(
        return_value=Response(200, json={"access_token": "valid_token"})
    )

    adapter = XAdapter(config, http_client, mock_logger)
    token = await adapter.bearer_token_manager.get()

    assert token == "valid_token"
    assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_x_get_conversation_messages(x_config, http_client, mock_logger):
    conv_id = "conv123"
    respx.get(f"https://api.x.com/2/dm_conversations/{conv_id}/dm_events").mock(
        return_value=Response(
            200,
            json={
                "data": [
                    {
                        "id": "e1",
                        "text": "msg1",
                        "sender_id": "u1",
                        "created_at": "2023-01-01T00:00:00Z",
                        "dm_conversation_id": conv_id,
                    }
                ]
            },
        )
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    messages = await adapter.get_conversation_messages(conv_id)
    assert len(messages) == 1
    assert messages[0].text == "msg1"
    assert messages[0].chat_id == conv_id


@pytest.mark.asyncio
@respx.mock
async def test_x_get_participant_messages(x_config, http_client, mock_logger):
    participant_id = "u1"
    respx.get(f"https://api.x.com/2/dm_conversations/with/{participant_id}/dm_events").mock(
        return_value=Response(
            200,
            json={
                "data": [
                    {
                        "id": "e2",
                        "text": "msg2",
                        "sender_id": participant_id,
                        "created_at": "2023-01-01T00:00:00Z",
                        "dm_conversation_id": "conv456",
                    }
                ]
            },
        )
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    messages = await adapter.get_participant_messages(participant_id)
    assert len(messages) == 1
    assert messages[0].text == "msg2"
    assert messages[0].sender.id == participant_id


@pytest.mark.asyncio
@respx.mock
async def test_x_create_group_conversation(x_config, http_client, mock_logger):
    participant_ids = ["u1", "u2"]
    text = "Hello group"
    respx.post("https://api.x.com/2/dm_conversations").mock(
        return_value=Response(201, json={"data": {"id": "dm_grp_1", "dm_conversation_id": "conv_grp_1"}})
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    res = await adapter.create_group_conversation(participant_ids, text)
    assert res.success is True
    assert res.message_id == "dm_grp_1"


@pytest.mark.asyncio
@respx.mock
async def test_x_get_messages(x_config, http_client, mock_logger):
    respx.get("https://api.x.com/2/dm_events").mock(
        return_value=Response(
            200,
            json={
                "data": [
                    {
                        "id": "e3",
                        "text": "msg3",
                        "sender_id": "u1",
                        "created_at": "2023-01-01T00:00:00Z",
                        "dm_conversation_id": "conv789",
                    },
                    {
                        "id": "e4",
                        "text": "msg4",
                        "sender_id": "u2",
                        "created_at": "2023-01-01T01:00:00Z",
                        "dm_conversation_id": "conv789",
                    },
                ]
            },
        )
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    messages = await adapter.get_messages(limit=10)
    assert len(messages) == 2
    assert messages[0].text == "msg3"
    assert messages[1].text == "msg4"

    # Test filtering by chat_id
    filtered = await adapter.get_messages(chat_id="conv789")
    assert len(filtered) == 2

    filtered_none = await adapter.get_messages(chat_id="nonexistent")
    assert len(filtered_none) == 0


@pytest.mark.asyncio
@respx.mock
async def test_x_create_compliance_job(x_config, http_client, mock_logger):
    respx.post("https://api.x.com/2/compliance/jobs").mock(
        return_value=Response(
            201,
            json={
                "data": {
                    "id": "job123",
                    "type": "tweets",
                    "name": "test_job",
                    "upload_url": "https://upload.example.com",
                    "download_url": "https://download.example.com",
                    "status": "created",
                }
            },
        )
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    job = await adapter.create_compliance_job("tweets", "test_job")
    assert job["id"] == "job123"
    assert job["upload_url"] == "https://upload.example.com"


@pytest.mark.asyncio
@respx.mock
async def test_x_list_compliance_jobs(x_config, http_client, mock_logger):
    respx.get("https://api.x.com/2/compliance/jobs").mock(
        return_value=Response(
            200,
            json={
                "data": [
                    {"id": "job1", "type": "tweets", "status": "complete"},
                    {"id": "job2", "type": "users", "status": "in_progress"},
                ]
            },
        )
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    jobs = await adapter.list_compliance_jobs()
    assert len(jobs) == 2
    assert jobs[0]["id"] == "job1"


@pytest.mark.asyncio
@respx.mock
async def test_x_get_compliance_job(x_config, http_client, mock_logger):
    respx.get("https://api.x.com/2/compliance/jobs/job123").mock(
        return_value=Response(200, json={"data": {"id": "job123", "status": "complete"}})
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    job = await adapter.get_compliance_job("job123")
    assert job["id"] == "job123"
    assert job["status"] == "complete"


@pytest.mark.asyncio
@respx.mock
async def test_x_upload_compliance_ids(x_config, http_client, mock_logger, tmp_path):
    # Mock the external upload URL
    respx.put("https://upload.example.com").mock(return_value=Response(200))

    # Create dummy ID file
    id_file = tmp_path / "ids.txt"
    id_file.write_text("123\n456\n")

    adapter = XAdapter(x_config, http_client, mock_logger)
    success = await adapter.upload_compliance_ids("https://upload.example.com", str(id_file))
    assert success is True


@pytest.mark.asyncio
@respx.mock
async def test_x_download_compliance_results(x_config, http_client, mock_logger):
    # Mock the external download URL
    respx.get("https://download.example.com").mock(return_value=Response(200, text="123,delete\n456,delete"))

    adapter = XAdapter(x_config, http_client, mock_logger)
    results = await adapter.download_compliance_results("https://download.example.com")
    assert "123,delete" in results


@pytest.mark.asyncio
async def test_bearer_token_manager_secret_masking(mock_logger, http_client):
    """Verify that secrets are masked in __repr__ and stored as SecretStr."""
    api_key = "test_key"
    api_secret = "test_secret"
    token = "test_token"
    
    manager = BearerTokenManager(api_key, api_secret, http_client, mock_logger, pre_supplied_token=token)
    
    # Check internal storage
    assert isinstance(manager._api_key, SecretStr)
    assert isinstance(manager._api_secret, SecretStr)
    assert isinstance(manager._token, SecretStr)
    
    # Check __repr__ masking
    repr_str = repr(manager)
    assert api_key not in repr_str
    assert api_secret not in repr_str
    assert token not in repr_str
    assert "api_key=<masked>" in repr_str
    assert "api_secret=<masked>" in repr_str


@pytest.mark.asyncio
@respx.mock
async def test_bearer_token_fetch_success(mock_logger, http_client):
    """Verify successful token fetch from correct URL."""
    api_key = "key"
    api_secret = "secret"
    
    # Mock the new URL
    route = respx.post("https://api.x.com/oauth2/token").mock(
        return_value=Response(200, json={"access_token": "new_token"})
    )
    
    manager = BearerTokenManager(api_key, api_secret, http_client, mock_logger)
    token = await manager.get()
    
    assert token == "new_token"
    assert isinstance(manager._token, SecretStr)
    assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_bearer_token_fetch_missing_token(mock_logger, http_client):
    """Verify error raised when response lacks access_token."""
    respx.post("https://api.x.com/oauth2/token").mock(
        return_value=Response(200, json={"other_field": "value"})
    )
    
    manager = BearerTokenManager("k", "s", http_client, mock_logger)
    
    with pytest.raises(AuthenticationError) as exc:
        await manager.get()
    
    assert "No valid access_token received" in str(exc.value)


@pytest.mark.asyncio
@respx.mock
async def test_bearer_token_fetch_http_error(mock_logger, http_client):
    """Verify HTTP errors are caught and wrapped."""
    respx.post("https://api.x.com/oauth2/token").mock(
        return_value=Response(500)
    )
    
    manager = BearerTokenManager("k", "s", http_client, mock_logger)
    
    with pytest.raises(AuthenticationError) as exc:
        await manager.get()
    
    assert "Failed to fetch X bearer token" in str(exc.value)