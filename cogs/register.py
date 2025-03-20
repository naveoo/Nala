import discord
from discord.ext import commands
from discord import app_commands
import uuid
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
REDIRECT_URI = os.getenv("GITHUB_REDIRECT_URI")

DATABASE_PATH = os.path.join("database", "database.db")
conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
cursor = conn.cursor()

class Register(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        self.logs_channel = self.bot.get_channel(int(os.getenv("LOGS_CHANNEL")))
    
    @app_commands.command(name="register", description="Enregistrez-vous pour lier votre compte GitHub.")
    async def register(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=False)

            discord_id = str(interaction.user.id)
            state = str(uuid.uuid4())

            cursor.execute('''
            INSERT OR IGNORE INTO Users (id, created_at)
            VALUES (?, ?)
            ''', (discord_id, datetime.now()))
            conn.commit()

            cursor.execute('''
            INSERT INTO PendingRegistrations (state, discord_id)
            VALUES (?, ?)
            ''', (state, discord_id))
            conn.commit()

            embed = discord.Embed(
                title="Inscription",
                description="✅ Vous avez bien été enregistré ! Vous pouvez maintenant vous authentifier avec GitHub.",
                color=discord.Color.blue()
            )
            embed.add_field(name="🔗 Lien d'authentification GitHub", value=f"Cliquez sur [ce lien](https://github.com/login/oauth/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=repo&state={state}) pour vous authentifier avec GitHub.")
            embed.set_footer(text="Vous avez 5 minutes pour compléter l'authentification.")
            await interaction.followup.send(embed=embed, ephemeral=False)
        except Exception as e:
            embed = discord.Embed(title="Erreur dans /register", description="Une erreur est apparue à l'éxecution de la commande", color=discord.Color.red())
            embed.add_field(name="Détails de l'erreur", value=f"Utilisateur : {interaction.user.name} ({interaction.user.id})\nServeur : {interaction.guild.name} ({interaction.guild.id})")
            embed.add_field(name="Retour console", value=e[:1000])
            print(f"❌ Erreur dans la commande /register : {e}")
            await interaction.followup.send("Une erreur s'est produite lors de l'exécution de la commande.", ephemeral=False)

async def setup(bot):
    await bot.add_cog(Register(bot))