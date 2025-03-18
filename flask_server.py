from quart import Quart, request, jsonify
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

def create_quart_app(bot):
    app = Quart(__name__)

    @app.route("/")
    async def home(): 
        return "Hello, world!"

    @app.route("/callback")
    async def callback():
        code = request.args.get("code")
        state = request.args.get("state")
        if not code or not state:
            return "Erreur : Paramètres manquants."

        # Vérifier l'état dans la base de données
        cursor.execute('SELECT discord_id FROM PendingRegistrations WHERE state = ?', (state,))
        result = cursor.fetchone()
        if not result:
            return "Erreur : State invalide."
        discord_id = result[0]

        # Obtenir le token GitHub
        token = await get_github_token(code)
        if not token:
            return "Erreur : Impossible de récupérer le token."

        # Récupérer le nom d'utilisateur GitHub
        github_username = await get_github_username(token)
        if not github_username:
            return "Erreur : Impossible de récupérer le nom d'utilisateur GitHub."

        # Sauvegarder les informations dans la base de données
        save_github_info(discord_id, github_username, token)
        cursor.execute('DELETE FROM PendingRegistrations WHERE state = ?', (state,))
        conn.commit()

        return "Authentification réussie ! Votre compte GitHub est maintenant lié."

    async def get_github_token(code):
        url = "https://github.com/login/oauth/access_token"
        payload = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": code,
            "redirect_uri": REDIRECT_URI
        }
        headers = {"Accept": "application/json"}
        async with requests.Session() as session:
            response = await session.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                return response.json().get("access_token")
            return None

    async def get_github_username(token):
        url = "https://api.github.com/user"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/json"
        }
        async with requests.Session() as session:
            response = await session.get(url, headers=headers)
            if response.status_code == 200:
                return response.json().get("login")
            return None

    def save_github_info(discord_id, github_username, token):
        cursor.execute('''
        INSERT OR REPLACE INTO Users (id, github_username, github_token)
        VALUES (?, ?, ?)
        ''', (discord_id, github_username, token))
        conn.commit()

    return app
