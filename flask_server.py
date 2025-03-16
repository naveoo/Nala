from flask import Flask
from github_auth import handle_callback  # Importer la fonction du fichier github_auth.py
from github_webhook import handle_github_webhook  # Importer la fonction du fichier github_webhook.py

app = Flask(__name__)

@app.route('/')
def home():
    return 'Page d\'accueil'

@app.route("/callback")
def callback():
    return handle_callback()  # Gestion du callback GitHub

@app.route("/github_webhook", methods=["POST"])
def github_webhook():
    return handle_github_webhook()  # Gestion du webhook GitHub

def start_flask_server():
    app.run(host="0.0.0.0", port=5000, debug=True)

if __name__ == "__main__":
    start_flask_server()
