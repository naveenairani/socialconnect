import logging

import pytest
import respx
from httpx import AsyncClient, Response
from pydantic import SecretStr

from socialconnector.core.exceptions import AuthenticationError, RateLimitError
from socialconnector.core.models import AdapterConfig, Tweet
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
    respx.post("https://api.x.com/2/media/upload").mock(
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
    respx.get("https://api.x.com/2/dm_conversations/conv789/dm_events?dm_event.fields=id,text,sender_id,created_at,dm_conversation_id,event_type,participant_ids&max_results=50").mock(
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

    filtered = await adapter.get_messages(chat_id="conv789")
    assert len(filtered) == 2

    respx.get("https://api.x.com/2/dm_conversations/nonexistent/dm_events?dm_event.fields=id,text,sender_id,created_at,dm_conversation_id,event_type,participant_ids&max_results=50").mock(
        return_value=Response(200, json={"data": []})
    )
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


@pytest.mark.asyncio
@respx.mock
async def test_rate_limit_error_no_body_leak(x_config, mock_logger, http_client):
    """Verify Issue #3: Rate limit errors don't leak response body."""
    respx.get("https://api.x.com/2/tweets/1").mock(
        return_value=Response(429, text="Sensitive body content", headers={"x-rate-limit-reset": "1234567890"})
    )
    adapter = XAdapter(x_config, http_client, mock_logger)
    with pytest.raises(RateLimitError) as exc:
        await adapter._request("GET", "tweets/1")

    assert "Sensitive body content" not in str(exc.value)
    assert "X rate limit hit" in str(exc.value)


@pytest.mark.asyncio
@respx.mock
async def test_validate_path_param_rejects_invalid(x_config, mock_logger, http_client):
    """Verify Issue #2: Malicious path parameters are rejected."""
    from socialconnector.core.exceptions import SocialConnectorError
    adapter = XAdapter(x_config, http_client, mock_logger)

    with pytest.raises(SocialConnectorError) as exc:
        await adapter.get_user_info("../../etc/passwd")
    assert "Invalid path parameter" in str(exc.value)


@pytest.mark.asyncio
async def test_adapter_config_empty_api_key_rejected():
    """Verify Issue #2: Empty configuration fields are rejected by Pydantic."""
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        AdapterConfig(provider="x", api_key="  ")


@pytest.mark.asyncio
@respx.mock
async def test_media_polling_max_attempts(x_config, mock_logger, http_client):
    """Verify Issue #5: Media polling terminates after max attempts."""
    from socialconnector.core.exceptions import MediaError
    # Mock STATUS returning in_progress forever
    respx.get("https://api.x.com/2/media/upload?command=STATUS&media_id=m1").mock(
        return_value=Response(200, json={"data": {"processing_info": {"state": "in_progress", "check_after_secs": 0}}})
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    # We lower MAX_POLL_ATTEMPTS for the test to be fast
    adapter.MAX_POLL_ATTEMPTS = 2

    with pytest.raises(MediaError) as exc:
        await adapter._poll_media_status("m1", {"state": "in_progress", "check_after_secs": 0})
    assert "polling exceeded max attempts" in str(exc.value)


@pytest.mark.asyncio
@respx.mock
async def test_bearer_token_expiry_refresh(mock_logger, http_client):
    """Verify Issue #8: Expired tokens are refreshed."""
    import time

    config = AdapterConfig(provider="x", api_key="k", api_secret="s")
    # Mocking first fetch
    respx.post("https://api.x.com/oauth2/token").mock(
        return_value=Response(200, json={"access_token": "token1", "expires_in": 3600})
    )

    adapter = XAdapter(config, http_client, mock_logger)
    await adapter.bearer_token_manager.get()
    assert adapter.bearer_token_manager.cached_token == "token1"

    # Mocking second fetch
    respx.post("https://api.x.com/oauth2/token").mock(
        return_value=Response(200, json={"access_token": "token2", "expires_in": 3600})
    )

    # Manually expire the token
    adapter.bearer_token_manager._fetched_at = time.time() - 4000

    token = await adapter.bearer_token_manager.get()
    assert token == "token2"


@pytest.mark.asyncio
@respx.mock
async def test_compliance_upload_rejects_ssrf_url(x_config, mock_logger, http_client):
    """Verify Issue #9: SSRF attempts in compliance URLs are blocked."""
    from socialconnector.core.exceptions import SocialConnectorError
    adapter = XAdapter(x_config, http_client, mock_logger)

    with pytest.raises(SocialConnectorError) as exc:
        await adapter.upload_compliance_ids("http://169.254.169.254/latest/meta-data/", "dummy.txt")
    assert "Insecure protocol" in str(exc.value) or "Blocked untrusted" in str(exc.value)


@pytest.mark.asyncio
@respx.mock
async def test_compliance_upload_rejects_path_traversal(x_config, mock_logger, http_client):
    """Verify Issue #10: Path traversal in compliance file paths is blocked."""
    from socialconnector.core.exceptions import SocialConnectorError
    adapter = XAdapter(x_config, http_client, mock_logger)

    with pytest.raises(SocialConnectorError) as exc:
        # Avoid path traversal (test against a likely forbidden path)
        await adapter.upload_compliance_ids("https://api.x.com", "../../windows/system32/drivers/etc/hosts")
    assert "Path traversal detected" in str(exc.value)


@pytest.mark.asyncio
@respx.mock
async def test_auth_error_no_stack_leak(x_config, mock_logger, http_client):
    """Verify Issue #3: Auth errors don't leak raw exception details in message."""
    # Mock users/me returning something that causes a generic Exception
    respx.get("https://api.x.com/2/users/me").mock(return_value=Response(500))

    adapter = XAdapter(x_config, http_client, mock_logger)
    with pytest.raises(AuthenticationError) as exc:
        await adapter.connect()

    # Message should be generic
    assert str(exc.value) == "X authentication failed. Please check your credentials."


@pytest.mark.asyncio
@respx.mock
async def test_x_search_written_notes_success(x_config, http_client, mock_logger):
    """Test that search_written_notes correctly paginates and returns CommunityNote objects."""
    respx.get("https://api.x.com/2/notes/search/notes_written").mock(
        return_value=Response(
            200,
            json={
                "data": [
                    {"id": "note1", "text": "Content 1", "note_id": "N1"},
                    {"id": "note2", "text": "Content 2", "note_id": "N2"},
                ],
                "meta": {"next_token": "token_next", "result_count": 2},
            },
        )
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    result = await adapter.search_written_notes(limit=2)

    assert result.result_count == 2
    assert len(result.data) == 2
    assert result.data[0].id == "note1"
    assert result.data[1].id == "note2"
    assert result.next_token == "token_next"


@pytest.mark.asyncio
@respx.mock
async def test_x_search_written_notes_params(x_config, http_client, mock_logger):
    """Verify that params like test_mode and note_fields are correctly passed."""
    route = respx.get(
        "https://api.x.com/2/notes/search/notes_written",
        params={"test_mode": "true", "note.fields": "text,created_at"},
    ).mock(return_value=Response(200, json={"data": [], "meta": {"result_count": 0}}))

    adapter = XAdapter(x_config, http_client, mock_logger)
    await adapter.search_written_notes(test_mode=True, note_fields=["text", "created_at"])

    assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_x_create_note_success(x_config, http_client, mock_logger):
    """Test that create_note correctly posts and returns a CommunityNote."""
    respx.post("https://api.x.com/2/notes").mock(
        return_value=Response(201, json={"data": {"id": "note123", "text": "New note"}})
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    note = await adapter.create_note("New note")

    assert note.id == "note123"
    assert note.text == "New note"


@pytest.mark.asyncio
@respx.mock
async def test_x_evaluate_note_success(x_config, http_client, mock_logger):
    """Test that evaluate_note correctly posts rating."""
    respx.post("https://api.x.com/2/evaluate_note").mock(
        return_value=Response(200, json={"data": {"success": True}})
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    success = await adapter.evaluate_note("note123", helpful=True, rating="helpful")

    assert success is True


@pytest.mark.asyncio
@respx.mock
async def test_x_search_eligible_posts_success(x_config, http_client, mock_logger):
    """Test that search_eligible_posts returns Tweet objects."""
    respx.get("https://api.x.com/2/notes/search/posts_eligible_for_notes").mock(
        return_value=Response(
            200,
            json={
                "data": [
                    {"id": "t1", "text": "Post 1", "author_id": "u1"},
                    {"id": "t2", "text": "Post 2", "author_id": "u2"},
                ],
                "meta": {"result_count": 2},
            },
        )
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    result = await adapter.search_eligible_posts(test_mode=True)

    assert result.result_count == 2
    assert len(result.data) == 2
    assert isinstance(result.data[0], Tweet)
    assert result.data[1].id == "t2"


@pytest.mark.asyncio
@respx.mock
async def test_x_delete_note_success(x_config, http_client, mock_logger):
    """Test that delete_note correctly calls DELETE."""
    respx.delete("https://api.x.com/2/notes/note123").mock(
        return_value=Response(200, json={"data": {"deleted": True}})
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    response = await adapter.delete_note("note123")

    assert response.success is True





