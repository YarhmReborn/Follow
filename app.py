from flask import Flask, render_template, request, redirect, url_for, jsonify
import uuid
import requests
from supabase import create_client

SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your-supabase-key"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

CLIENT_KEY = "awhxqbcrzn6drte4"
CLIENT_SECRET = "9HFMeBBtUDdlRMD8YdNUE2UcqALtvHM9"

app = Flask(__name__)

def get_tiktok_token():
    url = "https://open.tiktokapis.com/v2/oauth/token/"
    data = {
        "client_key": CLIENT_KEY,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials"
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(url, data=data, headers=headers)
    return response.json().get("access_token")

@app.route("/", methods=["GET", "POST"])
def create_link():
    if request.method == "POST":
        reward_link = request.form["reward_link"]
        tiktok_username = request.form["tiktok_username"]
        unique_id = str(uuid.uuid4())[:8]
        supabase.table("reward_links").insert({
            "id": unique_id,
            "reward_link": reward_link,
            "tiktok_username": tiktok_username,
            "completed_count": 0
        }).execute()
        return redirect(url_for("unlock_page", uid=unique_id))
    return render_template("create_link.html")

@app.route("/unlock/<uid>")
def unlock_page(uid):
    data = supabase.table("reward_links").select("*").eq("id", uid).execute()
    if len(data.data) == 0:
        return "Invalid Link"
    return render_template("unlock_page.html", **data.data[0])

@app.route("/check_follow", methods=["POST"])
def check_follow():
    req = request.get_json()
    target = req.get("target")
    user = req.get("user")
    uid = req.get("uid")
    token = get_tiktok_token()
    if not token:
        return jsonify({"error": "TikTok token fetch failed"}), 500

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    json_data = {"username": target, "max_count": 100}
    response = requests.post(
        "https://open.tiktokapis.com/v2/research/user/followers/",
        headers=headers, json=json_data
    )

    followers = response.json().get("data", {}).get("user_followers", [])
    usernames = [f["username"] for f in followers]
    followed = user in usernames

    if followed:
        current = supabase.table("reward_links").select("completed_count").eq("id", uid).execute().data[0]["completed_count"]
        supabase.table("reward_links").update({"completed_count": current + 1}).eq("id", uid).execute()

    return jsonify({"followed": followed})

if __name__ == "__main__":
    app.run(debug=True)
