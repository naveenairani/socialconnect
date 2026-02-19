# SocialConnector 🔗

A unified Python SDK for connecting with multiple social media and messaging platforms (X, Telegram, Discord, etc.) through a simple, consistent API.

## Installation

```bash
# Install from GitHub
pip install git+https://github.com/yourusername/socialconnector.git
```

## Quick Start

```python
from socialconnector import SocialConnector

# Initialize with X (formerly Twitter)
connector = SocialConnector("x", api_key="...", api_secret="...")

# Post a public update (Tweet)
await connector.post(text="Hello world from SocialConnector!")

# Send a private direct message (DM)
await connector.direct_message(chat_id="12345", text="Hello privately!")
```

## Supported Platforms

| Platform   | Post | DM  | Media | Webhooks | Status  |
|------------|------|-----|-------|----------|---------|
| X (Twitter)| ✅   | ✅  | ✅    | ✅       | Stable  |
| Telegram   | ✅   | ✅  | ✅    | ✅       | Stable  |
| Slack      | ✅   | ✅  | ✅    | ✅       | Planned |

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full architecture and design pattern documentation.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License — see [LICENSE](LICENSE) for details.
