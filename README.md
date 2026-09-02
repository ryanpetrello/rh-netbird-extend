# rh-netbird-extend

Extend your NetBird VPN session without opening a browser.

NetBird sessions last 36 hours. When one expires, the GUI pops a browser
window for SSO re-authentication. This script performs that OAuth flow
headlessly so you can extend your session from the terminal.

## Prerequisites

- An active NetBird connection (initial login must be done via the GUI)
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended) or `pip install requests`
- Your SSO credentials

## Installation

```bash
# Clone the repo
git clone https://github.com/ryanpetrello/rh-netbird-extend.git
cd rh-netbird-extend

# Copy the script to your PATH
cp rh-netbird-extend ~/bin/
chmod +x ~/bin/rh-netbird-extend
```

No separate `pip install` step needed. The script uses
[PEP 723](https://peps.python.org/pep-0723/) inline metadata, so `uv run`
resolves dependencies automatically.

## Usage

```bash
# Interactive (prompts for password)
uv run rh-netbird-extend --username jdoe

# Piped from a password manager
pass sso | uv run rh-netbird-extend --username jdoe
```

On success, the script prints the new session expiry:

```
Session expires: 2026-09-04T12:00:00Z (in 1d 11h)
```

## Configuration

Set your username once via environment variable so you don't need to
pass `--username` every time:

```bash
# Add to your .bashrc / .zshrc
export RH_NETBIRD_USERNAME=jdoe
```

Then just:

```bash
rh-netbird-extend
```

