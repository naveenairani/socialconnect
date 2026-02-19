# SocialConnector

> A unified Python SDK for connecting with multiple social media and messaging platforms through a single, consistent API.

[![PyPI](https://img.shields.io/badge/install-GitHub-blue)](https://github.com/naveenairani/socialconnect)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

---

## Features

- **Unified API** — one interface for X, Telegram, Slack, Discord, and more
- **Post & DM** — public posts and private direct messages
- **Media uploads** — images and files across platforms
- **Webhook support** — receive real-time events
- **Type-safe** — full Pydantic v2 models and type annotations
- **Easy config** — load credentials from `.env` files

---

## Installation

```bash
# Install from GitHub
pip install git+https://github.com/naveenairani/socialconnect.git

# Install with a specific platform's extras
pip install "git+https://github.com/naveenairani/socialconnect.git#egg=socialconnector[twitter]"

# Install everything
pip install "git+https://github.com/naveenairani/socialconnect.git#egg=socialconnector[all]"
```

---

## Quick Start

```python
import asyncio
from socialconnector import SocialConnector

async def main():
    # X (Twitter) — OAuth1 credentials
    connector = SocialConnector(
        "x",
        api_key="YOUR_API_KEY",
        api_secret="YOUR_API_SECRET",
        access_token="YOUR_ACCESS_TOKEN",
        access_token_secret="YOUR_ACCESS_TOKEN_SECRET",
    )

    # Post a public Tweet
    response = await connector.post(text="Hello world from SocialConnector!")
    print(response)

    # Send a private DM
    await connector.direct_message(chat_id="user_id_here", text="Hello privately!")

asyncio.run(main())
```

Using `.env` for credentials:

```bash
# .env
X_API_KEY=your_key
X_API_SECRET=your_secret
X_ACCESS_TOKEN=your_token
X_ACCESS_TOKEN_SECRET=your_token_secret
```

```python
from dotenv import load_dotenv
load_dotenv()
connector = SocialConnector("x")  # reads from environment automatically
```

---

## Supported Platforms

| Platform    | Post | DM  | Media | Webhooks | Status              |
|-------------|------|-----|-------|----------|---------------------|
| X (Twitter) | ✅   | ✅  | ✅    | ✅       | Working             |
| Telegram    | ✅   | ✅  | ❌    | ✅       | Partial             |
| Slack       | ❌   | ❌  | ❌    | ❌       | Stub (coming soon)  |
| Discord     | ❌   | ❌  | ❌    | ❌       | Stub (coming soon)  |
| WhatsApp    | ❌   | ❌  | ❌    | ❌       | Stub (coming soon)  |

---

## Architecture

SocialConnector uses the **Adapter Pattern** — every platform implements the same `BaseAdapter` interface so your application code never needs to know which platform it is talking to.

```
SocialConnector (factory)
    └── BaseAdapter (abstract)
            ├── XAdapter          (X / Twitter)
            ├── TelegramAdapter   (Telegram)
            ├── SlackAdapter      (Slack)
            └── DiscordAdapter    (Discord)
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full design documentation.

---

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) to get started.

## Security

Found a vulnerability? See [SECURITY.md](SECURITY.md) for responsible disclosure instructions.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for release history.

## License

MIT License — see [LICENSE](LICENSE) for details.
