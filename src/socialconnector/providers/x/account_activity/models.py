from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from socialconnector.core.models import PageInfo


class ValidateSubscriptionResponseData(BaseModel):
    """Nested model for ValidateSubscriptionResponseData"""

    subscribed: bool | None = None


class ValidateSubscriptionResponse(BaseModel):
    """Response model for validate_subscription"""

    data: ValidateSubscriptionResponseData | None = None
    errors: list[Any] | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class CreateSubscriptionRequest(BaseModel):
    """Request model for create_subscription"""

    model_config = ConfigDict(populate_by_name=True)


class CreateSubscriptionResponseData(BaseModel):
    """Nested model for CreateSubscriptionResponseData"""

    subscribed: bool | None = None


class CreateSubscriptionResponse(BaseModel):
    """Response model for create_subscription"""

    data: CreateSubscriptionResponseData | None = None
    errors: list[Any] | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class UpdateSubscriptionRequest(BaseModel):
    """Request model for update_subscription"""

    model_config = ConfigDict(populate_by_name=True)


class UpdateSubscriptionResponseData(BaseModel):
    """Nested model for UpdateSubscriptionResponseData"""

    subscribed: bool | None = None


class UpdateSubscriptionResponse(BaseModel):
    """Response model for update_subscription"""

    data: UpdateSubscriptionResponseData | None = None
    errors: list[Any] | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class GetSubscriptionsResponseData(BaseModel):
    """Nested model for GetSubscriptionsResponseData"""

    application_id: str | None = None
    subscriptions: list[Any] | None = None
    webhook_id: str | None = None
    webhook_url: str | None = None


class GetSubscriptionsResponse(BaseModel):
    """Response model for get_subscriptions"""

    data: GetSubscriptionsResponseData = Field(
        description="The list of active subscriptions for a specified webhook",
        default_factory=lambda: GetSubscriptionsResponseData(),
    )
    errors: list[Any] | None = None
    meta: PageInfo | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class DeleteSubscriptionResponseData(BaseModel):
    """Nested model for DeleteSubscriptionResponseData"""

    subscribed: bool | None = None


class DeleteSubscriptionResponse(BaseModel):
    """Response model for delete_subscription"""

    data: DeleteSubscriptionResponseData | None = None
    errors: list[Any] | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class GetSubscriptionCountResponseData(BaseModel):
    """Nested model for GetSubscriptionCountResponseData"""

    account_name: str | None = None
    provisioned_count: str | None = None
    subscriptions_count_all: str | None = None
    subscriptions_count_direct_messages: str | None = None
    create_replay_job_response: "CreateReplayJobResponse | None" = None
    delete_subscription_response: "DeleteSubscriptionResponse | None" = None
    get_subscription_count_response: "GetSubscriptionCountResponse | None" = None


class GetSubscriptionCountResponse(BaseModel):
    """Response model for get_subscription_count"""

    data: GetSubscriptionCountResponseData = Field(
        description="The count of active subscriptions across all webhooks",
        default_factory=lambda: GetSubscriptionCountResponseData(),
    )
    errors: list[Any] | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class CreateReplayJobResponse(BaseModel):
    """Response model for create_replay_job"""

    created_at: str | None = None
    job_id: str | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class StreamResponse(BaseModel):
    """Activity Stream (Streaming) data item"""

    model_config = ConfigDict(populate_by_name=True, extra="allow")
