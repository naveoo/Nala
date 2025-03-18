import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import aiohttp
import os
from dotenv import load_dotenv
import traceback

load_dotenv()
DATABASE_PATH = os.path.join("database", "database.db")
conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
cursor = conn.cursor()

class Profile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logs_channel = None  # Initialisation différée

    async def cog_load(self):
        """S'exécute après le chargement du cog."""
        await self.bot.wait_until_ready()
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
                
                repo_stars = await self.get_repos_stars_bulk(repos, github_token)
                
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
            await self.log_error("/profile", interaction, e)
            if not interaction.response.is_done():
                await interaction.response.send_message("Une erreur s'est produite lors de l'exécution de la commande.", ephemeral=True)

    async def get_repos_stars_bulk(self, repos, github_token):
        """Optimisation : récupère les étoiles de plusieurs dépôts en une seule requête par utilisateur."""
        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        repo_stars = []
        async with aiohttp.ClientSession() as session:
            for repo in repos:
                url = f"https://api.github.com/repos/{repo}"
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        stars = data.get("stargazers_count", 0)
                        repo_stars.append(f"{repo} : {stars} ⭐")
                    else:
                        repo_stars.append(f"{repo} : Erreur ❌")
        return repo_stars

    async def log_error(self, command, interaction, error):
        if not self.logs_channel:
            print("Erreur : Canal de logs introuvable.")
            return
        
        embed = discord.Embed(title=f"Erreur dans la commande {command}",
                              description=f"Utilisateur : {interaction.user.name if interaction else 'N/A'} ({interaction.user.id if interaction else 'N/A'})\nServeur : {interaction.guild.name if interaction else 'N/A'} ({interaction.guild.id if interaction else 'N/A'})",
                              color=discord.Color.red())
        error_details = traceback.format_exc() or str(error)
        if len(error_details) > 1990:
            error_details = error_details[:1990] + "...\n(tronqué)"
        embed.add_field(name="Détails de l'erreur", value=f"```{error_details}```", inline=False)
        await self.logs_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Profile(bot))