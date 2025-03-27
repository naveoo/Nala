import discord
from discord.ext import commands
from discord import app_commands
import uuid
import os

class GenerateUUID(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        self.logs_channel = self.bot.get_channel(int(os.getenv("LOGS_CHANNEL")))

    @app_commands.command(name="generate_uuid", description="Génère un UUID unique.")
    async def generate_uuid(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        try:
            unique_id = str(uuid.uuid4())
            embed = discord.Embed(
                title="🔑 UUID Généré",
                description=f"Voici votre UUID unique : `{unique_id}`",
                color=discord.Color.purple()
            )
            await interaction.followup.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(title="Erreur dans /generate_uuid", description="Une erreur est apparue à l'éxecution de la commande", color=discord.Color.red())
            embed.add_field(name="Détails de l'erreur", value=f"Utilisateur : {interaction.user.name} ({interaction.user.id})\nServeur : {interaction.guild.name} ({interaction.guild.id})")
            embed.add_field(name="Retour console", value=e[:1000])
            print(f"❌ Erreur dans la commande /generate_uuid : {e}")
            await interaction.followup.send("Une erreur s'est produite lors de la génération de l'UUID.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(GenerateUUID(bot))
