# X (Twitter) Provider

The `XAdapter` provides a comprehensive integration with the X API v2 (and v1.1 for media uploads).

## Authentication

X supports two primary authentication modes:

1. **OAuth 1.0a (User Context)**: Required for POST/DELETE actions (tweets, likes, DMs) and accessing private user data. Requires `api_key`, `api_secret`, `access_token`, and `access_token_secret`.
2. **OAuth 2.0 (App-only)**: Used for read-only access to public data. Requires `api_key` and `api_secret` (a bearer token will be obtained automatically, or you can supply one via `bearer_token`).

### Configuration

All authentication parameters can be passed directly to `SocialConnector` — the factory automatically routes provider-specific fields like `access_token` and `bearer_token` into the adapter:

```python
from socialconnector import SocialConnector

sc = SocialConnector(
    provider="x",
    api_key="YOUR_API_KEY",
    api_secret="YOUR_API_SECRET",
    access_token="YOUR_ACCESS_TOKEN",
    access_token_secret="YOUR_ACCESS_TOKEN_SECRET",
    bearer_token="YOUR_BEARER_TOKEN",  # optional
)
```

### Environment Variables (`.env`)

```env
TWITTER_API_KEY=...
TWITTER_API_SECRET=...
TWITTER_ACCESS_TOKEN=...
TWITTER_ACCESS_TOKEN_SECRET=...
TWITTER_BEARER_TOKEN=...          # optional
TWITTER_CLIENT_ID=...             # for future OAuth 2.0 PKCE
TWITTER_CLIENT_SECRET=...         # for future OAuth 2.0 PKCE
```

```python
import os
from dotenv import load_dotenv
from socialconnector import SocialConnector

load_dotenv()

sc = SocialConnector(
    provider="x",
    api_key=os.getenv("TWITTER_API_KEY"),
    api_secret=os.getenv("TWITTER_API_SECRET"),
    access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
    access_token_secret=os.getenv("TWITTER_ACCESS_TOKEN_SECRET"),
    bearer_token=os.getenv("TWITTER_BEARER_TOKEN"),
)
```

## Supported Features

### Tweets

- `post(text, media, reply_to_id, quote_tweet_id)`: Create a tweet.
- `delete_message(chat_id, message_id)`: Delete a tweet.
- `get_tweet(tweet_id)`: Fetch a single tweet.
- `get_tweets(ids)`: Batch fetch tweets.
- `get_home_timeline(user_id)`: Get user's home timeline (OAuth 1.0a).
- `get_user_tweets(user_id)`: Get a user's tweets.
- `get_user_mentions(user_id)`: Get mentions for a user.

### Direct Messages (DM v2)

- `direct_message(chat_id, text)`: Send a DM to a specific user (recipient user ID).
- `send_to_conversation(conversation_id, text)`: Send a DM to an existing conversation.
- `create_group_conversation(participant_ids, text)`: Create a new group DM.
- `get_messages(chat_id, limit)`: List all DM events.
- `get_conversation_messages(conversation_id, limit)`: List events for a specific conversation.
- `get_participant_messages(participant_id, limit)`: List events for a one-to-one conversation.

### Social Interactions

- `like_tweet(user_id, tweet_id)`: Like a tweet.
- `unlike_tweet(user_id, tweet_id)`: Remove a like.
- `get_liked_tweets(user_id)`: Get tweets liked by a user.
- `retweet(user_id, tweet_id)`: Retweet a tweet.
- `unretweet(user_id, tweet_id)`: Undo a retweet.

### Relationship Management

- `follow_user(user_id, target_user_id)`: Follow a user.
- `unfollow_user(user_id, target_user_id)`: Unfollow a user.
- `get_followers(user_id)`: Get followers list.
- `get_following(user_id)`: Get following list.

### Information Organization

- `bookmark_tweet(user_id, tweet_id)`: Bookmark a tweet.
- `remove_bookmark(user_id, tweet_id)`: Remove a bookmark.
- `get_bookmarks(user_id)`: List bookmarks.
- `create_list(name, description, private)`: Create a Twitter list.
- `delete_list(list_id)`: Delete a list.
- `add_list_member(list_id, user_id)`: Add user to list.
- `remove_list_member(list_id, user_id)`: Remove user from list.
- `get_list_tweets(list_id)`: Get tweets from a list.

### Search & Discovery

- `search_tweets(query, all_history)`: Search tweets (recent or all).
- `get_user_info(user_id)`: Get user details.
- `get_user_by_username(username)`: Get user by handle.

### Real-time (Filtered Stream)

- `add_stream_rule(value, tag)`: Add filtering rule.
- `delete_stream_rules(ids)`: Remove filtering rules.
- `get_stream_rules()`: List current rules.

## Usage Example

```python
import asyncio
import os
from dotenv import load_dotenv
from socialconnector import SocialConnector

load_dotenv()

async def main():
    sc = SocialConnector(
        provider="x",
        api_key=os.getenv("TWITTER_API_KEY"),
        api_secret=os.getenv("TWITTER_API_SECRET"),
        access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
        access_token_secret=os.getenv("TWITTER_ACCESS_TOKEN_SECRET"),
    )

    await sc.connect()

    # Post a tweet
    result = await sc.post("Hello from SocialConnect!")
    print(f"Tweet ID: {result.message_id}")

    # Like a tweet (provider-specific method)
    await sc.adapter.like_tweet(user_id="123", tweet_id="456")

    await sc.disconnect()

asyncio.run(main())
```

## Free Tier Limitations

The X API free tier includes:
- **Post creation** (`POST /2/tweets`) — 1,500 tweets/month
- **Post deletion** (`DELETE /2/tweets/:id`)
- **User lookup** (`GET /2/users/me`)

Rate limiting is handled automatically. The adapter paces requests (1s minimum interval) and retries on 429 responses with exponential backoff.

## Scopes Required

Ensure your X App has the following permissions enabled in the Developer Portal:

- `tweet.read`, `tweet.write`
- `users.read`
- `follows.read`, `follows.write`
- `like.read`, `like.write`
- `bookmark.read`, `bookmark.write`
- `list.read`, `list.write`
- `dm.read`, `dm.write` (for DMs)
- `offline.access` (if using OAuth 2.0 PKCE — future)
