from flask import Flask, request, jsonify
import requests
import sqlite3
from dotenv import load_dotenv
import os
import discord
from discord.ext import commands

load_dotenv()

CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
REDIRECT_URI = os.getenv("GITHUB_REDIRECT_URI")

GITHUB_API_URL = "https://api.github.com"
GITHUB_WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # URL de ton serveur Flask pour le webhook, ex : http://ton-serveur.com/github_webhook

app = Flask(__name__)

DATABASE_PATH = os.path.join("database", "database.db")
conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
cursor = conn.cursor()

# Configuration du bot Discord
TOKEN = os.getenv("BOT_TOKEN")
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Fonction pour créer un webhook sur GitHub
def create_github_webhook(github_token, repo_name):
    url = f"{GITHUB_API_URL}/repos/{repo_name}/hooks"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/json"
    }
    payload = {
        "name": "web",
        "active": True,
        "events": ["push", "issues", "create", "pull_request", "release"],  # Tu peux personnaliser les événements
        "config": {
            "url": GITHUB_WEBHOOK_URL,
            "content_type": "json"
        }
    }

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 201:
        print(f"Webhook créé avec succès pour {repo_name}")
        return response.json()
    else:
        print(f"Erreur lors de la création du webhook : {response.status_code}")
        return None

# Route pour recevoir les événements Webhook de GitHub
@app.route("/github_webhook", methods=["POST"])
def github_webhook():
    data = request.json
    event_type = request.headers.get("X-GitHub-Event")
    repository_name = data["repository"]["full_name"]

    # Récupérer tous les utilisateurs inscrits à ce dépôt
    cursor.execute('SELECT discord_id FROM UserRepos WHERE repo_name = ?', (repository_name,))
    user_ids = cursor.fetchall()

    if user_ids:
        for user_id in user_ids:
            discord_user_id = user_id[0]
            discord_user = bot.get_user(int(discord_user_id))
            if discord_user:
                # En fonction de l'événement, personnaliser le message
                if event_type == "push":
                    commits = data["commits"]
                    commit_messages = [commit["message"] for commit in commits]
                    message = f"🎉 Nouveau commit dans le dépôt {repository_name} :\n" + "\n".join(commit_messages)
                elif event_type == "issues":
                    issue_title = data["issue"]["title"]
                    issue_url = data["issue"]["html_url"]
                    message = f"📣 Nouvelle issue dans {repository_name} : {issue_title}\n{issue_url}"
                elif event_type == "create":
                    if data["ref_type"] == "branch":
                        branch_name = data["ref"]
                        message = f"🌿 Nouvelle branche {branch_name} créée dans {repository_name}."
                    else:
                        message = f"🔔 Nouvel événement dans {repository_name}."
                else:
                    message = f"📢 Événement {event_type} dans le dépôt {repository_name}."

                # Utiliser bot.loop.create_task() pour envoyer le message asynchrone
                bot.loop.create_task(send_dm(discord_user, message))

    return jsonify({"status": "success"}), 200

# Fonction asynchrone pour envoyer un message à l'utilisateur Discord
async def send_dm(discord_user, message):
    try:
        await discord_user.send(message)
    except discord.Forbidden:
        print(f"Impossible d'envoyer un message à {discord_user.name}.")
    except Exception as e:
        print(f"Erreur lors de l'envoi du message à {discord_user.name}: {e}")

# Route pour l'enregistrement d'un utilisateur et l'abonnement à un dépôt
@app.route("/register_repo", methods=["POST"])
def register_repo():
    discord_id = request.json.get("discord_id")
    repo_name = request.json.get("repo_name")
    github_token = request.json.get("github_token")  # Token d'accès GitHub de l'utilisateur

    # Enregistrer l'abonnement dans la base de données
    cursor.execute('INSERT INTO UserRepos (discord_id, repo_name) VALUES (?, ?)', (discord_id, repo_name))
    conn.commit()

    # Créer le webhook pour le dépôt
    result = create_github_webhook(github_token, repo_name)
    
    if result:
        return jsonify({"status": "success", "message": "Utilisateur inscrit et webhook créé."}), 200
    else:
        return jsonify({"status": "error", "message": "Erreur lors de la création du webhook."}), 500

# Démarrer le serveur Flask
def run_flask():
    app.run(host="0.0.0.0", port=5000, debug=False)
