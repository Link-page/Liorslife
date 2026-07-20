import os
import json
import requests

CLIENT_ID = os.environ.get("KICK_CLIENT_ID")
CLIENT_SECRET = os.environ.get("KICK_CLIENT_SECRET")
CHANNEL_SLUG = "liorslife"  # שנה לשם הערוץ שלך אם צריך


def get_access_token():
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


def fetch_and_save():
    if not CLIENT_ID or not CLIENT_SECRET:
        print("Missing KICK_CLIENT_ID / KICK_CLIENT_SECRET environment variables.")
        return

    try:
        token = get_access_token()
    except Exception as e:
        print("Error getting access token:", e)
        return

    headers = {"Authorization": f"Bearer {token}"}

    # 1. סטטוס לייב
    live_status = {"is_live": False}
    try:
        res = requests.get(
            "https://api.kick.com/public/v1/channels",
            headers=headers,
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

    # 2. לידרבורד ה-Kicks (מטבע המתנות של קיק)
    # שים לב: אין כרגע endpoint רשמי ללידרבורד סאבים/מתנות (subs.json) --
    # רק ללידרבורד ה-Kicks עצמו. אם קיק יוסיפו endpoint כזה בעתיד, אפשר להוסיף בלוק דומה.
    try:
        res = requests.get(
            "https://api.kick.com/public/v1/kicks/leaderboard",
            headers=headers,
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
