import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import aiohttp
import os
import traceback
from dotenv import load_dotenv

load_dotenv()

SECRET_NAME = os.getenv("DISCORD_WEBHOOK_URL")

DATABASE_PATH = os.path.join("database", "database.db")
conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
cursor = conn.cursor()

class RemoveRepo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logs_channel = None  # Initialisation différée

    async def cog_load(self):
        """S'exécute après le chargement du cog."""
        await self.bot.wait_until_ready()
        self.logs_channel = self.bot.get_channel(int(os.getenv("LOGS_CHANNEL")))

    @app_commands.command(name="remove_repo", description="Retirez un dépôt GitHub de votre profil.")
    async def remove_repo(self, interaction: discord.Interaction, repo_name: str):
        discord_id = str(interaction.user.id)
        try:
            cursor.execute('SELECT github_token FROM Users WHERE id = ?', (discord_id,))
            result = cursor.fetchone()

            if result:
                github_token = result[0]
                cursor.execute('''
                SELECT webhook_id FROM UserRepos
                WHERE discord_id = ? AND repo_name = ?
                ''', (discord_id, repo_name))
                webhook_info = cursor.fetchone()

                if webhook_info:
                    webhook_id = webhook_info[0]
                    await self.delete_github_workflow(repo_name, github_token)
                    cursor.execute('''
                    DELETE FROM UserRepos
                    WHERE discord_id = ? AND repo_name = ?
                    ''', (discord_id, repo_name))
                    conn.commit()
                    if await self.delete_github_secret(github_token, SECRET_NAME, repo_name):
                        if cursor.rowcount > 0:
                            await interaction.response.send_message(
                                f"Le dépôt `{repo_name}` a été retiré de votre profil. Le webhook et le workflow ont été supprimés.",
                                ephemeral=True
                            )
                        else:
                            await interaction.response.send_message(
                                f"Le dépôt `{repo_name}` n'est pas dans votre profil.",
                                ephemeral=True
                            )
                    else:
                        await interaction.response.send_message(
                        "Erreur lors de la suppression du secret Github.",
                        ephemeral=True
                    )
                else:
                    await interaction.response.send_message(
                        f"Le dépôt `{repo_name}` n'est pas dans votre profil.",
                        ephemeral=True
                    )
            else:
                await interaction.response.send_message(
                    "Vous n'êtes pas encore enregistré.",
                    ephemeral=True
                )
        except Exception as e:
            await self.log_error("/remove_repo", interaction, repo_name, e)
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "Une erreur s'est produite lors de la suppression du dépôt.",
                    ephemeral=True
                )

    async def delete_github_workflow(self, repo_name, github_token):
        try:
            url = f"https://api.github.com/repos/{repo_name}/contents/.github/workflows/notify-discord.yml"
            headers = {
                "Authorization": f"token {github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        sha = data["sha"]
                        payload = {
                            "message": "Suppression du workflow de notification Discord",
                            "sha": sha
                        }
                        async with session.delete(url, json=payload, headers=headers) as delete_response:
                            return delete_response.status == 200
            return False
        except Exception as e:
            await self.log_error("delete_github_workflow", None, repo_name, e)
            return False

    async def delete_github_secret(self, github_token, secret_name, repo_name):
        try:
            url = f"https://api.github.com/repos/{repo_name}/actions/secrets/{secret_name}"
            headers = {
                "Authorization": f"token {github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            async with aiohttp.ClientSession() as session:
                async with session.delete(url, headers=headers) as response:
                    return response.status == 204
        except Exception as e:
            await self.log_error("delete_github_secret", None, repo_name, e)
            return False

    async def log_error(self, command, interaction, repo_name, error):
        if not self.logs_channel:
            print("Erreur : Canal de logs introuvable.")
            return
        
        embed = discord.Embed(title=f"Erreur dans la commande {command}",
                              description=f"Argument : {repo_name}\nUtilisateur : {interaction.user.name if interaction else 'N/A'} ({interaction.user.id if interaction else 'N/A'})\nServeur : {interaction.guild.name if interaction else 'N/A'} ({interaction.guild.id if interaction else 'N/A'})",
                              color=discord.Color.red())
        error_details = traceback.format_exc() or str(error)
        if len(error_details) > 1990:
            error_details = error_details[:1990] + "...\n(tronqué)"
        embed.add_field(name="Détails de l'erreur", value=f"```{error_details}```", inline=False)
        await self.logs_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(RemoveRepo(bot))