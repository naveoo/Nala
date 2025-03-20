import discord
from discord.ext import commands
from discord import app_commands
import os
import random
import string

class GeneratePassword(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        @commands.Cog.listener()
        async def on_ready(self):
            self.logs_channel = self.bot.get_channel(int(os.getenv("LOGS_CHANNEL")))

    @app_commands.command(name="generate_password", description="Génère un mot de passe aléatoire.")
    @app_commands.describe(length="Longueur du mot de passe souhaitée (minimum : 4)")
    async def generate_password(self, interaction: discord.Interaction, length: int):
        await interaction.response.defer(ephemeral=False)
        try:
            if length < 4:
                await interaction.followup.send("La longueur doit être au moins de 4 caractères.", ephemeral=True)
                return
            
            characters = string.ascii_letters + string.digits + string.punctuation
            password = ''.join(random.choice(characters) for _ in range(length))
            
            embed = discord.Embed(
                title="🔒 Mot de Passe Généré",
                description=f"Voici votre mot de passe : ```{password}```",
                color=discord.Color.purple()
            )
            await interaction.followup.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(title="Erreur dans /generate_password", description="Une erreur est apparue à l'éxecution de la commande", color=discord.Color.red())
            embed.add_field(name="Détails de l'erreur", value=f"Utilisateur : {interaction.user.name} ({interaction.user.id})\nServeur : {interaction.guild.name} ({interaction.guild.id})")
            embed.add_field(name="Retour console", value=e[:1000])
            print(f"❌ Erreur dans la commande /generate_password : {e}")
            await interaction.followup.send("Une erreur s'est produite lors de la génération du mot de passe.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(GeneratePassword(bot))
