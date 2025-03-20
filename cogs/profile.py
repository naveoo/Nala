import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import requests
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_PATH = os.path.join("database", "database.db")
conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
cursor = conn.cursor()

class Profile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.logs_channel = self.bot.get_channel(int(os.getenv("LOGS_CHANNEL")))
    
    @app_commands.command(name="profile", description="Affichez votre profil ou celui d'un autre utilisateur.")
    async def profile(self, interaction: discord.Interaction, user: discord.User = None):   
        try:
            target_user = user or interaction.user
            discord_id = str(target_user.id)
            cursor.execute('''
            SELECT github_username, github_token, created_at FROM Users WHERE id = ?
            ''', (discord_id,))
            result = cursor.fetchone()

            if result:
                github_username, github_token, created_at = result
                cursor.execute('''
                SELECT repo_name FROM UserRepos WHERE discord_id = ?
                ''', (discord_id,))
                repos = [row[0] for row in cursor.fetchall()]
                repo_stars = []
                for repo in repos:
                    stars = self.get_repo_stars(repo, github_token)
                    repo_stars.append(f"{repo} : {stars} ⭐")
                embed = discord.Embed(
                    title=f"Profil de {target_user.name}",
                    color=discord.Color.blue()
                )
                embed.set_thumbnail(url=target_user.avatar.url)
                embed.add_field(name="Nom GitHub", value=github_username, inline=False)
                embed.add_field(name="Date d'inscription", value=created_at, inline=False)
                embed.add_field(name="Dépôts suivis", value="\n".join(repo_stars) if repo_stars else "Aucun dépôt suivi", inline=False)
                await interaction.response.send_message(embed=embed, ephemeral=False)
            else:
                await interaction.response.send_message(f"{target_user.name} n'est pas encore enregistré.", ephemeral=True)
        except Exception as e:
            embed = discord.Embed(title="Erreur dans /profile", description="Une erreur est apparue à l'éxecution de la commande", color=discord.Color.red())
            embed.add_field(name="Détails de l'erreur", value=f"Utilisateur : {interaction.user.name} ({interaction.user.id})\nServeur : {interaction.guild.name} ({interaction.guild.id})")
            embed.add_field(name="Retour console", value=e[:1000])
            print(f"❌ Erreur dans la commande /profile : {e}")
            await interaction.response.send_message("Une erreur s'est produite lors de l'exécution de la commande.", ephemeral=True)

    def get_repo_stars(self, repo_name, github_token):
        try:
            url = f"https://api.github.com/repos/{repo_name}"
            headers = {
                "Authorization": f"token {github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response.json().get("stargazers_count", 0)
            else:
                print(f"Erreur GitHub API : {response.status_code} - {response.text}")
                return 0
        except Exception as e:
            print(f"Erreur lors de la récupération des étoiles pour {repo_name} : {e}")
            return 0

async def setup(bot):
    await bot.add_cog(Profile(bot))