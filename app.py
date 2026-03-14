from flask import Flask, jsonify
import json
import os
import requests as req

app = Flask(__name__)

# ── YOUR GITHUB DETAILS ────────────────────────
GITHUB_USERNAME = "saikumar47412"       # your GitHub username
GITHUB_REPO     = "cloud-cost-dashboard" # your repo name
GITHUB_BRANCH   = "main"
DATA_FILE_PATH  = "data.json"
# ──────────────────────────────────────────────

RAW_URL = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{GITHUB_REPO}/{GITHUB_BRANCH}/{DATA_FILE_PATH}"

@app.route("/")
def index():
    with open("templates/index.html", "r") as f:
        return f.read()

@app.route("/api/data")
def get_data():
    try:
        token = os.environ.get("GITHUB_TOKEN", "")
        headers = {"Authorization": f"token {token}"} if token else {}
        response = req.get(RAW_URL, timeout=10, headers=headers)
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({"error": f"Could not fetch data.json from GitHub (status {response.status_code}). Please upload data.json to your GitHub repo."})
    except Exception as e:
        return jsonify({"error": f"Error fetching data: {str(e)}"})

if __name__ == "__main__":
    import os port = int(os.environ.get("PORT", 5000)) app.run(host="0.0.0.0", port=port)
