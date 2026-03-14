from flask import Flask, jsonify, render_template_string
import json
import os

app = Flask(__name__)
DATA_FILE = "data.json"

@app.route("/")
def index():
    with open("templates/index.html", "r") as f:
        return f.read()

@app.route("/api/data")
def get_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return jsonify(json.load(f))
    return jsonify({"error": "No data available yet. Please run the script."})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
