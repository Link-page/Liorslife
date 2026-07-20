import os
import json
import requests

CLIENT_ID = os.environ.get("KICK_CLIENT_ID")
CLIENT_SECRET = os.environ.get("KICK_CLIENT_SECRET")
REFRESH_TOKEN = os.environ.get("KICK_REFRESH_TOKEN")  # NEW - see get_kick_refresh_token.py
CHANNEL_SLUG = "liorslife"  # שנה לשם הערוץ שלך אם צריך


def get_app_access_token():
    """
    App Access Token (client_credentials grant).
    Fine for /public/v1/channels — Kick's own API spec lists AppAccessToken
    as an accepted auth method for that endpoint.
    """
    resp = requests.post(
        "https://id.kick.com/oauth/token",
        data={
            "grant_type": "client_credentials",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        },
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def get_user_access_token():
    """
    User Access Token (refresh_token grant).
    REQUIRED for /public/v1/kicks/leaderboard — per Kick's own API spec
    (https://api.kick.com/swagger/doc.yaml), that endpoint ONLY accepts a
    UserAccessToken with the 'kicks:read' scope. An app (client_credentials)
    token is not a valid option for it at all, no matter what — that's why
    this endpoint was always failing before.

    KICK_REFRESH_TOKEN is obtained once, manually, by running
    get_kick_refresh_token.py on your own computer and saving the printed
    refresh_token as a GitHub secret.
    """
    if not REFRESH_TOKEN:
        return None
    resp = requests.post(
        "https://id.kick.com/oauth/token",
        data={
            "grant_type": "refresh_token",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "refresh_token": REFRESH_TOKEN,
        },
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()

    new_refresh = data.get("refresh_token")
    if new_refresh and new_refresh != REFRESH_TOKEN:
        # Kick's refresh token uses a sliding expiry window. If it ever comes
        # back with a *different* value, the GitHub secret needs updating or
        # the leaderboard will start failing again once the old one expires.
        print(
            "NOTE: Kick returned a new refresh_token. Update the "
            "KICK_REFRESH_TOKEN GitHub secret to the value below:"
        )
        print(new_refresh)

    return data["access_token"]


def fetch_and_save():
    if not CLIENT_ID or not CLIENT_SECRET:
        print("Missing KICK_CLIENT_ID / KICK_CLIENT_SECRET environment variables.")
        return

    # ---------------------------------------------------------------
    # 1. Live status — works fine with an App Access Token
    # ---------------------------------------------------------------
    try:
        app_token = get_app_access_token()
    except Exception as e:
        print("Error getting app access token:", e)
        app_token = None

    live_status = {"is_live": False}
    if app_token:
        try:
            res = requests.get(
                "https://api.kick.com/public/v1/channels",
                headers={"Authorization": f"Bearer {app_token}"},
                params={"slug": CHANNEL_SLUG},
                timeout=10,
            )
            if res.status_code == 200:
                data = res.json().get("data", [])
                if data:
                    live_status["is_live"] = bool(
                        data[0].get("stream", {}).get("is_live", False)
                    )
            else:
                print(f"Failed to fetch channel: {res.status_code} — {res.text[:300]}")
        except Exception as e:
            print("Error fetching live status:", e)

    with open("live_status.json", "w", encoding="utf-8") as f:
        json.dump(live_status, f)

    # ---------------------------------------------------------------
    # 2. KICKs leaderboard — REQUIRES a user token with 'kicks:read'
    # ---------------------------------------------------------------
    try:
        user_token = get_user_access_token()
    except Exception as e:
        print("Error getting user access token (refresh_token grant):", e)
        user_token = None

    if not user_token:
        print(
            "No usable user access token (KICK_REFRESH_TOKEN missing/invalid). "
            "The kicks leaderboard endpoint requires a user token with the "
            "'kicks:read' scope — an app token cannot access it, ever. "
            "Run get_kick_refresh_token.py once locally to fix this."
        )
        if not os.path.exists("leaderboard.json"):
            with open("leaderboard.json", "w", encoding="utf-8") as f:
                json.dump({}, f)
        return

    try:
        res = requests.get(
            "https://api.kick.com/public/v1/kicks/leaderboard",
            headers={"Authorization": f"Bearer {user_token}"},
            params={"top": 10},
            timeout=10,
        )
        if res.status_code == 200:
            with open("leaderboard.json", "w", encoding="utf-8") as f:
                json.dump(res.json(), f)
        else:
            print(
                f"Failed to fetch kicks leaderboard: {res.status_code} — {res.text[:300]}"
            )
            if not os.path.exists("leaderboard.json"):
                with open("leaderboard.json", "w", encoding="utf-8") as f:
                    json.dump({}, f)
    except Exception as e:
        print("Error fetching kicks leaderboard:", e)
        if not os.path.exists("leaderboard.json"):
            with open("leaderboard.json", "w", encoding="utf-8") as f:
                json.dump({}, f)


if __name__ == "__main__":
    fetch_and_save()
