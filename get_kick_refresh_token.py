"""
Run this ONCE, on your own computer (NOT inside GitHub Actions), to get a Kick
refresh_token that has the 'kicks:read' scope. The KICKs leaderboard endpoint
can only ever be read with a user token that has this scope — an app token
(client_id/secret alone) cannot access it, by design on Kick's side.

Before running:
  1. Go to kick.com -> Settings -> Developer -> your app (the one whose
     client_id/secret you're already using for KICK_CLIENT_ID / KICK_CLIENT_SECRET).
  2. Add this exact Redirect URI to the app:  http://localhost:8080/callback
  3. pip install requests

Then run:  python get_kick_refresh_token.py
It will open your browser, ask you to log in to Kick as LiorsLife and approve
access, then print a refresh_token. Copy that value into a new GitHub secret
named KICK_REFRESH_TOKEN (Settings -> Secrets and variables -> Actions).
"""
import base64
import hashlib
import http.server
import secrets
import threading
import urllib.parse
import webbrowser

import requests

CLIENT_ID = input("Kick Client ID: ").strip()
CLIENT_SECRET = input("Kick Client Secret: ").strip()
REDIRECT_URI = "http://localhost:8080/callback"
SCOPE = "kicks:read"

code_verifier = secrets.token_urlsafe(64)
code_challenge = (
    base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest())
    .decode()
    .rstrip("=")
)
state = secrets.token_urlsafe(16)

auth_url = "https://id.kick.com/oauth/authorize?" + urllib.parse.urlencode(
    {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPE,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
)

received = {}


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        qs = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(qs)
        received["code"] = params.get("code", [None])[0]
        received["state"] = params.get("state", [None])[0]
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(
            "<h2>Done — you can close this tab and go back to the terminal.</h2>".encode()
        )

    def log_message(self, *args):
        pass  # keep the terminal quiet


server = http.server.HTTPServer(("localhost", 8080), Handler)
threading.Thread(target=server.handle_request, daemon=True).start()

print("\nOpening your browser to log in to Kick and authorize the app...")
print("If it doesn't open automatically, visit this URL manually:\n")
print(auth_url + "\n")
webbrowser.open(auth_url)

print("Waiting for you to finish logging in / approving in the browser...")
while "code" not in received:
    pass

server.server_close()

if received.get("state") != state:
    raise SystemExit("State mismatch — possible CSRF, aborting.")

if not received.get("code"):
    raise SystemExit("No authorization code received — did you click 'Approve'?")

resp = requests.post(
    "https://id.kick.com/oauth/token",
    data={
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "code": received["code"],
        "code_verifier": code_verifier,
    },
    timeout=10,
)
resp.raise_for_status()
tokens = resp.json()

print("\n✅ Success! Copy the value below into a new GitHub secret named KICK_REFRESH_TOKEN:\n")
print(tokens["refresh_token"])
print("\n(This refresh token stays valid indefinitely as long as the workflow")
print("keeps running at least once every ~30 days — the expiry resets on each use.)")
