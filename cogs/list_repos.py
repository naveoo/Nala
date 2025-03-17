import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import requests
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Connexion à la base de données
DATABASE_PATH = os.path.join("database", "database.db")
conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
cursor = conn.cursor()

class ListRepos(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="list_repos", description="Listez les dépôts GitHub auxquels vous pouvez vous inscrire.")
    async def list_repos(self, interaction: discord.Interaction):
        discord_id = str(interaction.user.id)

        try:
            # Récupérer le token GitHub de l'utilisateur
            cursor.execute('''
            SELECT github_token FROM Users WHERE id = ?
            ''', (discord_id,))
            result = cursor.fetchone()

            if result:
                github_token = result[0]

                # Récupérer la liste des dépôts de l'utilisateur
                repos = self.get_user_repos(github_token)

                if repos:
                    # Créer un embed pour afficher la liste des dépôts
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
            print(f"❌ Erreur dans la commande /list_repos : {e}")
            await interaction.response.send_message("Une erreur s'est produite lors de la récupération des dépôts.", ephemeral=False)

    def get_user_repos(self, github_token):
        try:
            url = "https://api.github.com/user/repos"
            headers = {
                "Authorization": f"token {github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            params = {
                "per_page": 100  # Limiter à 100 dépôts par page
            }
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                repos = [repo["full_name"] for repo in response.json()]
                return repos
            else:
                print(f"Erreur GitHub API : {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Erreur lors de la récupération des dépôts GitHub : {e}")
            return None

async def setup(bot):
    await bot.add_cog(ListRepos(bot))