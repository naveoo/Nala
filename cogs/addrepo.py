import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Button, View
import sqlite3
import requests
import os
from dotenv import load_dotenv
import secrets
import base64
from nacl import encoding, public
import asyncio
import time

# Charger les variables d'environnement
load_dotenv()

# Connexion à la base de données
DATABASE_PATH = os.path.join("database", "database.db")
conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
cursor = conn.cursor()

# Vérifier si la colonne webhook_url existe dans la table UserRepos
try:
    cursor.execute("PRAGMA table_info(UserRepos)")
    columns = cursor.fetchall()
    
    webhook_url_exists = False
    for column in columns:
        if column[1] == 'webhook_url':
            webhook_url_exists = True
            break
            
    if not webhook_url_exists:
        print("⚠️ Ajout de la colonne webhook_url à la table UserRepos...")
        cursor.execute("ALTER TABLE UserRepos ADD COLUMN webhook_url TEXT")
        conn.commit()
        print("✅ Colonne webhook_url ajoutée avec succès.")
except Exception as e:
    print(f"❌ Erreur lors de la vérification/ajout de la colonne webhook_url: {e}")

class AddRepo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="addrepo", description="Ajoutez un dépôt GitHub à votre profil.")
    @app_commands.describe(repo_name="Nom du dépôt GitHub (format : owner/repo)", channel="Salon Discord pour les notifications")
    async def addrepo(self, interaction: discord.Interaction, repo_name: str, channel: discord.TextChannel):
        # Différer la réponse pour éviter l'expiration de l'interaction
        await interaction.response.defer(ephemeral=False)

        discord_id = str(interaction.user.id)

        try:
            # Récupérer le token GitHub de l'utilisateur
            cursor.execute('SELECT github_token FROM Users WHERE id = ?', (discord_id,))
            result = cursor.fetchone()

            if result:
                github_token = result[0]

                # Vérifier si le dépôt existe
                if self.check_repo_exists(repo_name, github_token):
                    # Créer un webhook Discord dans le salon spécifié
                    webhook = await self.create_discord_webhook(channel, repo_name, github_token)

                    if webhook:
                        webhook_url = webhook.url

                        # Créer un secret GitHub Actions avec l'URL du webhook Discord
                        if self.create_github_secret(repo_name, github_token, "DISCORD_WEBHOOK_URL", webhook_url):
                            # Créer le fichier de workflow GitHub Actions
                            await self.create_github_workflow(interaction)
                            cursor.execute('''
                            INSERT OR IGNORE INTO UserRepos (discord_id, repo_name, webhook_url)
                            VALUES (?, ?, ?)
                            ''', (discord_id, repo_name, webhook_url))
                            conn.commit()

                            if cursor.rowcount > 0:
                                await interaction.followup.send(
                                    f"Le dépôt `{repo_name}` a été ajouté à votre profil. Les notifications seront envoyées dans {channel.mention}.",
                                    ephemeral=True
                                )
                            else:
                                await interaction.followup.send(
                                    f"Vous suivez déjà le dépôt `{repo_name}`.",
                                    ephemeral=True
                                )
                        else:
                            await interaction.followup.send(
                                "Erreur lors de la création du secret GitHub.",
                                ephemeral=True
                            )
                    else:
                        await interaction.followup.send(
                            "Erreur lors de la création du webhook Discord.",
                            ephemeral=True
                        )
                else:
                    await interaction.followup.send(
                        f"Le dépôt `{repo_name}` n'existe pas ou vous n'y avez pas accès.",
                        ephemeral=True
                    )
            else:
                await interaction.followup.send(
                    "Vous n'êtes pas encore enregistré.",
                    ephemeral=True
                )
        except Exception as e:
            print(f"❌ Erreur dans la commande /addrepo : {e}")
            await interaction.followup.send(
                "Une erreur s'est produite lors de l'ajout du dépôt.",
                ephemeral=True
            )

    def check_repo_exists(self, repo_name, github_token):
        """
        Vérifie si le dépôt existe et est accessible avec le token GitHub fourni.
        """
        try:
            url = f"https://api.github.com/repos/{repo_name}"
            headers = {
                "Authorization": f"token {github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            response = requests.get(url, headers=headers)
            return response.status_code == 200
        except Exception as e:
            print(f"Erreur lors de la vérification du dépôt : {e}")
            return False

    async def create_discord_webhook(self, channel, repo_name, github_token):
        """
        Crée un webhook Discord dans le salon spécifié.
        """
        try:
            repo_info = self.get_repo_info(repo_name, github_token)
            if not repo_info:
                return None

            avatar_url = repo_info["owner"]["avatar_url"]
            repo_icon = requests.get(avatar_url).content
            webhook = await channel.create_webhook(
                name=repo_name,
                avatar=repo_icon,
                reason=f"Webhook pour les notifications du dépôt {repo_name}"
            )
            return webhook
        except Exception as e:
            print(f"Erreur lors de la création du webhook Discord : {e}")
            return None

    def get_repo_info(self, repo_name, github_token):
        """
        Récupère les informations du dépôt GitHub.
        """
        try:
            url = f"https://api.github.com/repos/{repo_name}"
            headers = {
                "Authorization": f"token {github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            response = requests.get(url, headers=headers)
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            print(f"Erreur lors de la récupération des informations du dépôt : {e}")
            return None

    def encrypt_secret(self, public_key: str, secret_value: str) -> str:
        """
        Chiffre un secret avec la clé publique GitHub.
        """
        public_key = public.PublicKey(public_key.encode("utf-8"), encoding.Base64Encoder())
        sealed_box = public.SealedBox(public_key)
        encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
        return base64.b64encode(encrypted).decode("utf-8")

    def create_github_secret(self, repo_name, github_token, secret_name, secret_value):
        """
        Crée un secret GitHub Actions dans le dépôt.
        """
        try:
            url = f"https://api.github.com/repos/{repo_name}/actions/secrets/public-key"
            headers = {
                "Authorization": f"token {github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            response = requests.get(url, headers=headers)
            public_key = response.json()["key"]
            key_id = response.json()["key_id"]
            encrypted_secret = self.encrypt_secret(public_key, secret_value)
            url = f"https://api.github.com/repos/{repo_name}/actions/secrets/{secret_name}"
            payload = {
                "encrypted_value": encrypted_secret,
                "key_id": key_id
            }
            response = requests.put(url, json=payload, headers=headers)
            return response.status_code == 201 or response.status_code == 204
        except Exception as e:
            print(f"Erreur lors de la création du secret GitHub : {e}")
            return False

    async def create_github_workflow(self, interaction):
        # Création de l'embed
        embed = discord.Embed(
            title="📌 Instructions pour configurer GitHub Actions",
            description="Voici comment ajouter un workflow GitHub Actions pour recevoir des notifications sur Discord.",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="1️⃣ Créer le dossier `.github/workflows/`",
            value="Dans votre dépôt GitHub, créez un dossier `.github/workflows/` si ce n'est pas encore fait.",
            inline=False
        )
        embed.add_field(
            name="2️⃣ Ajouter un fichier `notify-discord.yml`",
            value="Dans `.github/workflows`, créez un fichier nommé `notify-discord.yml`.",
            inline=False
        )
        embed.add_field( name="3️⃣ Ajouter ce contenu au fichier `notify-discord.yml`", value=""
        "```yaml\n" 
        "name: Notify Discord on Commit\n" 
        "on:\n" 
        " push:\n" 
        " branches:\n" 
        " - main\n" 
        "jobs:\n" 
        " notify:\n" 
        " runs-on: ubuntu-latest\n" 
        " steps:\n" 
        " - name: Send Discord Notification\n" 
        " uses: appleboy/discord-action@master\n" 
        " with:\n" 
        " webhook_url: ${{ secrets.DISCORD_WEBHOOK_URL }}\n" 
        " message: |\n" 
        " Nouveau commit sur **${{ github.repository }}** par **${{ github.actor }}** :\n" 
        " - **Message** : ${{ github.event.head_commit.message }}\n" 
        " - **Lien** : ${{ github.event.head_commit.url }}\n" 
        "```"
        , inline=False )
        embed.set_footer(text="Cliquez sur le bouton ci-dessous lorsque vous avez terminé toutes les étapes.")

        # Création du bouton
        button = Button(label="✅ J'ai terminé", style=discord.ButtonStyle.success)

        # Définition de l'action après un clic sur le bouton
        async def button_callback(interaction_button: discord.Interaction):
            await interaction_button.response.send_message("Merci ! Vous avez validé les étapes. 🎉")
            # Vous pouvez inclure ici la suite logique de votre commande

        button.callback = button_callback

        # Ajout du bouton à une vue
        view = View()
        view.add_item(button)

        # Envoi de l'embed avec le bouton
        await interaction.followup.send(embed=embed, view=view)

# Fonction pour charger le cog
async def setup(bot):
    await bot.add_cog(AddRepo(bot))
