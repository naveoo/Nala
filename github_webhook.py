import sqlite3
import hmac
import hashlib
import json
from requests import request
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_PATH = os.path.join("database", "database.db")
conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
cursor = conn.cursor()

GITHUB_SECRET = os.getenv("GITHUB_SECRET")  # Clé secrète pour valider les webhooks

def handle_github_webhook():
    # Vérification de la signature HMAC pour valider l'intégrité de la requête
    signature = request.headers.get("X-Hub-Signature-256")
    if not validate_signature(request.data, signature):
        return "Signature invalide", 400

    # Parsing du payload JSON envoyé par GitHub
    payload = request.get_json()

    # Logique pour envoyer un message privé à l'utilisateur
    process_webhook_payload(payload)

    return "Webhook reçu et traité avec succès."

def validate_signature(payload, signature):
    """Vérifie si la signature HMAC du webhook est valide."""
    mac = hmac.new(GITHUB_SECRET.encode(), msg=payload, digestmod=hashlib.sha256)
    expected_signature = "sha256=" + mac.hexdigest()
    return hmac.compare_digest(expected_signature, signature)

def process_webhook_payload(payload):
    """Traite les données du webhook et envoie un message privé aux utilisateurs concernés."""
    action = payload.get("action")
    repo_name = payload.get("repository", {}).get("name")
    # Exemple de message à envoyer en fonction de l'action (commit, issue, etc.)
    if action == "opened":
        message = f"Nouvelle modification sur le dépôt `{repo_name}` : une nouvelle issue a été ouverte !"
    elif action == "pushed":
        message = f"Nouvelle modification sur le dépôt `{repo_name}` : un commit a été effectué !"
    else:
        message = f"Une action a eu lieu sur le dépôt `{repo_name}`."

    # Exemple d'envoi d'un MP à un utilisateur spécifique (via un Discord bot)
    # Remplacer `discord_id` par l'ID réel de l'utilisateur (à récupérer depuis la base de données)
    discord_id = "ID_UTILISATEUR_EXEMPLE"
    send_private_message(discord_id, message)

def send_private_message(discord_id, message):
    """Envoie un message privé à l'utilisateur via le bot Discord."""
    # Logique pour envoyer le message via ton bot Discord
    pass
