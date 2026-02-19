# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### In Progress
- Telegram: media upload support
- Slack provider implementation
- Discord provider implementation
- WhatsApp provider implementation

---

## [0.1.0] - 2026-02-19

### Added
- Core SDK infrastructure: `BaseAdapter`, `AdapterFactory`, `AdapterRegistry`
- Typed request/response models via Pydantic v2 (`Message`, `MessageResponse`, `Media`, `UserInfo`)
- Custom exceptions: `AuthenticationError`, `MessageError`, `SocialConnectorError`
- Shared `HTTPClient` (httpx-based) with timeout support
- **X (Twitter)** provider: post tweets, send DMs, media upload, OAuth1 + OAuth2 authentication
- **Telegram** provider: send messages, edit/delete messages, webhook support (media upload not yet implemented)
- Stub adapters registered for Slack, Discord, WhatsApp (not yet implemented)
- `python-dotenv` based configuration via `.env` files
- Full type annotations and Google-style docstrings

### Fixed
- Build backend corrected from internal `setuptools.backends._legacy:_Backend` to standard
  `setuptools.build_meta` for compatibility with all pip versions (including Google Colab)

[Unreleased]: https://github.com/naveenairani/socialconnect/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/naveenairani/socialconnect/releases/tag/v0.1.0
