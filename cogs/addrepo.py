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

class AddRepo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="addrepo", description="Ajoutez un dépôt GitHub à votre profil.")
    async def addrepo(self, interaction: discord.Interaction, repo_name: str):
        discord_id = str(interaction.user.id)

        try:
            # Récupérer le token GitHub de l'utilisateur
            cursor.execute('''
            SELECT github_token FROM Users WHERE id = ?
            ''', (discord_id,))
            result = cursor.fetchone()

            if result:
                github_token = result[0]

                # Vérifier si le dépôt existe
                if self.check_repo_exists(repo_name, github_token):
                    # Ajouter le dépôt à la table UserRepos
                    cursor.execute('''
                    INSERT OR IGNORE INTO UserRepos (discord_id, repo_name)
                    VALUES (?, ?)
                    ''', (discord_id, repo_name))
                    conn.commit()

                    if cursor.rowcount > 0:
                        await interaction.response.send_message(f"Le dépôt `{repo_name}` a été ajouté à votre profil.", ephemeral=True)
                    else:
                        await interaction.response.send_message(f"Vous suivez déjà le dépôt `{repo_name}`.", ephemeral=True)
                else:
                    await interaction.response.send_message(f"Le dépôt `{repo_name}` n'existe pas ou vous n'y avez pas accès.", ephemeral=True)
            else:
                await interaction.response.send_message("Vous n'êtes pas encore enregistré.", ephemeral=True)
        except Exception as e:
            print(f"❌ Erreur dans la commande /addrepo : {e}")
            await interaction.response.send_message("Une erreur s'est produite lors de l'ajout du dépôt.", ephemeral=True)

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

async def setup(bot):
    await bot.add_cog(AddRepo(bot))