import os
import json
import requests

API_KEY = os.environ.get("KICK_API_KEY")
CHANNEL_NAME = "liorslife"

# הגדרת ה-Headers שקיק דורשים מה-API הרשמי שלהם
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json"
}

def fetch_and_save():
    # 1. בדיקת סטטוס לייב (מול ה-API הרגיל / ערוצים)
    # שים לב: יכול להיות שנקודת הקצה ל-API רשמי שונה מ-API ציבורי, נשתמש בזה כבסיס.
    live_status = {"is_live": False}
    try:
        url = f"https://kick.com/api/v2/channels/{CHANNEL_NAME}"
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            is_live = bool(data.get("livestream", {}).get("is_live", False))
            live_status["is_live"] = is_live
    except Exception as e:
        print("Error fetching live status:", e)
        
    with open("live_status.json", "w", encoding="utf-8") as f:
        json.dump(live_status, f)

    # 2. משיכת ה-Leaderboards ל-Kicks
    # במידה ולחשבון המפתח שלך יש גישה ספציפית ל-Endpoint אחר, יש לעדכן את ה-URL
    try:
        kicks_url = f"https://kick.com/api/v2/channels/{CHANNEL_NAME}/leaderboards/kicks"
        res = requests.get(kicks_url, headers=headers, timeout=10)
        if res.status_code == 200:
            with open("leaderboard.json", "w", encoding="utf-8") as f:
                json.dump(res.json(), f)
        else:
            print("Failed to fetch kicks leaderboard:", res.status_code)
    except Exception as e:
        print("Error fetching kicks leaderboard:", e)

    # 3. משיכת ה-Subs
    try:
        subs_url = f"https://kick.com/api/v2/channels/{CHANNEL_NAME}/leaderboards/gifts"
        res = requests.get(subs_url, headers=headers, timeout=10)
        if res.status_code == 200:
            with open("subs.json", "w", encoding="utf-8") as f:
                json.dump(res.json(), f)
        else:
            print("Failed to fetch subs leaderboard:", res.status_code)
    except Exception as e:
        print("Error fetching subs leaderboard:", e)

if __name__ == "__main__":
    fetch_and_save()
