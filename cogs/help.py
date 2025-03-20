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
        embed.add_field(name="```Attention```", value="Plusieurs fonctionnalitées poussées du bot nécessitent une inscription préalable avec /register, il est donc vivement conseillé de s'inscrire avant toute utilisation.")
        embed.add_field(
            name="Commandes Github",
            value=(
                "`/profile` • Permet d'afficher son profil et ses dépôts associés.\n"
                "`/list_repos` • Permet de lister tous les dépôts disponibles à l'utilisateur.\n"
                "`/add_repo <utilisateur/dépôt>` • Permet d'ajouter un dépôt à son profil et de définir un salon où recevoir les notifications suivantes :\n"
                " --- Commits\n"
                " --- Pull request ouverte\n"
                " --- Pull request fermée\n"
                " --- Issue ouverte\n"
                " --- Nouveau Fork\n"
                " --- Publication de release\n"
                "`/remove_repo <utilisateur/dépôt>` • Permet d'enlever un dépôt à son profil et de réinitialiser les paramètres."
                "`/last_commits <utilisateur/dépôt> • Permet d'afficher les 5 derniers commits sur un dépôt."
                "`/last_issues <utilisateur/dépôt>` • Permet d'afficher les 5 dernières issues d'un dépôt."
            ),
            inline=False
        )

        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Help(bot))
