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
    from socialconnector.core.models import CreateJobsRequest
    req = CreateJobsRequest(type="tweets", name="test_job")
    job = await adapter.create_compliance_job(body=req)
    assert job.data.id == "job123"
    assert job.data.upload_url == "https://upload.example.com"


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
    assert len(jobs.data) == 2
    assert jobs.data[0].id == "job1"


@pytest.mark.asyncio
@respx.mock
async def test_x_get_compliance_job(x_config, http_client, mock_logger):
    respx.get("https://api.x.com/2/compliance/jobs/job123").mock(
        return_value=Response(200, json={"data": {"id": "job123", "status": "complete"}})
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    job = await adapter.get_compliance_job("job123")
    assert job.data.id == "job123"
    assert job.data.status == "complete"


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


@pytest.mark.asyncio
@respx.mock
async def test_x_validate_subscription_success(x_config, http_client, mock_logger):
    """Test that validate_subscription correctly calls GET."""
    respx.get("https://api.x.com/2/account_activity/webhooks/webhook_123/subscriptions/all").mock(
        return_value=Response(200, json={"data": {"subscribed": True}})
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    response = await adapter.validate_subscription("webhook_123")

    assert response.data.subscribed is True


@pytest.mark.asyncio
@respx.mock
async def test_x_create_subscription_success(x_config, http_client, mock_logger):
    """Test that create_subscription correctly calls POST."""
    from socialconnector.core.models import CreateSubscriptionRequest

    respx.post("https://api.x.com/2/account_activity/webhooks/webhook_123/subscriptions/all").mock(
        return_value=Response(201, json={"data": {"subscribed": True}})
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    req = CreateSubscriptionRequest()
    response = await adapter.create_subscription("webhook_123", body=req)

    assert response.data.subscribed is True


@pytest.mark.asyncio
@respx.mock
async def test_x_get_subscriptions_success(x_config, http_client, mock_logger):
    """Test that get_subscriptions correctly calls GET."""
    respx.get("https://api.x.com/2/account_activity/webhooks/webhook_123/subscriptions/all/list").mock(
        return_value=Response(
            200,
            json={
                "data": {
                    "application_id": "app_123",
                    "webhook_id": "webhook_123",
                    "webhook_url": "https://example.com/webhook",
                    "subscriptions": [{"user_id": "user_456"}],
                }
            },
        )
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    response = await adapter.get_subscriptions("webhook_123")

    assert response.data.application_id == "app_123"
    assert len(response.data.subscriptions) == 1
    assert response.data.subscriptions[0]["user_id"] == "user_456"


@pytest.mark.asyncio
@respx.mock
async def test_x_delete_subscription_success(x_config, http_client, mock_logger):
    """Test that delete_subscription correctly calls DELETE."""
    respx.delete("https://api.x.com/2/account_activity/webhooks/webhook_123/subscriptions/user_456/all").mock(
        return_value=Response(200, json={"data": {"subscribed": False}})
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    response = await adapter.delete_subscription("webhook_123", "user_456")

    assert response.data.subscribed is False


@pytest.mark.asyncio
@respx.mock
async def test_x_get_subscription_count_success(x_config, http_client, mock_logger):
    """Test that get_subscription_count correctly calls GET."""
    respx.get("https://api.x.com/2/account_activity/subscriptions/count").mock(
        return_value=Response(
            200,
            json={
                "data": {
                    "account_name": "AcmeCorp",
                    "subscriptions_count_all": "100",
                    "provisioned_count": "500",
                    "subscriptions_count_direct_messages": "50",
                }
            },
        )
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    response = await adapter.get_subscription_count()

    assert response.data.account_name == "AcmeCorp"
    assert response.data.subscriptions_count_all == "100"


@pytest.mark.asyncio
@respx.mock
async def test_x_create_replay_job_success(x_config, http_client, mock_logger):
    """Test that create_replay_job correctly calls POST with parameters."""
    route = respx.post("https://api.x.com/2/account_activity/replay/webhooks/webhook_123/subscriptions/all").mock(
        return_value=Response(201, json={"job_id": "replay_job_999", "created_at": "2023-10-27T12:00:00Z"})
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    response = await adapter.create_replay_job("webhook_123", "202310221200", "202310271200")

    assert response.job_id == "replay_job_999"
    assert route.called
    assert "from_date=202310221200" in str(route.calls.last.request.url)
@pytest.mark.asyncio
@respx.mock
async def test_x_chat_send_message_success(x_config, http_client, mock_logger):
    """Test that send_message correctly calls POST and returns the response."""
    from socialconnector.core.models import SendMessageRequest

    route = respx.post("https://api.x.com/2/chat/conversations/conv-123/messages").mock(
        return_value=Response(201, json={"data": {"encoded_message_event": "encoded_test_data"}})
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    req = SendMessageRequest(encoded_message_create_event="event_data", message_id="msg-123")
    response = await adapter.send_message("conv-123", body=req)

    assert route.called
    assert response.data.encoded_message_event == "encoded_test_data"


@pytest.mark.asyncio
@respx.mock
async def test_x_chat_get_conversation_success(x_config, http_client, mock_logger):
    """Test that get_conversation correctly calls GET and paginates."""
    route1 = respx.get("https://api.x.com/2/chat/conversations/conv-123?max_results=10").mock(
        return_value=Response(
            200,
            json={
                "data": [{"id": "msg-1", "text": "hello"}],
                "meta": {"next_token": "token-123", "result_count": 1}
            }
        )
    )

    route2 = respx.get("https://api.x.com/2/chat/conversations/conv-123?max_results=10&pagination_token=token-123").mock(
        return_value=Response(
            200,
            json={
                "data": [{"id": "msg-2", "text": "world"}],
                "meta": {"result_count": 1}
            }
        )
    )

    adapter = XAdapter(x_config, http_client, mock_logger)

    pages = []
    async for page in adapter.get_conversation("conv-123", max_results=10):
        pages.append(page)

    assert len(pages) == 2
    assert route1.called
    assert route2.called
    assert pages[0].data[0]["id"] == "msg-1"
    assert pages[1].data[0]["id"] == "msg-2"


@pytest.mark.asyncio
@respx.mock
async def test_x_chat_get_user_public_keys_success(x_config, http_client, mock_logger):
    """Test get_user_public_keys correctly queries public keys."""
    route = respx.get("https://api.x.com/2/users/user-123/public_keys").mock(
        return_value=Response(200, json={"data": [{"public_key": "pub_key_test"}]})
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    response = await adapter.get_user_public_keys("user-123")

    assert route.called
    assert response.data[0]["public_key"] == "pub_key_test"


@pytest.mark.asyncio
@respx.mock
async def test_x_chat_add_user_public_key_success(x_config, http_client, mock_logger):
    """Test add_user_public_key calls POST."""
    from socialconnector.core.models import AddUserPublicKeyRequest

    route = respx.post("https://api.x.com/2/users/user-123/public_keys").mock(
        return_value=Response(201, json={"data": {"version": "1.0", "error_code": None}})
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    req = AddUserPublicKeyRequest(public_key="my_new_key", version="1.0")
    response = await adapter.add_user_public_key("user-123", body=req)

    assert route.called
    assert response.data.version == "1.0"


@pytest.mark.asyncio
@respx.mock
async def test_x_chat_get_conversations_success(x_config, http_client, mock_logger):
    """Test that get_conversations correctly calls GET."""
    route = respx.get("https://api.x.com/2/chat/conversations?max_results=50").mock(
        return_value=Response(
            200,
            json={
                "data": [{"conversation_id": "conv-1", "type": "GROUP"}],
                "meta": {"result_count": 1}
            }
        )
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    pages = []
    async for page in adapter.get_conversations(max_results=50):
        pages.append(page)

    assert route.called
    assert len(pages) == 1
@pytest.mark.asyncio
@respx.mock
async def test_x_communities_get_by_id_success(x_config, http_client, mock_logger):
    """Test that get_community_by_id correctly calls GET and returns the response."""
    route = respx.get("https://api.x.com/2/communities/comm-123").mock(
        return_value=Response(
            200,
            json={
                "data": {"id": "comm-123", "name": "Python Developers", "created_at": "2023-01-01T00:00:00.000Z"}
            }
        )
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    response = await adapter.get_community_by_id("comm-123", community_fields=["name", "created_at"])

    assert route.called
    assert "community.fields=name%2Ccreated_at" in str(route.calls.last.request.url)
    assert response.data.id == "comm-123"
    assert response.data.name == "Python Developers"


@pytest.mark.asyncio
@respx.mock
async def test_x_communities_search_success(x_config, http_client, mock_logger):
    """Test that search_communities correctly calls GET and paginates."""
    route1 = respx.get("https://api.x.com/2/communities/search?query=programming&max_results=10").mock(
        return_value=Response(
            200,
            json={
                "data": [{"id": "comm-1", "name": "Python"}],
                "meta": {"next_token": "token-123"}
            }
        )
    )

    route2 = respx.get("https://api.x.com/2/communities/search?query=programming&max_results=10&pagination_token=token-123").mock(
        return_value=Response(
            200,
            json={
                "data": [{"id": "comm-2", "name": "JavaScript"}],
                "meta": {}
            }
        )
    )

    adapter = XAdapter(x_config, http_client, mock_logger)

    pages = []
    async for page in adapter.search_communities("programming", max_results=10):
        pages.append(page)

    assert len(pages) == 2
    assert route1.called
    assert route2.called
    assert pages[0].data[0]["id"] == "comm-1"
    assert pages[1].data[0]["id"] == "comm-2"


@pytest.mark.asyncio
@respx.mock
async def test_x_update_subscription_success(x_config, http_client, mock_logger):
    """Test that update_subscription correctly calls PUT."""
    from socialconnector.core.models import UpdateSubscriptionRequest

    respx.put("https://api.x.com/2/activity/subscriptions/sub_123").mock(
        return_value=Response(200, json={"data": {"subscribed": True}})
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    req = UpdateSubscriptionRequest()
    response = await adapter.update_subscription("sub_123", body=req)

    assert response.data.subscribed is True


@pytest.mark.asyncio
@respx.mock
async def test_x_create_activity_subscription_success(x_config, http_client, mock_logger):
    """Test that create_activity_subscription correctly calls POST on activity/subscriptions."""
    from socialconnector.core.models import CreateSubscriptionRequest

    respx.post("https://api.x.com/2/activity/subscriptions").mock(
        return_value=Response(200, json={"data": {"subscribed": True}})
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    req = CreateSubscriptionRequest()
    response = await adapter.create_activity_subscription(body=req)

    assert response.data.subscribed is True


@pytest.mark.asyncio
@respx.mock
async def test_x_delete_activity_subscription_success(x_config, http_client, mock_logger):
    """Test that delete_activity_subscription correctly calls DELETE on activity/subscriptions."""
    respx.delete("https://api.x.com/2/activity/subscriptions/sub_456").mock(
        return_value=Response(200, json={"data": {"subscribed": False}})
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    response = await adapter.delete_activity_subscription("sub_456")

    assert response.data.subscribed is False


@pytest.mark.asyncio
@respx.mock
async def test_x_get_activity_subscriptions_success(x_config, http_client, mock_logger):
    """Test that get_activity_subscriptions correctly paginates and calls GET on activity/subscriptions."""
    respx.get("https://api.x.com/2/activity/subscriptions").mock(
        side_effect=[
            Response(
                200,
                json={
                    "data": {"application_id": "app_1", "subscriptions": [{"id": "sub_1"}]},
                    "meta": {"next_token": "token_1"}
                }
            ),
            Response(
                200,
                json={
                    "data": {"application_id": "app_1", "subscriptions": [{"id": "sub_2"}]}
                }
            ),
        ]
    )

    adapter = XAdapter(x_config, http_client, mock_logger)

    pages = []
    async for page in adapter.get_activity_subscriptions(max_results=1):
        pages.append(page)

    assert len(pages) == 2
    assert pages[0].meta.next_token == "token_1"
    assert pages[1].meta is None


@pytest.mark.asyncio
async def test_x_activity_stream_success(x_config, http_client, mock_logger):
    """Test that stream correctly yields StreamResponse objects using stream_with_retry."""
    import json

    from socialconnector.core.models import StreamResponse

    # Note: respx doesn't easily mock async streams using stream_with_retry,
    # so we mock httpx.AsyncClient.stream instead
    class MockStreamContext:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

        @property
        def status_code(self):
            return 200

        async def aiter_text(self):
            yield json.dumps({"data": {"id": "act_1", "text": "Activity 1"}}) + "\n"
            yield json.dumps({"data": {"id": "act_2", "text": "Activity 2"}}) + "\n"

    adapter = XAdapter(x_config, http_client, mock_logger)
    adapter._last_request_time = 0  # disable rate limits

    # Mock token method
    async def mock_get_token():
        return "mock_token"
    adapter.bearer_token_manager.get = mock_get_token

    # Mock the actual stream method from http_client
    adapter.http_client.stream = lambda *args, **kwargs: MockStreamContext()


    events = []
    async for event in adapter.stream(backfill_minutes=5):
        events.append(event)
        if len(events) == 2:
            break

    assert len(events) == 2
    assert isinstance(events[0], StreamResponse)
    assert isinstance(events[0], StreamResponse)
    assert events[0].data["id"] == "act_1"
    assert events[1].data["id"] == "act_2"


@pytest.mark.asyncio
@respx.mock
async def test_x_create_compliance_job_success(x_config, http_client, mock_logger):
    """Test creating a compliance job returning Pydantic model."""
    from socialconnector.core.models import CreateJobsRequest

    respx.post("https://api.x.com/2/compliance/jobs").mock(
        return_value=Response(
            201,
            json={"data": {"id": "job_123", "type": "tweets", "name": "Test Job"}}
        )
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    req = CreateJobsRequest(type="tweets", name="Test Job")
    response = await adapter.create_compliance_job(body=req)

    assert response.data.id == "job_123"
    assert response.data.type == "tweets"
    assert response.data.name == "Test Job"


@pytest.mark.asyncio
@respx.mock
async def test_x_get_compliance_job_success(x_config, http_client, mock_logger):
    """Test getting a compliance job returning Pydantic model."""
    respx.get("https://api.x.com/2/compliance/jobs/job_123").mock(
        return_value=Response(
            200,
            json={"data": {"id": "job_123", "type": "tweets", "status": "in_progress"}}
        )
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    response = await adapter.get_compliance_job("job_123")

    assert response.data.id == "job_123"
    assert response.data.status == "in_progress"


@pytest.mark.asyncio
@respx.mock
async def test_x_list_compliance_jobs_success(x_config, http_client, mock_logger):
    """Test listing compliance jobs returning Pydantic model."""
    respx.get("https://api.x.com/2/compliance/jobs?type=users").mock(
        return_value=Response(
            200,
            json={
                "data": [
                    {"id": "job_1", "type": "users"},
                    {"id": "job_2", "type": "users"}
                ]
            }
        )
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    response = await adapter.list_compliance_jobs(type="users")

    assert len(response.data) == 2
    assert response.data[0].id == "job_1"
    assert response.data[1].id == "job_2"


@pytest.mark.asyncio
@respx.mock
async def test_x_get_connection_history_success(x_config, http_client, mock_logger):
    """Test get_connection_history returns paginated response and yields objects."""
    respx.get("https://api.x.com/2/connections").mock(
        side_effect=[
            Response(
                200,
                json={
                    "data": [{"id": "conn_1", "status": "active"}],
                    "meta": {"next_token": "token_123"}
                }
            ),
            Response(
                200,
                json={
                    "data": [{"id": "conn_2", "status": "inactive"}]
                }
            ),
        ]
    )

    adapter = XAdapter(x_config, http_client, mock_logger)

    pages = []
    async for page in adapter.get_connection_history(status="all", max_results=10):
        pages.append(page)

    assert len(pages) == 2
    assert pages[0].meta.next_token == "token_123"
    assert pages[0].data[0]["id"] == "conn_1"
    assert pages[1].data[0]["id"] == "conn_2"


@pytest.mark.asyncio
@respx.mock
async def test_x_delete_all_connections_success(x_config, http_client, mock_logger):
    """Test delete_all_connections calls correct route."""
    route = respx.delete("https://api.x.com/2/connections/all").mock(
        return_value=Response(
            200,
            json={"data": {"successful_kills": 5, "failed_kills": 0, "results": []}}
        )
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    response = await adapter.delete_all_connections()

    assert route.called
    assert response.data.successful_kills == 5


@pytest.mark.asyncio
@respx.mock
async def test_x_delete_connections_by_endpoint_success(x_config, http_client, mock_logger):
    """Test delete_connections_by_endpoint calls correct route with ID parameter."""
    route = respx.delete("https://api.x.com/2/connections/endpoint_1").mock(
        return_value=Response(
            200,
            json={"data": {"successful_kills": 2, "failed_kills": 1, "results": []}}
        )
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    response = await adapter.delete_connections_by_endpoint("endpoint_1")

    assert route.called
    assert response.data.successful_kills == 2
    assert response.data.failed_kills == 1


@pytest.mark.asyncio
@respx.mock
async def test_x_delete_connections_by_uuids_success(x_config, http_client, mock_logger):
    """Test delete_connections_by_uuids properly mounts request payloads."""
    from socialconnector.core.models import DeleteByUuidsRequest

    route = respx.delete("https://api.x.com/2/connections").mock(
        return_value=Response(
            200,
            json={"data": {"successful_kills": 3, "failed_kills": 0, "results": []}}
        )
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    req = DeleteByUuidsRequest(uuids=["id_1", "id_2", "id_3"])
    response = await adapter.delete_connections_by_uuids(req)

    assert route.called
    assert response.data.successful_kills == 3


@pytest.mark.asyncio
@respx.mock
async def test_x_dms_get_events_by_participant_id(x_config, http_client, mock_logger):
    pid = "participant_123"
    respx.get(f"https://api.x.com/2/dm_conversations/with/{pid}/dm_events").mock(
        return_value=Response(
            200,
            json={
                "data": [
                    {
                        "id": "e1",
                        "text": "msg1",
                        "sender_id": "participant_123",
                        "created_at": "2023-01-01T00:00:00Z",
                        "dm_conversation_id": "conv456",
                    }
                ]
            },
        )
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    count = 0
    async for page in adapter.get_events_by_participant_id(pid, max_results=50):
        assert page.data and len(page.data) == 1
        assert page.data[0]["text"] == "msg1"
        count += 1
    assert count == 1


@pytest.mark.asyncio
@respx.mock
async def test_x_dms_get_events_by_conversation_id(x_config, http_client, mock_logger):
    conv_id = "conv456"
    respx.get(f"https://api.x.com/2/dm_conversations/{conv_id}/dm_events").mock(
        return_value=Response(
            200,
            json={
                "data": [
                    {
                        "id": "e2",
                        "text": "msg2",
                        "sender_id": "participant_456",
                    }
                ]
            },
        )
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    count = 0
    async for page in adapter.get_events_by_conversation_id(conv_id, max_results=50):
        assert page.data and len(page.data) == 1
        assert page.data[0]["text"] == "msg2"
        count += 1
    assert count == 1


@pytest.mark.asyncio
@respx.mock
async def test_x_dms_get_events_by_id(x_config, http_client, mock_logger):
    eid = "e2"
    respx.get(f"https://api.x.com/2/dm_events/{eid}").mock(
        return_value=Response(
            200,
            json={
                "data": {
                    "id": "e2",
                    "text": "msg2",
                    "sender_id": "participant_456",
                }
            },
        )
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    res = await adapter.get_events_by_id(eid)
    assert res.data and res.data.id == "e2"
    assert res.data.text == "msg2"


@pytest.mark.asyncio
@respx.mock
async def test_x_dms_delete_events(x_config, http_client, mock_logger):
    eid = "e2"
    respx.delete(f"https://api.x.com/2/dm_events/{eid}").mock(
        return_value=Response(200, json={"data": {"deleted": True}})
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    res = await adapter.delete_events(eid)
    assert res.data and res.data.deleted is True


@pytest.mark.asyncio
@respx.mock
async def test_x_dms_create_conversation(x_config, http_client, mock_logger):
    respx.post("https://api.x.com/2/dm_conversations").mock(
        return_value=Response(201, json={"data": {"dm_conversation_id": "conv456", "dm_event_id": "e1"}})
    )

    from socialconnector.core.models import CreateConversationRequest

    adapter = XAdapter(x_config, http_client, mock_logger)
    req = CreateConversationRequest(conversation_type="Group", message="Hello", participant_ids="111,222")
    res = await adapter.create_conversation(req)
    assert res.data and res.data.dm_conversation_id == "conv456"
    assert res.data.dm_event_id == "e1"


@pytest.mark.asyncio
@respx.mock
async def test_x_dms_create_by_conversation_id(x_config, http_client, mock_logger):
    conv_id = "conv_123"
    respx.post(f"https://api.x.com/2/dm_conversations/{conv_id}/messages").mock(
        return_value=Response(201, json={"data": {"dm_conversation_id": conv_id, "dm_event_id": "e1"}})
    )

    from socialconnector.core.models import CreateByConversationIdRequest

    adapter = XAdapter(x_config, http_client, mock_logger)
    req = CreateByConversationIdRequest(text="Hello again")
    res = await adapter.create_by_conversation_id(conv_id, req)
    assert res.data and res.data.dm_conversation_id == conv_id
    assert res.data.dm_event_id == "e1"


@pytest.mark.asyncio
@respx.mock
async def test_x_dms_create_by_participant_id(x_config, http_client, mock_logger):
    pid = "part_123"
    respx.post(f"https://api.x.com/2/dm_conversations/with/{pid}/messages").mock(
        return_value=Response(201, json={"data": {"dm_conversation_id": "conv_456", "dm_event_id": "e1"}})
    )

    from socialconnector.core.models import CreateByParticipantIdRequest

    adapter = XAdapter(x_config, http_client, mock_logger)
    req = CreateByParticipantIdRequest(text="Hello again")
    res = await adapter.create_by_participant_id(pid, req)
    assert res.data and res.data.dm_conversation_id == "conv_456"
    assert res.data.dm_event_id == "e1"


@pytest.mark.asyncio
@respx.mock
async def test_x_dms_get_events(x_config, http_client, mock_logger):
    respx.get("https://api.x.com/2/dm_events").mock(
        return_value=Response(
            200,
            json={
                "data": [
                    {
                        "id": "e2",
                        "text": "msg2",
                        "sender_id": "participant_456",
                    }
                ]
            },
        )
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    count = 0
    async for page in adapter.get_events(max_results=50):
        assert page.data and len(page.data) == 1
        assert page.data[0]["text"] == "msg2"
        count += 1
    assert count == 1


@pytest.mark.asyncio
@respx.mock
async def test_x_general_get_open_api_spec(x_config, http_client, mock_logger):
    respx.get("https://api.x.com/2/openapi.json").mock(
        return_value=Response(
            200,
            json={
                "openapi": "3.0.0",
                "info": {"title": "X API v2", "version": "2.0"},
                "paths": {},
            },
        )
    )
    adapter = XAdapter(x_config, http_client, mock_logger)
    res = await adapter.get_open_api_spec()
    assert getattr(res, "openapi", None) == "3.0.0" or res.model_dump().get("openapi") == "3.0.0"


# ── get_list_followers tests ─────────────────────────────────────────────────


@pytest.mark.asyncio
@respx.mock
async def test_get_list_followers_basic(x_config, http_client, mock_logger):
    """Returns followers for a list — single page, no pagination."""
    respx.get("https://api.x.com/2/lists/list123/followers").mock(
        return_value=Response(
            200,
            json={
                "data": [
                    {"id": "u1", "name": "Alice", "username": "alice"},
                    {"id": "u2", "name": "Bob",   "username": "bob"},
                ],
                "meta": {"result_count": 2},
            },
        )
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    result = await adapter.get_list_followers("list123")

    assert result.result_count == 2
    assert result.data[0]["id"] == "u1"
    assert result.data[1]["username"] == "bob"
    assert result.next_token is None


@pytest.mark.asyncio
@respx.mock
async def test_get_list_followers_pagination(x_config, http_client, mock_logger):
    """Automatically follows next_token across two pages."""
    pages = [
        {
            "data": [{"id": "u1", "name": "Alice", "username": "alice"}],
            "meta": {"result_count": 1, "next_token": "tok_page2"},
        },
        {
            "data": [{"id": "u2", "name": "Bob", "username": "bob"}],
            "meta": {"result_count": 1},
        },
    ]
    call_count = 0

    def side_effect(request):
        nonlocal call_count
        data = pages[min(call_count, len(pages) - 1)]
        call_count += 1
        return Response(200, json=data)

    respx.get("https://api.x.com/2/lists/list456/followers").mock(side_effect=side_effect)

    adapter = XAdapter(x_config, http_client, mock_logger)
    result = await adapter.get_list_followers("list456", limit=200)

    assert len(result.data) == 2
    assert result.data[0]["id"] == "u1"
    assert result.data[1]["id"] == "u2"
    assert call_count == 2


@pytest.mark.asyncio
@respx.mock
async def test_get_list_followers_invalid_list_id(x_config, http_client, mock_logger):
    """Rejects malicious / traversal list IDs before making any HTTP call."""
    from socialconnector.core.exceptions import SocialConnectorError

    adapter = XAdapter(x_config, http_client, mock_logger)

    with pytest.raises(SocialConnectorError) as exc:
        await adapter.get_list_followers("../../etc/passwd")

    assert "Invalid path parameter" in str(exc.value)


# ── get_list_tweets tests ────────────────────────────────────────────────────


@pytest.mark.asyncio
@respx.mock
async def test_get_list_tweets_basic(x_config, http_client, mock_logger):
    """Returns tweets for a list — single page, no pagination."""
    respx.get("https://api.x.com/2/lists/list789/tweets").mock(
        return_value=Response(
            200,
            json={
                "data": [
                    {"id": "t1", "text": "Hello world", "author_id": "u1"},
                    {"id": "t2", "text": "Second tweet", "author_id": "u2"},
                ],
                "meta": {"result_count": 2},
            },
        )
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    result = await adapter.get_list_tweets("list789")

    assert result.result_count == 2
    assert result.data[0]["id"] == "t1"
    assert result.data[1]["text"] == "Second tweet"
    assert result.next_token is None


@pytest.mark.asyncio
@respx.mock
async def test_get_list_tweets_field_params(x_config, http_client, mock_logger):
    """Verifies that field params are forwarded correctly to the API."""
    route = respx.get(
        "https://api.x.com/2/lists/list789/tweets",
        params={
            "tweet.fields": "created_at,public_metrics",
            "expansions": "author_id",
            "user.fields": "name,username",
            "max_results": 100,
        },
    ).mock(
        return_value=Response(
            200,
            json={"data": [{"id": "t1", "text": "Hi"}], "meta": {"result_count": 1}},
        )
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    await adapter.get_list_tweets(
        "list789",
        tweet_fields=["created_at", "public_metrics"],
        expansions=["author_id"],
        user_fields=["name", "username"],
    )

    assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_get_list_tweets_invalid_list_id(x_config, http_client, mock_logger):
    """Rejects malicious / traversal list IDs before making any HTTP call."""
    from socialconnector.core.exceptions import SocialConnectorError

    adapter = XAdapter(x_config, http_client, mock_logger)

    with pytest.raises(SocialConnectorError) as exc:
        await adapter.get_list_tweets("../../etc/passwd")

    assert "Invalid path parameter" in str(exc.value)


# ── get_list_by_id tests ─────────────────────────────────────────────────────


@pytest.mark.asyncio
@respx.mock
async def test_get_list_by_id_basic(x_config, http_client, mock_logger):
    """Returns list metadata by ID."""
    respx.get("https://api.x.com/2/lists/list123").mock(
        return_value=Response(
            200,
            json={
                "data": {
                    "id": "list123",
                    "name": "My List",
                    "owner_id": "u1",
                    "private": False,
                }
            },
        )
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    result = await adapter.get_list_by_id("list123")

    assert result["data"]["id"] == "list123"
    assert result["data"]["name"] == "My List"


@pytest.mark.asyncio
@respx.mock
async def test_get_list_by_id_invalid_id(x_config, http_client, mock_logger):
    """Rejects malicious list IDs before making any HTTP call."""
    from socialconnector.core.exceptions import SocialConnectorError

    adapter = XAdapter(x_config, http_client, mock_logger)

    with pytest.raises(SocialConnectorError) as exc:
        await adapter.get_list_by_id("../../etc/passwd")

    assert "Invalid path parameter" in str(exc.value)


# ── update_list tests ────────────────────────────────────────────────────────


@pytest.mark.asyncio
@respx.mock
async def test_update_list_basic(x_config, http_client, mock_logger):
    """Updates list metadata successfully."""
    route = respx.put("https://api.x.com/2/lists/list123").mock(
        return_value=Response(200, json={"data": {"updated": True}})
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    result = await adapter.update_list(
        "list123", name="New Name", description="Updated description", private=True
    )

    import json
    assert result is True
    assert route.called
    req_json = json.loads(route.calls[0].request.content)
    assert req_json["name"] == "New Name"
    assert req_json["description"] == "Updated description"
    assert req_json["private"] is True


@pytest.mark.asyncio
@respx.mock
async def test_update_list_invalid_id(x_config, http_client, mock_logger):
    """Rejects malicious list IDs before making any HTTP call."""
    from socialconnector.core.exceptions import SocialConnectorError

    adapter = XAdapter(x_config, http_client, mock_logger)

    with pytest.raises(SocialConnectorError) as exc:
        await adapter.update_list("../../etc/passwd", name="Hack")

    assert "Invalid path parameter" in str(exc.value)


# ── delete_list tests ────────────────────────────────────────────────────────


@pytest.mark.asyncio
@respx.mock
async def test_delete_list_basic(x_config, http_client, mock_logger):
    """Deletes list successfully."""
    route = respx.delete("https://api.x.com/2/lists/list123").mock(
        return_value=Response(200, json={"data": {"deleted": True}})
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    result = await adapter.delete_list("list123")

    assert result is True
    assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_delete_list_invalid_id(x_config, http_client, mock_logger):
    """Rejects malicious list IDs before making any HTTP call."""
    from socialconnector.core.exceptions import SocialConnectorError

    adapter = XAdapter(x_config, http_client, mock_logger)

    with pytest.raises(SocialConnectorError) as exc:
        await adapter.delete_list("../../etc/passwd")

    assert "Invalid path parameter" in str(exc.value)


# ── add_list_member tests ────────────────────────────────────────────────────


@pytest.mark.asyncio
@respx.mock
async def test_add_list_member_basic(x_config, http_client, mock_logger):
    """Adds member to list successfully."""
    route = respx.post("https://api.x.com/2/lists/list123/members").mock(
        return_value=Response(200, json={"data": {"is_member": True}})
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    result = await adapter.add_list_member("list123", "u999")

    assert result is True
    assert route.called

    import json
    req_json = json.loads(route.calls[0].request.content)
    assert req_json["user_id"] == "u999"


@pytest.mark.asyncio
@respx.mock
async def test_add_list_member_invalid_id(x_config, http_client, mock_logger):
    """Rejects malicious list IDs before making any HTTP call."""
    from socialconnector.core.exceptions import SocialConnectorError

    adapter = XAdapter(x_config, http_client, mock_logger)

    with pytest.raises(SocialConnectorError) as exc:
        await adapter.add_list_member("../../etc/passwd", "u999")

    assert "Invalid path parameter" in str(exc.value)


# ── create_list tests ────────────────────────────────────────────────────────


@pytest.mark.asyncio
@respx.mock
async def test_create_list_basic(x_config, http_client, mock_logger):
    """Creates a new list successfully."""
    route = respx.post("https://api.x.com/2/lists").mock(
        return_value=Response(
            200, json={"data": {"id": "list123", "name": "New List"}}
        )
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    result = await adapter.create_list("New List", description="My desc", private=True)

    assert result["id"] == "list123"
    assert result["name"] == "New List"
    assert route.called

    import json
    req_json = json.loads(route.calls[0].request.content)
    assert req_json["name"] == "New List"
    assert req_json["description"] == "My desc"
    assert req_json["private"] is True


# ── get_media_by_keys tests ──────────────────────────────────────────────────


@pytest.mark.asyncio
@respx.mock
async def test_get_media_by_keys(x_config, http_client, mock_logger):
    """Retrieves media by keys successfully."""
    route = respx.get("https://api.x.com/2/media").mock(
        return_value=Response(
            200, json={"data": [{"media_key": "3_12345", "type": "photo"}]}
        )
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    result = await adapter.get_media_by_keys(["3_12345", "3_67890"], media_fields=["type", "url"])

    assert result["data"][0]["media_key"] == "3_12345"
    assert route.called

    query = route.calls[0].request.url.query.decode("utf-8")
    assert "media_keys=3_12345%2C3_67890" in query
    assert "media.fields=type%2Curl" in query


# ── get_media_analytics tests ────────────────────────────────────────────────


@pytest.mark.asyncio
@respx.mock
async def test_get_media_analytics(x_config, http_client, mock_logger):
    """Retrieves media analytics successfully."""
    route = respx.get("https://api.x.com/2/media/analytics").mock(
        return_value=Response(
            200, json={"data": [{"media_key": "3_12345", "view_count": 100}]}
        )
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    result = await adapter.get_media_analytics(
        ["3_12345"],
        start_time="2023-01-01T00:00:00Z",
        end_time="2023-01-02T00:00:00Z",
        granularity="day",
        media_analytics_fields=["view_count", "engagement"],
    )

    assert result["data"][0]["media_key"] == "3_12345"
    assert route.called

    query = route.calls[0].request.url.query.decode("utf-8")
    assert "media_keys=3_12345" in query
    assert "start_time=2023-01-01T00%3A00%3A00Z" in query
    assert "end_time=2023-01-02T00%3A00%3A00Z" in query
    assert "granularity=day" in query
    assert "media_analytics.fields=view_count%2Cengagement" in query


# ── get_media_by_key tests ───────────────────────────────────────────────────


@pytest.mark.asyncio
@respx.mock
async def test_get_media_by_key_basic(x_config, http_client, mock_logger):
    """Retrieves single media by key successfully."""
    route = respx.get("https://api.x.com/2/media/3_12345").mock(
        return_value=Response(
            200, json={"data": {"media_key": "3_12345", "type": "photo"}}
        )
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    result = await adapter.get_media_by_key("3_12345", media_fields=["type", "url"])

    assert result["data"]["media_key"] == "3_12345"
    assert result["data"]["type"] == "photo"
    assert route.called

    query = route.calls[0].request.url.query.decode("utf-8")
    assert "media.fields=type%2Curl" in query


@pytest.mark.asyncio
@respx.mock
async def test_get_media_by_key_invalid_id(x_config, http_client, mock_logger):
    """Rejects malicious media keys before making any HTTP call."""
    from socialconnector.core.exceptions import SocialConnectorError

    adapter = XAdapter(x_config, http_client, mock_logger)

    with pytest.raises(SocialConnectorError) as exc:
        await adapter.get_media_by_key("../../etc/passwd")

    assert "Invalid path parameter" in str(exc.value)


# ── append_upload tests ──────────────────────────────────────────────────────


@pytest.mark.asyncio
@respx.mock
async def test_append_upload_success(x_config, http_client, mock_logger):
    """Successfully appends media chunk."""
    route = respx.post("https://api.x.com/2/media/upload/3_12345/append").mock(
        return_value=Response(204)
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    result = await adapter.append_upload("3_12345", b"test data", 0)

    assert result is True
    assert route.called

    # Assert form data
    request = route.calls[0].request
    assert b"APPEND" in request.content
    assert b"3_12345" in request.content
    assert b"test data" in request.content


@pytest.mark.asyncio
@respx.mock
async def test_append_upload_error(x_config, http_client, mock_logger):
    """Handles HTTP error during append."""
    respx.post("https://api.x.com/2/media/upload/3_12345/append").mock(
        return_value=Response(400)
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    result = await adapter.append_upload("3_12345", b"test data", 0)

    assert result is False


# ── finalize_upload tests ────────────────────────────────────────────────────


@pytest.mark.asyncio
@respx.mock
async def test_finalize_upload_success(x_config, http_client, mock_logger):
    """Successfully finalizes media upload."""
    route = respx.post("https://api.x.com/2/media/upload/3_12345/finalize").mock(
        return_value=Response(200, json={"data": {"media_id": "3_12345", "processing_info": {"state": "pending"}}})
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    result = await adapter.finalize_upload("3_12345")

    assert result["media_id"] == "3_12345"
    assert result["processing_info"]["state"] == "pending"
    assert route.called

    request = route.calls[0].request
    assert b"command=FINALIZE" in request.content
    assert b"media_id=3_12345" in request.content


@pytest.mark.asyncio
@respx.mock
async def test_finalize_upload_invalid_id(x_config, http_client, mock_logger):
    """Rejects malicious media id."""
    from socialconnector.core.exceptions import SocialConnectorError

    adapter = XAdapter(x_config, http_client, mock_logger)

    with pytest.raises(SocialConnectorError) as exc:
        await adapter.finalize_upload("../../etc/passwd")

    assert "Invalid path parameter" in str(exc.value)


# ── get_upload_status tests ──────────────────────────────────────────────────


@pytest.mark.asyncio
@respx.mock
async def test_get_upload_status_success(x_config, http_client, mock_logger):
    """Successfully gets media upload status."""
    route = respx.get("https://api.x.com/2/media/upload").mock(
        return_value=Response(
            200, json={"data": {"processing_info": {"state": "in_progress", "progress_percent": 50}}}
        )
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    result = await adapter.get_upload_status("3_12345")

    assert result["state"] == "in_progress"
    assert result["progress_percent"] == 50
    assert route.called

    query = route.calls[0].request.url.query.decode("utf-8")
    assert "command=STATUS" in query
    assert "media_id=3_12345" in query


@pytest.mark.asyncio
@respx.mock
async def test_get_upload_status_flat_response(x_config, http_client, mock_logger):
    """Successfully gets media upload status from flat response."""
    respx.get("https://api.x.com/2/media/upload").mock(
        return_value=Response(
            200, json={"processing_info": {"state": "succeeded"}}
        )
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    result = await adapter.get_upload_status("3_12345")

    assert result["state"] == "succeeded"


# ── upload tests ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
@respx.mock
async def test_upload_success(x_config, http_client, mock_logger):
    """Successfully initiates media upload via upload()."""
    route = respx.post("https://api.x.com/2/media/upload").mock(
        return_value=Response(
            200, json={"data": {"id": "3_12345"}}
        )
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    result = await adapter.upload(command="INIT", total_bytes=1024, media_type="image/jpeg")

    assert result["id"] == "3_12345"
    assert route.called

    import json
    request = route.calls[0].request
    req_json = json.loads(request.content)
    assert req_json["command"] == "INIT"
    assert req_json["total_bytes"] == 1024
    assert req_json["media_type"] == "image/jpeg"


# ── create_metadata tests ────────────────────────────────────────────────────


@pytest.mark.asyncio
@respx.mock
async def test_create_metadata_success(x_config, http_client, mock_logger):
    """Successfully creates media metadata."""
    route = respx.post("https://api.x.com/2/media/metadata").mock(
        return_value=Response(
            201, json={"data": {}}
        )
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    result = await adapter.create_metadata(media_id="3_12345", alt_text={"text": "A description"})

    assert result == {}
    assert route.called

    import json
    request = route.calls[0].request
    req_json = json.loads(request.content)
    assert req_json["media_id"] == "3_12345"
    assert req_json["alt_text"]["text"] == "A description"

# ── create_subtitles tests ───────────────────────────────────────────────────


@pytest.mark.asyncio
@respx.mock
async def test_create_subtitles_success(x_config, http_client, mock_logger):
    """Successfully creates media subtitles."""
    route = respx.post("https://api.x.com/2/media/subtitles").mock(
        return_value=Response(
            201, json={"data": {"media_id": "3_12345"}}
        )
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    subtitles = [{"media_id": "3_12345", "language_code": "en", "display_name": "English"}]
    result = await adapter.create_subtitles(media_id="3_12345", subtitles=subtitles)

    assert result["media_id"] == "3_12345"
    assert route.called

    import json
    request = route.calls[0].request
    req_json = json.loads(request.content)
    assert req_json["media_id"] == "3_12345"
    assert req_json["subtitles"][0]["language_code"] == "en"


# ── delete_subtitles tests ───────────────────────────────────────────────────


@pytest.mark.asyncio
@respx.mock
async def test_delete_subtitles_success(x_config, http_client, mock_logger):
    """Successfully deletes media subtitles."""
    route = respx.delete("https://api.x.com/2/media/subtitles").mock(
        return_value=Response(
            200, json={"data": {"media_id": "3_12345"}}
        )
    )

    adapter = XAdapter(x_config, http_client, mock_logger)

    result = await adapter.delete_subtitles(
        media_id="3_12345",
        media_category="TweetVideo",
        subtitle_info={"subtitles": [{"language_code": "en"}]}
    )

    assert result["media_id"] == "3_12345"
    assert route.called

    import json
    request = route.calls[0].request
    req_json = json.loads(request.content)
    assert req_json["media_id"] == "3_12345"
    assert req_json["media_category"] == "TweetVideo"


# ── initialize_upload tests ──────────────────────────────────────────────────


@pytest.mark.asyncio
@respx.mock
async def test_initialize_upload_success(x_config, http_client, mock_logger):
    """Successfully initializes media upload via initialize_upload()."""
    route = respx.post("https://api.x.com/2/media/upload/initialize").mock(
        return_value=Response(
            200, json={"data": {"id": "3_12345"}}
        )
    )

    adapter = XAdapter(x_config, http_client, mock_logger)
    result = await adapter.initialize_upload(total_bytes=1024, media_type="image/jpeg", media_category="TweetVideo")

    assert result["id"] == "3_12345"
    assert route.called

    import json
    request = route.calls[0].request
    req_json = json.loads(request.content)
    assert req_json["total_bytes"] == 1024
    assert req_json["media_type"] == "image/jpeg"
    assert req_json["media_category"] == "TweetVideo"
