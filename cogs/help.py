import discord
from discord.ext import commands
from discord import app_commands

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Donne la liste des commandes disponibles.")
    async def help(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Résultat de la commande help")

async def setup(bot):
    await bot.add_cog(Help(bot))