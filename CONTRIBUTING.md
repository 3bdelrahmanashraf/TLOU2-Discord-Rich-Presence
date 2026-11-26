# Contributing

Thanks for your interest in contributing to **TLOU2 Discord Rich Presence**.

## Before you start

- Read the [README](README.md) for project scope, setup, and current status.
- Check existing [issues](https://github.com/3bdelrahmanashraf/tlou2-discord-rich-presence/issues) before opening a new one.
- For No Return work, follow the tracking issues (#2-#32) and keep v1.2.0 story support stable.

## Good ways to contribute

- **Bug reports**: include game version/build, mod version, install method (ASI/VBS), logs, and reproduction steps.
- **Discord assets**: follow `DISCORD-ASSETS.txt` and the asset master checklist (#32). Asset keys must match exactly.
- **Docs**: fix typos, clarify setup/troubleshooting, or improve verification notes.
- **Code**: keep changes focused, avoid unrelated refactors, and preserve the read-only/no-save-edit constraint.

## Development setup

1. Clone the repo.
2. Use Python 3.11+ for local checks.
3. Copy `config.json.example` to `config.json` for local testing if needed.
4. Validate Python syntax before opening a PR:

   ```powershell
   python -m py_compile tlou2_rpc.py
   python -m py_compile promo/make_progress.py
   ```

## Pull requests

- Keep PRs small and scoped to one change.
- Describe what changed, why, and how it was verified.
- Include screenshots/logs when changing status formatting, assets, or docs visuals.
- Do not include secrets, personal tokens, or unrelated local files.
- Do not bump the version beyond the approved v1.2.0 placeholder, or package/release full No Return features, unless explicitly approved.

## Issue labels

- `good first issue`: good entry points for newcomers.
- `help wanted`: contributions welcome.
- `bug`: something is broken.
- `enhancement`: improvement or new capability.

## Security / secrets

If you find a leaked secret or sensitive data, **do not open a public issue with the secret value**. Follow [SECURITY.md](SECURITY.md) and report it privately through GitHub's security channels.
