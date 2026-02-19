"""
Tests for core infrastructure: Paginator (Cursor), Streaming, OAuth2 PKCE.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from socialconnector.core.oauth2_pkce import OAuth2PKCEFlow, OAuth2Token
from socialconnector.core.paginator import Cursor, _extract_nested
from socialconnector.core.streaming import (
    StreamErrorType,
    _classify,
    _compute_backoff,
)

# --------------------------------------------------------------------------- #
# Paginator                                                                    #
# --------------------------------------------------------------------------- #


class TestExtractNested:
    def test_dict_single_key(self):
        assert _extract_nested({"a": 1}, "a") == 1

    def test_dict_nested(self):
        data = {"meta": {"next_token": "tok123"}}
        assert _extract_nested(data, "meta.next_token") == "tok123"

    def test_missing_key_returns_none(self):
        assert _extract_nested({}, "meta.next_token") is None

    def test_object_attribute(self):
        class Obj:
            next_token = "abc"

        assert _extract_nested(Obj(), "next_token") == "abc"

    def test_none_input(self):
        assert _extract_nested(None, "a.b") is None


class TestCursor:
    @pytest.fixture
    def two_page_method(self):
        """Async callable returning two pages then no token."""
        pages = [
            {"data": [1, 2, 3], "meta": {"next_token": "page2"}},
            {"data": [4, 5], "meta": {}},
        ]
        call_count = [0]

        async def method(**kwargs):
            idx = call_count[0]
            call_count[0] += 1
            return pages[idx]

        return method

    @pytest.mark.asyncio
    async def test_pages_iterates_all(self, two_page_method):
        cursor = Cursor(two_page_method)
        pages = [p async for p in cursor.pages()]
        assert len(pages) == 2
        assert pages[0]["data"] == [1, 2, 3]
        assert pages[1]["data"] == [4, 5]

    @pytest.mark.asyncio
    async def test_pages_respects_limit(self, two_page_method):
        cursor = Cursor(two_page_method)
        pages = [p async for p in cursor.pages(limit=1)]
        assert len(pages) == 1

    @pytest.mark.asyncio
    async def test_items_iterates_all(self, two_page_method):
        cursor = Cursor(two_page_method)
        items = [i async for i in cursor.items()]
        assert items == [1, 2, 3, 4, 5]

    @pytest.mark.asyncio
    async def test_items_respects_limit(self, two_page_method):
        cursor = Cursor(two_page_method)
        items = [i async for i in cursor.items(limit=3)]
        assert items == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_passes_pagination_token(self):
        """Second call must receive the token from the first page."""
        received_tokens = []

        async def method(pagination_token=None, **kwargs):
            received_tokens.append(pagination_token)
            if pagination_token is None:
                return {"data": [1], "meta": {"next_token": "tok_next"}}
            return {"data": [2], "meta": {}}

        cursor = Cursor(method)
        items = [i async for i in cursor.items()]
        assert items == [1, 2]
        assert received_tokens == [None, "tok_next"]

    @pytest.mark.asyncio
    async def test_custom_token_field(self):
        async def method(cursor=None):
            if cursor is None:
                return {"items": ["a"], "next_cursor": "c1"}
            return {"items": ["b"], "next_cursor": None}

        cur = Cursor(
            method,
            next_token_field="next_cursor",
            data_field="items",
            token_param="cursor",
        )
        items = [i async for i in cur.items()]
        assert items == ["a", "b"]


# --------------------------------------------------------------------------- #
# Streaming                                                                    #
# --------------------------------------------------------------------------- #


class TestComputeBackoff:
    def test_exponential_growth(self):
        b0 = _compute_backoff(0, 1.0, 64.0, 2.0, jitter=False)
        b1 = _compute_backoff(1, 1.0, 64.0, 2.0, jitter=False)
        b2 = _compute_backoff(2, 1.0, 64.0, 2.0, jitter=False)
        assert b0 == 1.0
        assert b1 == 2.0
        assert b2 == 4.0

    def test_max_cap(self):
        b = _compute_backoff(100, 1.0, 64.0, 2.0, jitter=False)
        assert b == 64.0

    def test_jitter_adds_noise(self):
        # With jitter the value should be > base but not more than 25% more
        results = {_compute_backoff(0, 1.0, 64.0, 2.0, jitter=True) for _ in range(50)}
        # Should have more than one unique value
        assert len(results) > 1


class TestClassifyError:
    def test_rate_limit(self):

        exc = Exception("rate limited")
        err = _classify(exc, status=429)
        assert err.error_type == StreamErrorType.RATE_LIMITED
        assert err.is_retryable

    def test_auth_error_not_retryable(self):
        err = _classify(Exception("unauthorized"), status=401)
        assert err.error_type == StreamErrorType.AUTH_ERROR
        assert not err.is_retryable

    def test_server_error_retryable(self):
        err = _classify(Exception("internal"), status=503)
        assert err.is_retryable

    def test_client_error_not_retryable(self):
        err = _classify(Exception("bad req"), status=400)
        assert not err.is_retryable

    def test_timeout_retryable(self):
        import httpx

        err = _classify(httpx.TimeoutException("timeout"))
        assert err.error_type == StreamErrorType.TIMEOUT
        assert err.is_retryable


# --------------------------------------------------------------------------- #
# OAuth2 PKCE Flow                                                             #
# --------------------------------------------------------------------------- #


class TestOAuth2PKCEFlow:
    @pytest.fixture
    def flow(self):
        return OAuth2PKCEFlow(
            client_id="my_client",
            client_secret="my_secret",
            redirect_uri="https://example.com/callback",
            token_url="https://api.x.com/2/oauth2/token",
            authorization_url="https://x.com/i/oauth2/authorize",
            scopes=["tweet.read", "offline.access"],
        )

    def test_get_authorization_url_generates_pkce(self, flow):
        url = flow.get_authorization_url()
        assert "code_challenge=" in url
        assert "code_challenge_method=S256" in url
        assert flow._code_verifier is not None
        assert flow._code_challenge is not None

    def test_code_challenge_deterministic(self, flow):
        """Same verifier always produces same challenge."""
        import base64
        import hashlib

        verifier = "test_verifier_abc"
        digest = hashlib.sha256(verifier.encode()).digest()
        expected = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
        assert flow._make_challenge(verifier) == expected

    def test_authorization_url_includes_scopes(self, flow):
        url = flow.get_authorization_url()
        assert "tweet.read" in url
        assert "offline.access" in url

    def test_authorization_url_includes_state(self, flow):
        url = flow.get_authorization_url(state="mystate")
        assert "state=mystate" in url

    @pytest.mark.asyncio
    async def test_exchange_code_calls_token_endpoint(self, flow):
        flow.get_authorization_url()  # generate verifier

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "access_token": "AT123",
            "token_type": "bearer",
            "expires_in": 7200,
            "refresh_token": "RT456",
            "scope": "tweet.read",
        }

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response

        token = await flow.exchange_code("AUTH_CODE", mock_client)
        assert token.access_token == "AT123"
        assert token.refresh_token == "RT456"
        assert flow.token is not None

        mock_client.post.assert_called_once()
        call_kwargs = mock_client.post.call_args
        data = call_kwargs[1]["data"]
        assert data["code"] == "AUTH_CODE"
        assert data["grant_type"] == "authorization_code"

    @pytest.mark.asyncio
    async def test_refresh_token_request(self, flow):
        flow.token = OAuth2Token(
            access_token="old_AT",
            refresh_token="RT_existing",
            expires_in=0,
            expires_at=0,  # already expired
        )
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "access_token": "new_AT",
            "token_type": "bearer",
            "expires_in": 7200,
        }
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response

        new_token = await flow.refresh(mock_client)
        assert new_token.access_token == "new_AT"

    def test_token_expiry(self):
        import time

        token = OAuth2Token(
            access_token="tok",
            expires_in=7200,
            expires_at=time.time() + 7200,
        )
        assert not token.is_expired

        expired = OAuth2Token(
            access_token="tok",
            expires_in=1,
            expires_at=time.time() - 100,
        )
        assert expired.is_expired
