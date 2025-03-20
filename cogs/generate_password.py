import discord
from discord.ext import commands
from discord import app_commands
import random
import string

class GeneratePassword(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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
            print(f"❌ Erreur dans la commande /generate_password : {e}")
            await interaction.followup.send("Une erreur s'est produite lors de la génération du mot de passe.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(GeneratePassword(bot))
