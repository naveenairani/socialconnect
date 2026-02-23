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
    ValidateSubscriptionResponse,
)


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
