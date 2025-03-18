import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Button, View
import sqlite3
import requests
import os
from dotenv import load_dotenv
import base64
from nacl import encoding, public

load_dotenv()

SECRET_NAME = os.getenv("GITHUB_SECRET_NAME")

DATABASE_PATH = os.path.join("database", "database.db")
conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
cursor = conn.cursor()

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

    @app_commands.command(name="add_repo", description="Ajoutez un dépôt GitHub à votre profil.")
    @app_commands.describe(repo_name="Nom du dépôt GitHub (format : owner/repo)", channel="Salon Discord pour les notifications")
    async def add_repo(self, interaction: discord.Interaction, repo_name: str, channel: discord.TextChannel):
        await interaction.response.defer(ephemeral=False)
        discord_id = str(interaction.user.id)
        try:
            cursor.execute('SELECT github_token FROM Users WHERE id = ?', (discord_id,))
            result = cursor.fetchone()
            if result:
                github_token = result[0]
                if self.check_repo_exists(repo_name, github_token):
                    webhook = await self.create_discord_webhook(channel, repo_name, github_token)
                    if webhook:
                        webhook_url = webhook.url
                        if self.create_github_secret(repo_name, github_token, SECRET_NAME, webhook_url):
                            await self.create_github_workflow(interaction)
                            cursor.execute('''
                            INSERT OR IGNORE INTO UserRepos (discord_id, repo_name, webhook_url)
                            VALUES (?, ?, ?)
                            ''', (discord_id, repo_name, webhook_url))
                            conn.commit()
                            if cursor.rowcount > 0:
                                await interaction.followup.send(
                                    f"Le dépôt `{repo_name}` a été ajouté à votre profil. Les notifications seront envoyées dans {channel.mention} après que vous ayez ajouté le fichier .yml dans votre repo.",
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
            print(f"❌ Erreur dans la commande /add_repo : {e}")
            await interaction.followup.send(
                "Une erreur s'est produite lors de l'ajout du dépôt.",
                ephemeral=True
            )

    def check_repo_exists(self, repo_name, github_token):
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
        try:
            existing_webhooks = await channel.webhooks()
            for webhook in existing_webhooks:
                if webhook.name == repo_name:
                    return webhook
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
            print(f"Webhook créé pour le dépôt {repo_name}: {webhook.url}")
            return webhook
        except Exception as e:
            print(f"Erreur lors de la création du webhook Discord : {e}")
            return None


    def get_repo_info(self, repo_name, github_token):
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
        public_key = public.PublicKey(public_key.encode("utf-8"), encoding.Base64Encoder())
        sealed_box = public.SealedBox(public_key)
        encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
        return base64.b64encode(encrypted).decode("utf-8")

    def create_github_secret(self, repo_name, github_token, secret_name, secret_value):
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
            name="2️⃣ Ajouter le fichier `notify-discord.yml`",
            value="Dans `.github/workflows`, ajoutez le fichier nommé `notify-discord.yml` disponible en pièce jointe.",
            inline=False
        )

        file = discord.File(".github/workflows/notify-discord.yml")
        await interaction.followup.send("📄 Mettez ce fichier YAML dans le dossier  :", file=file)


        embed.set_footer(text="Cliquez sur le bouton ci-dessous lorsque vous avez terminé toutes les étapes.")
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AddRepo(bot))
