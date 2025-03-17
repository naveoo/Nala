import discord
from discord.ext import commands
from discord import app_commands

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Donne la liste des commandes disponibles.")
    async def help(self, interaction: discord.Interaction):
        await interaction.response.defer()

        embed = discord.Embed(
            title="📌 Liste des commandes utilisables",
            description="",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="Commandes Github",
            value=(
                "`/register` • Permet de s'inscrire à la base de données du bot (Obligatoire pour les actions Github).\n"
                "`/profile` • Permet d'afficher son profil et ses repository associés.\n"
                "`/list_repos` • Permet de lister tous les repository disponibles à l'utilisateur.\n"
                "`/add_repo` • Permet d'ajouter un repository à son profil et de définir un salon où recevoir les notifications suivantes :\n"
                " --- Commits\n"
                " --- Pull request ouverte\n"
                " --- Pull request fermée\n"
                " --- Issue ouverte\n"
                " --- Nouveau Fork\n"
                " --- Publication de release\n"
                "`/remove_repo` • Permet d'enlever un repository à son profil et de réinitialiser les paramètres."
            ),
            inline=False
        )

        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Help(bot))
