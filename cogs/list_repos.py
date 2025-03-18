import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import requests
import os
import traceback
from dotenv import load_dotenv

load_dotenv()

DATABASE_PATH = os.path.join("database", "database.db")
conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
cursor = conn.cursor()

class ListRepos(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logs_channel = bot.get_channel(int(os.getenv("LOGS_CHANNEL")))

    @app_commands.command(name="list_repos", description="Listez les dépôts GitHub auxquels vous pouvez vous inscrire.")
    async def list_repos(self, interaction: discord.Interaction):
        discord_id = str(interaction.user.id)

        try:
            cursor.execute('''
            SELECT github_token FROM Users WHERE id = ?
            ''', (discord_id,))
            result = cursor.fetchone()

            if result:
                github_token = result[0]
                repos = await self.get_user_repos(github_token)

                if repos:
                    embed = discord.Embed(
                        title="📂 Vos dépôts GitHub",
                        description="Voici la liste des dépôts auxquels vous avez accès :",
                        color=discord.Color.blue()
                    )
                    embed.add_field(name="Dépôts", value="\n".join(repos), inline=False)

                    await interaction.response.send_message(embed=embed, ephemeral=False)
                else:
                    await interaction.response.send_message("Aucun dépôt trouvé.", ephemeral=False)
            else:
                await interaction.response.send_message("Vous n'êtes pas encore enregistré.", ephemeral=False)
        except Exception as e:
            await self.log_error("/list_repos", interaction, e)
            await interaction.response.send_message("Une erreur s'est produite lors de la récupération des dépôts.", ephemeral=False)

    async def get_user_repos(self, github_token):
        try:
            url = "https://api.github.com/user/repos"
            headers = {
                "Authorization": f"token {github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            params = {
                "per_page": 100
            }
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                repos = [repo["full_name"] for repo in response.json()]
                return repos
            else:
                print(f"Erreur GitHub API : {response.status_code} - {response.text}")
                return None
        except Exception as e:
            await self.log_error("/list_repos", None, e)
            return None

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
    await bot.add_cog(ListRepos(bot))