# Security policy

## Supported versions

| Version | Supported |
|---------|-----------|
| v1.1.0 (Story support) | Yes |
| Older releases | No |

No Return support is still in development and is not part of any shipped release.

## Reporting a vulnerability

Please **do not open a public issue** containing a vulnerability, secret, token,
or other sensitive data.

Use GitHub's private reporting channel instead:

1. Open the repository's **Security** tab.
2. Choose **Report a vulnerability** (this opens a private advisory draft).
3. Include the affected version, reproduction steps, and impact.

If private vulnerability reporting is unavailable, contact the maintainer
privately through GitHub rather than posting the details in an issue,
discussion, or pull request.

You should get an acknowledgement within a few days. Once the issue is
confirmed, the maintainer will agree a disclosure timeline with you before
publishing a fix or advisory.

## Scope

This mod is a read-only Discord Rich Presence helper for The Last of Us Part II
Remastered on PC. In scope:

- Leaked credentials, API keys, or tokens in source, configuration, or history.
- Unsafe handling of save data or process memory that could damage a user's
  game install or profile.
- Malicious release artifacts or supply-chain issues in the published package.

Out of scope:

- Game bugs or cheating concerns in The Last of Us Part II itself.
- Anti-cheat behaviour owned by the game publisher or platform.

## Secrets in this repository

`config.json` is included for reproducible builds and contains only the public
Discord application ID. It must never contain a bot token or user secret.
