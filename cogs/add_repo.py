import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import requests
import os
import traceback
from dotenv import load_dotenv

load_dotenv()

SECRET_NAME = os.getenv("GITHUB_SECRET_NAME")

DATABASE_PATH = os.path.join("database", "database.db")
conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
cursor = conn.cursor()

class AddRepo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logs_channel = None  # Initialisation différée

    async def cog_load(self):
        """S'exécute après le chargement du cog."""
        await self.bot.wait_until_ready()
        self.logs_channel = self.bot.get_channel(int(os.getenv("LOGS_CHANNEL")))

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
                if await self.check_repo_exists(repo_name, github_token):
                    webhook = await self.create_discord_webhook(channel, repo_name, github_token)
                    if webhook:
                        webhook_url = webhook.url
                        if await self.create_github_secret(repo_name, github_token, SECRET_NAME, webhook_url):
                            await self.create_github_workflow(interaction)
                            cursor.execute('''
                            INSERT OR IGNORE INTO UserRepos (discord_id, repo_name, webhook_url)
                            VALUES (?, ?, ?)
                            ''', (discord_id, repo_name, webhook_url))
                            conn.commit()
                            message = (f"Le dépôt `{repo_name}` a été ajouté à votre profil. "
                                       f"Les notifications seront envoyées dans {channel.mention} après que vous ayez ajouté le fichier .yml dans votre repo." 
                                       if cursor.rowcount > 0 else f"Vous suivez déjà le dépôt `{repo_name}`.")
                            await interaction.followup.send(message, ephemeral=True)
                        else:
                            await interaction.followup.send("Erreur lors de la création du secret GitHub.", ephemeral=True)
                    else:
                        await interaction.followup.send("Erreur lors de la création du webhook Discord.", ephemeral=True)
                else:
                    await interaction.followup.send(f"Le dépôt `{repo_name}` n'existe pas ou vous n'y avez pas accès.", ephemeral=True)
            else:
                await interaction.followup.send("Vous n'êtes pas encore enregistré.", ephemeral=True)
        except Exception as e:
            await self.log_error("/add_repo", interaction, e)
            if not interaction.response.is_done():
                await interaction.followup.send("Une erreur s'est produite lors de l'ajout du dépôt.", ephemeral=True)

    async def check_repo_exists(self, repo_name, github_token):
        try:
            url = f"https://api.github.com/repos/{repo_name}"
            headers = {"Authorization": f"token {github_token}", "Accept": "application/vnd.github.v3+json"}
            response = requests.get(url, headers=headers)
            return response.status_code == 200
        except Exception as e:
            await self.log_error("/add_repo - check_repo_exists", None, e)
            return False

    async def create_discord_webhook(self, channel, repo_name, github_token):
        try:
            existing_webhooks = await channel.webhooks()
            for webhook in existing_webhooks:
                if webhook.name == repo_name:
                    return webhook
            repo_info = await self.get_repo_info(repo_name, github_token)
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
            await self.log_error("/add_repo - create_discord_webhook", None, e)
            return None

    async def create_github_secret(self, repo_name, github_token, secret_name, secret_value):
        try:
            url = f"https://api.github.com/repos/{repo_name}/actions/secrets/public-key"
            headers = {"Authorization": f"token {github_token}", "Accept": "application/vnd.github.v3+json"}
            response = requests.get(url, headers=headers)
            public_key = response.json()["key"]
            key_id = response.json()["key_id"]
            encrypted_secret = self.encrypt_secret(public_key, secret_value)
            url = f"https://api.github.com/repos/{repo_name}/actions/secrets/{secret_name}"
            payload = {"encrypted_value": encrypted_secret, "key_id": key_id}
            response = requests.put(url, json=payload, headers=headers)
            return response.status_code in [201, 204]
        except Exception as e:
            await self.log_error("/add_repo - create_github_secret", None, e)
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
        await interaction.followup.send(embed=embed)

    async def log_error(self, command, interaction, error):
        if not self.logs_channel:
            print("Erreur : Canal de logs introuvable.")
            return
        embed = discord.Embed(title=f"Erreur dans la commande {command}",
                              description=f"Utilisateur : {interaction.user.name if interaction else 'N/A'} ({interaction.user.id if interaction else 'N/A'})" if interaction else "", color=discord.Color.red())
        error_details = traceback.format_exc() or str(error)
        if len(error_details) > 1990:
            error_details = error_details[:1990] + "...\n(tronqué)"
        embed.add_field(name="Détails de l'erreur", value=f"```{error_details}```", inline=False)
        await self.logs_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AddRepo(bot))