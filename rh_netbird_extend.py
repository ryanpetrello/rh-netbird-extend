#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["requests"]
# ///
"""Extend the NetBird VPN session without opening a browser.

Requires an active NetBird connection (use the GUI for initial login).
Performs the Red Hat SSO OAuth flow headlessly via PKCE, extending the
36-hour session window.

Reads the SSO password from stdin, or prompts interactively:

    password-manager-cmd | rh-netbird-extend --username jdoe
    rh-netbird-extend --username jdoe
"""

import argparse
import getpass
import json
import os
import subprocess
import sys
from html.parser import HTMLParser

import requests


class FormParser(HTMLParser):

    def __init__(self):
        super().__init__()
        self._in_form = False
        self._action = ""
        self._inputs = {}
        self.forms = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "form":
            self._in_form = True
            self._action = a.get("action", "")
            self._inputs = {}
        elif tag == "input" and self._in_form:
            name = a.get("name")
            if name:
                self._inputs[name] = a.get("value", "")

    def handle_endtag(self, tag):
        if tag == "form" and self._in_form:
            self.forms.append({
                "action": self._action,
                "inputs": dict(self._inputs),
            })
            self._in_form = False


def parse_forms(html):
    p = FormParser()
    p.feed(html)
    return p.forms


def die(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def read_password():
    if sys.stdin.isatty():
        return getpass.getpass("SSO password: ")
    return sys.stdin.readline().rstrip("\n")


def get_status():
    """Return the parsed 'netbird status --json' output."""
    result = subprocess.run(
        ["netbird", "status", "--json"], capture_output=True, text=True,
    )
    if result.returncode != 0:
        die("cannot reach the netbird daemon (is the service running?)")
    return json.loads(result.stdout)


def check_tunnel(status):
    """Verify the NetBird tunnel is up before attempting to extend."""
    mgmt = status.get("management", {})
    if not mgmt.get("connected"):
        die("tunnel is not connected; run 'netbird up' or connect via the GUI first")


def start_netbird_login(management_url):
    """Start 'netbird login --extend --no-browser' and return (proc, auth_url)."""
    proc = subprocess.Popen(
        [
            "netbird", "login", "--extend", "--no-browser",
            "--management-url", management_url,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    for line in proc.stdout:
        stripped = line.strip()
        if stripped.startswith("https://"):
            return proc, stripped
        if "already" in stripped.lower():
            print(stripped)
            proc.wait()
            sys.exit(0)

    proc.terminate()
    die("no auth URL received from netbird")


def sso_authenticate(auth_url, username, password):
    """Drive the Dex -> Keycloak SSO flow headlessly. Returns on success."""
    session = requests.Session()

    resp = session.get(auth_url)

    # Keycloak returns 401 with a Kerberos fallback form that auto-submits
    if resp.status_code == 401 or "Kerberos" in resp.text:
        forms = parse_forms(resp.text)
        if not forms:
            die("unexpected Kerberos fallback page (no form found)")
        resp = session.post(forms[0]["action"], data=forms[0]["inputs"])

    # Find and submit the login form
    forms = parse_forms(resp.text)
    login_form = next((f for f in forms if "username" in f["inputs"]), None)
    if not login_form:
        die("login form not found in SSO response")

    login_form["inputs"]["username"] = username
    login_form["inputs"]["password"] = password
    resp = session.post(login_form["action"], data=login_form["inputs"])

    if resp.status_code == 401:
        die("invalid credentials")

    if resp.status_code >= 400:
        die(f"SSO returned HTTP {resp.status_code}")

    # Keycloak re-renders the login form on bad credentials
    forms = parse_forms(resp.text)
    if forms and any("username" in f["inputs"] for f in forms):
        die("invalid credentials")

    if forms and any("otp" in f["inputs"] or "totp" in f["inputs"] for f in forms):
        die("TOTP/MFA required (not supported)")


def print_session_expiry():
    result = subprocess.run(
        ["netbird", "status"], capture_output=True, text=True,
    )
    for line in result.stdout.splitlines():
        if "Session expires" in line:
            print(line.strip())
            return


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument(
        "--username",
        default=os.environ.get("RH_NETBIRD_USERNAME"),
        help="Red Hat Kerberos ID (e.g. jdoe) [env: RH_NETBIRD_USERNAME]",
    )
    args = ap.parse_args()

    if not args.username:
        ap.error("--username is required (or set RH_NETBIRD_USERNAME)")

    status = get_status()
    check_tunnel(status)
    management_url = status["management"]["url"]

    password = read_password()
    if not password:
        ap.error("no password provided")
    proc, auth_url = start_netbird_login(management_url)
    try:
        sso_authenticate(auth_url, args.username, password)
    finally:
        proc.wait(timeout=15)

    if proc.returncode == 0:
        print_session_expiry()
    else:
        die(f"netbird exited {proc.returncode}")


if __name__ == "__main__":
    main()
