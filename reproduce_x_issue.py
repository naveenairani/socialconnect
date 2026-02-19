import asyncio
import os
import json
import httpx
from authlib.integrations.httpx_client import OAuth1Auth
from dotenv import load_dotenv

load_dotenv()

async def test_x_post():
    api_key = os.getenv("TWITTER_API_KEY")
    api_secret = os.getenv("TWITTER_API_SECRET")
    access_token = os.getenv("TWITTER_ACCESS_TOKEN")
    access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

    if not all([api_key, api_secret, access_token, access_token_secret]):
        print("Missing credentials in .env")
        return

    url = "https://api.x.com/2/tweets"
    data = {"text": "Reproduction test from SocialConnector SDK!"}
    
    auth = OAuth1Auth(
        client_id=api_key,
        client_secret=api_secret,
        token=access_token,
        token_secret=access_token_secret,
    )

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    print(f"Testing POST to {url} with json={data}")
    
    async with httpx.AsyncClient() as client:
        # Test 1: Using json parameter
        print("\n--- Test 1: Using json parameter ---")
        try:
            response = await client.request(
                "POST", url, json=data, auth=auth, headers=headers
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
        except Exception as e:
            print(f"Test 1 failed with error: {e}")

        # Test 2: Using content parameter (manual serialization)
        print("\n--- Test 2: Using content parameter ---")
        try:
            content = json.dumps(data)
            # Re-create auth just in case (though it should be fine)
            response = await client.request(
                "POST", url, content=content, auth=auth, headers=headers
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
        except Exception as e:
            print(f"Test 2 failed with error: {e}")

if __name__ == "__main__":
    asyncio.run(test_x_post())
