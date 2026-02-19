import asyncio
import os
import json
import httpx
from authlib.integrations.httpx_client import OAuth1Auth
from dotenv import load_dotenv

load_dotenv()

async def test_x_post_content():
    api_key = os.getenv("TWITTER_API_KEY")
    api_secret = os.getenv("TWITTER_API_SECRET")
    access_token = os.getenv("TWITTER_ACCESS_TOKEN")
    access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

    url = "https://api.x.com/2/tweets"
    data = {"text": "Test with manual serialization from SocialConnector SDK! 🚀"}
    
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

    print(f"Testing POST to {url} with content=json.dumps(data)")
    
    async with httpx.AsyncClient() as client:
        content = json.dumps(data)
        response = await client.request(
            "POST", url, content=content, auth=auth, headers=headers
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")

if __name__ == "__main__":
    asyncio.run(test_x_post_content())
