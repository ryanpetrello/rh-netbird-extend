# rh-netbird-extend

Extend your NetBird VPN session without opening a browser.

NetBird sessions last 36 hours. When one expires, the GUI pops a browser
window for SSO re-authentication. This script performs that OAuth flow
headlessly so you can extend your session from the terminal.

## Prerequisites

- An active NetBird connection (initial login must be done via the GUI)
- Python 3.11+
- Your SSO credentials

## Installation

```bash
# With pipx (isolated environment)
pipx install git+https://github.com/ryanpetrello/rh-netbird-extend.git

# Or with pip
pip install --user git+https://github.com/ryanpetrello/rh-netbird-extend.git
```

## Usage

```bash
# Interactive (prompts for password)
rh-netbird-extend --username jdoe

# Piped from a password manager
pass sso | rh-netbird-extend --username jdoe
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
