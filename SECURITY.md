# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 0.1.x   | ✅ Yes             |
| < 0.1   | ❌ No              |

## Reporting a Vulnerability

**Please do NOT report security vulnerabilities via GitHub Issues.** Public issues are visible to everyone, which could expose users before a fix is released.

Instead, report vulnerabilities by:

1. **Email**: Send details to the maintainer's email (listed in `pyproject.toml`)
2. **GitHub Private Advisory**: [Open a private security advisory](https://github.com/naveenairani/socialconnect/security/advisories/new)

### What to include

- A description of the vulnerability and its potential impact
- Steps to reproduce (proof-of-concept code if possible)
- Affected versions
- Any suggested mitigations

### What to expect

- **Acknowledgment** within 48 hours
- **Status update** within 7 days
- A **fix and coordinated disclosure** as quickly as possible, typically within 30 days

## Security Best Practices for Users

- **Never commit API keys or secrets** — always use environment variables or `.env` files (which should be in `.gitignore`)
- Use the provided `.env.example` as a template
- Rotate your API tokens if you suspect they have been exposed
- Use the minimum required API permissions/scopes for your use case
