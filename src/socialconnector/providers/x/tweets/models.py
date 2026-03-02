from typing import Any

from pydantic import BaseModel, ConfigDict


class Tweet(BaseModel):
    """Tweet model"""

    id: str | None = None
    text: str | None = None
    author_id: str | None = None
    created_at: str | None = None
    conversation_id: str | None = None
    in_reply_to_user_id: str | None = None
    referenced_tweets: list[Any] | None = None
    public_metrics: dict[str, Any] | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class TweetAnalyticsResponse(BaseModel):
    data: list[Any] | None = None
    errors: list[Any] | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class TweetCountsAllResponseMeta(BaseModel):
    total_tweet_count: int | None = None
    next_token: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class TweetCountsAllResponse(BaseModel):
    data: list[Any] | None = None
    errors: list[Any] | None = None
    meta: TweetCountsAllResponseMeta | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class TweetCreateRequest(BaseModel):
    text: str | None = None
    direct_message_deep_link: str | None = None
    for_super_followers_only: bool | None = None
    quote_tweet_id: str | None = None
    model_config = ConfigDict(populate_by_name=True, extra="allow")


class TweetCreateResponseData(BaseModel):
    id: str | None = None
    text: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class TweetCreateResponse(BaseModel):
    data: TweetCreateResponseData | None = None
    errors: list[Any] | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class TweetDeleteResponseData(BaseModel):
    deleted: bool | None = None

    model_config = ConfigDict(populate_by_name=True)


class TweetDeleteResponse(BaseModel):
    data: TweetDeleteResponseData | None = None
    errors: list[Any] | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class TweetGetByIdResponse(BaseModel):
    data: Tweet | None = None
    errors: list[Any] | None = None
    includes: Any | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class TweetInsights28hrResponse(BaseModel):
    data: list[Any] | None = None
    errors: list[Any] | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class TweetInsightsHistoricalResponse(BaseModel):
    data: list[Any] | None = None
    errors: list[Any] | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class TweetLikingUsersResponseMeta(BaseModel):
    next_token: str | None = None
    result_count: int | None = None

    model_config = ConfigDict(populate_by_name=True)


class TweetLikingUsersResponse(BaseModel):
    data: list[Any] | None = None
    errors: list[Any] | None = None
    meta: TweetLikingUsersResponseMeta | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class TweetQuotedResponseMeta(BaseModel):
    next_token: str | None = None
    result_count: int | None = None

    model_config = ConfigDict(populate_by_name=True)


class TweetQuotedResponse(BaseModel):
    data: list[Any] | None = None
    errors: list[Any] | None = None
    meta: TweetQuotedResponseMeta | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class TweetRepostsResponseMeta(BaseModel):
    next_token: str | None = None
    result_count: int | None = None

    model_config = ConfigDict(populate_by_name=True)


class TweetRepostsResponse(BaseModel):
    data: list[Any] | None = None
    errors: list[Any] | None = None
    meta: TweetRepostsResponseMeta | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class TweetRetweetedByResponseMeta(BaseModel):
    next_token: str | None = None
    result_count: int | None = None

    model_config = ConfigDict(populate_by_name=True)


class TweetRetweetedByResponse(BaseModel):
    data: list[Any] | None = None
    errors: list[Any] | None = None
    meta: TweetRetweetedByResponseMeta | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class TweetSearchAllResponseMeta(BaseModel):
    next_token: str | None = None
    result_count: int | None = None

    model_config = ConfigDict(populate_by_name=True)


class TweetSearchAllResponse(BaseModel):
    data: list[Any] | None = None
    errors: list[Any] | None = None
    meta: TweetSearchAllResponseMeta | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class TweetSearchRecentResponseMeta(BaseModel):
    next_token: str | None = None
    result_count: int | None = None

    model_config = ConfigDict(populate_by_name=True)


class TweetSearchRecentResponse(BaseModel):
    data: list[Any] | None = None
    errors: list[Any] | None = None
    meta: TweetSearchRecentResponseMeta | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class HideReplyRequest(BaseModel):
    hidden: bool

    model_config = ConfigDict(populate_by_name=True)


class HideReplyResponseData(BaseModel):
    hidden: bool | None = None

    model_config = ConfigDict(populate_by_name=True)


class HideReplyResponse(BaseModel):
    data: HideReplyResponseData | None = None
    errors: list[Any] | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")
