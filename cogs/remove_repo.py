import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import requests
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_NAME = os.getenv("DISCORD_WEBHOOK_URL")

DATABASE_PATH = os.path.join("database", "database.db")
conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
cursor = conn.cursor()

class RemoveRepo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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
                    if self.delete_github_webhook(repo_name, github_token, webhook_id):
                        self.delete_github_workflow(repo_name, github_token)
                        cursor.execute('''
                        DELETE FROM UserRepos
                        WHERE discord_id = ? AND repo_name = ?
                        ''', (discord_id, repo_name))
                        conn.commit()
                        if self.delete_github_secret(github_token,SECRET_NAME, repo_name):
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
                            "Erreur lors de la suppression du webhook GitHub.",
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
            print(f"❌ Erreur dans la commande /remove_repo : {e}")
            await interaction.response.send_message(
                "Une erreur s'est produite lors de la suppression du dépôt.",
                ephemeral=True
            )

    def delete_github_webhook(self, repo_name, github_token, webhook_id):
        """
        Supprime un webhook GitHub pour le dépôt spécifié.
        """
        try:
            url = f"https://api.github.com/repos/{repo_name}/hooks/{webhook_id}"
            headers = {
                "Authorization": f"token {github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            response = requests.delete(url, headers=headers)
            return response.status_code == 204
        except Exception as e:
            print(f"Erreur lors de la suppression du webhook GitHub : {e}")
            return False

    def delete_github_workflow(self, repo_name, github_token):
        try:
            url = f"https://api.github.com/repos/{repo_name}/contents/.github/workflows/notify-discord.yml"
            headers = {
                "Authorization": f"token {github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                sha = response.json()["sha"]
                payload = {
                    "message": "Suppression du workflow de notification Discord",
                    "sha": sha
                }
                response = requests.delete(url, json=payload, headers=headers)
                return response.status_code == 200
            else:
                print(f"Fichier de workflow introuvable : {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"Erreur lors de la suppression du workflow GitHub : {e}")
            return False
    def delete_github_secret(self, github_token, secret_name, repo_name):
        try:
            url = f"https://api.github.com/repos/{repo_name}/actions/secrets/{secret_name}"
            headers = {
                "Authorization": f"token {github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            response = requests.delete(url, headers=headers)
            if response.status_code == 204:
                print(f"Secret '{secret_name}' supprimé avec succès pour le dépôt {repo_name}.")
                return True
            else:
                print(f"Erreur lors de la suppression du secret '{secret_name}': {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"Exception lors de la suppression du secret '{secret_name}': {e}")
            return False
async def setup(bot):
    await bot.add_cog(RemoveRepo(bot))