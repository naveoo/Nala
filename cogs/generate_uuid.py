import discord
from discord.ext import commands
from discord import app_commands
import uuid

class GenerateUUID(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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
            print(f"❌ Erreur dans la commande /generate_uuid : {e}")
            await interaction.followup.send("Une erreur s'est produite lors de la génération de l'UUID.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(GenerateUUID(bot))
