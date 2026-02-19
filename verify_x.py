import asyncio
import os

from dotenv import load_dotenv

from socialconnector import SocialConnector

load_dotenv()

async def verify_x():
    print("Testing X (formerly Twitter) with provided keys...")
    api_key = os.getenv("TWITTER_API_KEY")
    api_secret = os.getenv("TWITTER_API_SECRET")

    # NOTE: To test post (posting), you need OAuth 1.0a tokens in .env
    access_token = os.getenv("TWITTER_ACCESS_TOKEN")
    access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

    connector = SocialConnector(
        "x",
        api_key=api_key,
        api_secret=api_secret,
        extra={
            "access_token": access_token,
            "access_token_secret": access_token_secret
        }
    )

    try:
        # 1. Connect (Verifies keys)
        await connector.connect()
        print("✅ Credentials accepted!")

        # 2. Fetch user info (Skipping to save rate limits if 429)
        handle = "airaninaveen"
        # user_info = await connector.adapter.get_user_by_username(handle)
        # print(f"✅ Fetched user info for @{handle}:")
        # print(f"   Name: {user_info.display_name}")
        # print(f"   ID: {user_info.id}")

        # 3. Attempt post (Requires OAuth 1.0a)
        if access_token and access_token_secret:
            print(f"Attempting to post to X for @{handle}...")
            # Mentioning the user in the post
            tweet_text = f"@{handle} Hello from my SocialConnector SDK! 🚀 #socialconnector #X"
            response = await connector.post(text=tweet_text)
            print(f"✅ Post successful! ID: {response.message_id}")
        else:
            print("⚠️ Skipping post test: TWITTER_ACCESS_TOKEN/SECRET not provided in .env")

    except Exception as e:
        print(f"❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await connector.disconnect()

if __name__ == "__main__":
    asyncio.run(verify_x())
