import discord
from discord.ext import commands
from discord import app_commands
import json

class GetDocumentation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="get_documentation", description="Obtenir différents liens de documentation de technologies.")
    async def get_documentation(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        with open("docs.json", "r") as file:
            data = json.load(file)
        embed = discord.Embed(color=discord.Color.purple(), title="Documentation rapide", description="")
        for key, value in data.items():
            embed.add_field(name=key.lower(), value=value, inline=False)
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(GetDocumentation(bot))