"""
X Account Activity Mixin for webhooks and subscriptions.
"""


from socialconnector.core.models import (
    CreateReplayJobResponse,
    CreateSubscriptionRequest,
    CreateSubscriptionResponse,
    DeleteSubscriptionResponse,
    GetSubscriptionCountResponse,
    GetSubscriptionsResponse,
    UpdateSubscriptionRequest,
    UpdateSubscriptionResponse,
    ValidateSubscriptionResponse,
    StreamResponse,
)
from socialconnector.core.streaming import StreamConfig, stream_with_retry
from typing import AsyncGenerator


class XAccountActivityMixin:
    """Mixin for account activity operations (webhooks and subscriptions)."""

    async def validate_subscription(self, webhook_id: str) -> ValidateSubscriptionResponse:
        """
        Validate subscription
        Checks a user’s Account Activity subscription for a given webhook.
        """
        path = f"account_activity/webhooks/{self._validate_path_param('webhook_id', webhook_id)}/subscriptions/all"
        res = await self._request("GET", path, auth_type="oauth1")
        return ValidateSubscriptionResponse.model_validate(res)

    async def create_subscription(
        self, webhook_id: str, body: CreateSubscriptionRequest | None = None
    ) -> CreateSubscriptionResponse:
        """
        Create subscription
        Creates an Account Activity subscription for the user and the given webhook.
        """
        path = f"account_activity/webhooks/{self._validate_path_param('webhook_id', webhook_id)}/subscriptions/all"

        json_data = None
        if body is not None:
            json_data = body.model_dump(exclude_none=True)

        res = await self._request("POST", path, json=json_data, auth_type="oauth1")
        return CreateSubscriptionResponse.model_validate(res)

    async def create_activity_subscription(
        self, body: CreateSubscriptionRequest | None = None
    ) -> CreateSubscriptionResponse:
        """
        Create X activity subscription
        Creates a subscription for an X activity event.
        Args:
            body: Request body
        Returns:
            CreateSubscriptionResponse: Response data
        """
        url = "activity/subscriptions"
        json_data = None
        if body is not None:
            json_data = body.model_dump(exclude_none=True)

        # The raw snippet prefers BearerToken for this endpoint
        res = await self._request("POST", url, json=json_data, auth_type="bearer_token")
        return CreateSubscriptionResponse.model_validate(res)

    async def update_subscription(
        self, subscription_id: str, body: UpdateSubscriptionRequest | None = None
    ) -> UpdateSubscriptionResponse:
        """
        Update X activity subscription
        Updates a subscription for an X activity event.
        Args:
            subscription_id: The ID of the subscription to update.
            body: Request body
        Returns:
            UpdateSubscriptionResponse: Response data
        """
        sub_id = self._validate_path_param("subscription_id", str(subscription_id))
        path = f"activity/subscriptions/{sub_id}"

        json_data = None
        if body is not None:
            json_data = body.model_dump(exclude_none=True)

        # Write operations prefer OAuth1 for X normally
        res = await self._request("PUT", path, json=json_data, auth_type="oauth1")
        return UpdateSubscriptionResponse.model_validate(res)

    async def delete_activity_subscription(self, subscription_id: str) -> DeleteSubscriptionResponse:
        """
        Deletes X activity subscription
        Deletes a subscription for an X activity event.
        Args:
            subscription_id: The ID of the subscription to delete.
        Returns:
            DeleteSubscriptionResponse: Response data
        """
        sub_id = self._validate_path_param("subscription_id", str(subscription_id))
        path = f"activity/subscriptions/{sub_id}"

        # The raw snippet prefers BearerToken for this endpoint
        res = await self._request("DELETE", path, auth_type="bearer_token")
        return DeleteSubscriptionResponse.model_validate(res)

    async def get_subscriptions(self, webhook_id: str) -> GetSubscriptionsResponse:
        """
        Get subscriptions
        Retrieves a list of all active subscriptions for a given webhook.
        """
        path = f"account_activity/webhooks/{self._validate_path_param('webhook_id', webhook_id)}/subscriptions/all/list"
        # The auto-generated code preferred BearerToken here
        res = await self._request("GET", path, auth_type="oauth2")
        return GetSubscriptionsResponse.model_validate(res)

    async def delete_subscription(self, webhook_id: str, user_id: str) -> DeleteSubscriptionResponse:
        """
        Delete subscription
        Deletes an Account Activity subscription for the given webhook and user ID.
        """
        webhook = self._validate_path_param("webhook_id", webhook_id)
        user = self._validate_path_param("user_id", user_id)
        path = f"account_activity/webhooks/{webhook}/subscriptions/{user}/all"
        # The auto-generated code preferred BearerToken here
        res = await self._request("DELETE", path, auth_type="oauth2")
        return DeleteSubscriptionResponse.model_validate(res)

    async def get_subscription_count(self) -> GetSubscriptionCountResponse:
        """
        Get subscription count
        Retrieves a count of currently active Account Activity subscriptions.
        """
        path = "account_activity/subscriptions/count"
        # The auto-generated code preferred BearerToken here
        res = await self._request("GET", path, auth_type="oauth2")
        return GetSubscriptionCountResponse.model_validate(res)

    async def create_replay_job(
        self, webhook_id: str, from_date: str, to_date: str
    ) -> CreateReplayJobResponse:
        """
        Create replay job
        Creates a replay job to retrieve activities from up to the past 5 days for all
        subscriptions associated with a given webhook.
        """
        webhook = self._validate_path_param("webhook_id", webhook_id)
        path = f"account_activity/replay/webhooks/{webhook}/subscriptions/all"
        params = {}
        if from_date is not None:
            params["from_date"] = from_date
        if to_date is not None:
            params["to_date"] = to_date

        # The auto-generated code preferred BearerToken here
        res = await self._request("POST", path, params=params, auth_type="oauth2")
        return CreateReplayJobResponse.model_validate(res)

    async def get_activity_subscriptions(
        self, max_results: int | None = None, pagination_token: str | None = None
    ) -> AsyncGenerator[GetSubscriptionsResponse, None]:
        """
        Get X activity subscriptions
        Get a list of active subscriptions for XAA. Automatically paginates.
        Args:
            max_results: The maximum number of results to return per page.
            pagination_token: This parameter is used to get the next 'page' of results.
        Yields:
            GetSubscriptionsResponse: One page of results at a time. Automatically handles pagination using next_token.
        """
        url = "activity/subscriptions"
        current_pagination_token = pagination_token

        while True:
            params = {}
            if max_results is not None:
                params["max_results"] = max_results
            if current_pagination_token:
                params["pagination_token"] = current_pagination_token

            res = await self._request("GET", url, params=params, auth_type="bearer_token")
            page_response = GetSubscriptionsResponse.model_validate(res)
            yield page_response

            next_token = None
            if page_response.meta:
                next_token = page_response.meta.next_token
            elif isinstance(res, dict) and "meta" in res:
                next_token = res["meta"].get("next_token")
            
            if not next_token:
                break
            current_pagination_token = next_token

    async def stream(
        self,
        backfill_minutes: int | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        stream_config: StreamConfig | None = None,
    ) -> AsyncGenerator[StreamResponse, None]:
        """
        Activity Stream (Streaming)
        Stream of X Activities.
        This is a streaming endpoint that yields data in real-time as it becomes available.
        Each yielded item represents a single data point from the stream.
        The connection is automatically managed with exponential backoff retry logic.
        If the stream disconnects, the SDK will automatically reconnect without client intervention.
        Args:
            backfill_minutes: The number of minutes of backfill requested.
            start_time: YYYY-MM-DDTHH:mm:ssZ. The earliest UTC timestamp from which the Post labels will be provided.
            end_time: YYYY-MM-DDTHH:mm:ssZ. The latest UTC timestamp from which the Post labels will be provided.
            stream_config: Optional StreamConfig for customizing retry behavior, timeouts, and callbacks.
        Yields:
            StreamResponse: Individual streaming data items
        Raises:
            StreamError: If a non-retryable error occurs (auth errors, client errors) or max retries exceeded.
        """
        url = f"{self.BASE_URL}/activity/stream"

        bearer_token = await self.bearer_token_manager.get()
        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Accept": "application/json",
        }

        params = {}
        if backfill_minutes is not None:
            params["backfill_minutes"] = backfill_minutes
        if start_time is not None:
            params["start_time"] = start_time
        if end_time is not None:
            params["end_time"] = end_time

        # Use robust streaming with automatic retry and exponential backoff
        iterator = stream_with_retry(
            http_client=self.http_client,
            method="GET",
            url=url,
            params=params,
            headers=headers,
            config=stream_config,
        )

        async for data in iterator:
            yield StreamResponse.model_validate(data)
