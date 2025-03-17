from flask import Flask, request, jsonify
import requests
import sqlite3
from dotenv import load_dotenv
import os
import discord
import asyncio
import hmac
import hashlib

# Charger les variables d'environnement
load_dotenv()

# Configuration GitHub
CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
REDIRECT_URI = os.getenv("GITHUB_REDIRECT_URI")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# Chemin de la base de données
DATABASE_PATH = os.path.join("database", "database.db")
conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
cursor = conn.cursor()

def create_flask_app(bot):
    app = Flask(__name__)

    # Middleware pour ajouter automatiquement l'en-tête "ngrok-skip-browser-warning"
    @app.after_request
    def add_ngrok_header(response):
        response.headers["ngrok-skip-browser-warning"] = "true"
        return response

    @app.route("/")
    def home():
        return "Hello, world!"

    # Route pour gérer le callback GitHub OAuth
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

    # Route pour gérer les webhooks GitHub
    @app.route('/github_webhook', methods=['POST'])
    def github_webhook():
        signature = request.headers.get('X-Hub-Signature-256')
        payload = request.get_data()
        repo_name = request.json['repository']['full_name']

        cursor.execute('SELECT discord_id, webhook_secret FROM UserRepos WHERE repo_name = ?', (repo_name,))
        result = cursor.fetchone()
        if result:
            discord_id, webhook_secret = result
            if not verify_webhook_signature(webhook_secret, payload, signature):
                return "Signature invalide", 403

            event = request.headers.get('X-GitHub-Event')
            if event == 'push':
                commits = request.json['commits']
                commit_messages = [commit['message'] for commit in commits]
                message = f"🔔 Nouveau(s) commit(s) dans `{repo_name}`:\n" + "\n".join(commit_messages)
            elif event == 'pull_request':
                pr_action = request.json['action']
                pr_title = request.json['pull_request']['title']
                message = f"🔔 Pull Request dans `{repo_name}`: {pr_title} ({pr_action})"
            else:
                return "Événement non géré", 200

            send_discord_dm(bot, discord_id, message)
            return jsonify({"message": "Webhook reçu"}), 200
        else:
            return "Dépôt non trouvé", 404

    return app

# Fonction pour récupérer le token GitHub
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

# Fonction pour récupérer le nom d'utilisateur GitHub
def get_github_username(token):
    url = "https://api.github.com/user"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/json"
    }
    response = requests.get(url, headers=headers)
    return response.json().get("login") if response.status_code == 200 else None

# Fonction pour sauvegarder les informations GitHub
def save_github_info(discord_id, github_username, token):
    cursor.execute('''
    INSERT OR REPLACE INTO Users (id, github_username, github_token)
    VALUES (?, ?, ?)
    ''', (discord_id, github_username, token))
    conn.commit()

# Fonction pour vérifier la signature du webhook
def verify_webhook_signature(secret, payload, signature):
    expected_signature = 'sha256=' + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected_signature, signature)

# Fonction pour envoyer un message Discord
def send_discord_dm(bot, discord_id, message):
    user = bot.get_user(int(discord_id))
    if user:
        asyncio.run_coroutine_threadsafe(user.send(message), bot.loop)

if __name__ == "__main__":
    app = create_flask_app(None)
    app.run(host="0.0.0.0", port=5000, debug=True)