import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Connexion à la base de données
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
            # Supprimer le dépôt de la table UserRepos
            cursor.execute('''
            DELETE FROM UserRepos
            WHERE discord_id = ? AND repo_name = ?
            ''', (discord_id, repo_name))
            conn.commit()

            if cursor.rowcount > 0:
                await interaction.response.send_message(f"Le dépôt `{repo_name}` a été retiré de votre profil.", ephemeral=True)
            else:
                await interaction.response.send_message(f"Le dépôt `{repo_name}` n'est pas dans votre profil.", ephemeral=True)
        except Exception as e:
            print(f"❌ Erreur dans la commande /remove_repo : {e}")
            await interaction.response.send_message("Une erreur s'est produite lors de la suppression du dépôt.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(RemoveRepo(bot))