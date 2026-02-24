import asyncio
import logging

from socialconnector.core.models import AdapterConfig
from socialconnector.providers.x import XAdapter


class DummyResponse:
    def __init__(self, status_code=200, headers=None, payload=None):
        self.status_code = status_code
        self.headers = headers or {}
        self._payload = payload if payload is not None else {"data": []}
        self.content = b"{}"

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError("http error")

    def json(self):
        return self._payload


class DummyHTTPClient:
    def __init__(self, response):
        self._response = response

    async def request(self, *args, **kwargs):
        return self._response


def test_x_request_ignores_invalid_rate_limit_headers():
    cfg = AdapterConfig(
        provider="x",
        api_key="k",
        api_secret="s",
        extra={"access_token": "tok", "access_token_secret": "sec"},
    )
    response = DummyResponse(
        status_code=200,
        headers={"x-rate-limit-remaining": "NaN", "x-rate-limit-reset": "not-a-timestamp"},
        payload={"data": {"id": "123"}},
    )

    adapter = XAdapter(cfg, DummyHTTPClient(response), logging.getLogger("test"))
    result = asyncio.run(adapter._request("GET", "users/me"))

    assert result["data"]["id"] == "123"
    assert adapter._rate_limit_remaining is None
    assert adapter._rate_limit_reset == 0
