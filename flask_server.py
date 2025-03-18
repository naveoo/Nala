from flask import Flask, request, jsonify
import requests
import sqlite3
from dotenv import load_dotenv
import os

load_dotenv()

CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
REDIRECT_URI = os.getenv("GITHUB_REDIRECT_URI")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

DATABASE_PATH = os.path.join("database", "database.db")
conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
cursor = conn.cursor()

def create_flask_app(bot):
    app = Flask(__name__)

    @app.route("/")
    def home():
        return "Hello, world!"

    @app.route("/callback")
    def callback():
        code = request.args.get("code")
        state = request.args.get("state")
        if not code or not state:
            return "Erreur : Paramètres manquants."

        cursor.execute('SELECT discord_id FROM PendingRegistrations WHERE state = ?', (state,))
        result = cursor.fetchone()
        if not result:
            return "Erreur : State invalide."
        discord_id = result[0]

        token = get_github_token(code)
        if not token:
            return "Erreur : Impossible de récupérer le token."

        github_username = get_github_username(token)
        if not github_username:
            return "Erreur : Impossible de récupérer le nom d'utilisateur GitHub."

        save_github_info(discord_id, github_username, token)
        cursor.execute('DELETE FROM PendingRegistrations WHERE state = ?', (state,))
        conn.commit()

        return "Authentification réussie ! Votre compte GitHub est maintenant lié."

    def get_github_token(code):
        url = "https://github.com/login/oauth/access_token"
        payload = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": code,
            "redirect_uri": REDIRECT_URI
        }
        headers = {"Accept": "application/json"}
        response = requests.post(url, json=payload, headers=headers)
        return response.json().get("access_token") if response.status_code == 200 else None

    def get_github_username(token):
        url = "https://api.github.com/user"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/json"
        }
        response = requests.get(url, headers=headers)
        return response.json().get("login") if response.status_code == 200 else None

    def save_github_info(discord_id, github_username, token):
        cursor.execute('''
        INSERT OR REPLACE INTO Users (id, github_username, github_token)
        VALUES (?, ?, ?)
        ''', (discord_id, github_username, token))
        conn.commit()

    return app

def run_flask_in_thread(bot):
    app = create_flask_app(bot)
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
