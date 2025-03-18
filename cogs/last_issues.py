import discord
from discord.ext import commands
from discord import app_commands
import requests
import os
from dotenv import load_dotenv

load_dotenv()

class ListIssues(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logs_channel = None

    async def cog_load(self):
        """S'exécute après le chargement du cog."""
        await self.bot.wait_until_ready()
        self.logs_channel = self.bot.get_channel(int(os.getenv("LOGS_CHANNEL")))

    @app_commands.command(name="list_issues", description="Liste les 5 dernières issues ouvertes d'un dépôt GitHub.")
    @app_commands.describe(repo_name="Nom du dépôt GitHub (format : owner/repo)")
    async def list_issues(self, interaction: discord.Interaction, repo_name: str):
        await interaction.response.defer(ephemeral=False)
        try:
            github_token = os.getenv("GITHUB_TOKEN")
            if not github_token:
                await interaction.followup.send("Le token GitHub n'est pas configuré.", ephemeral=True)
                return

            issues = await self.get_open_issues(repo_name, github_token)
            if issues is None:
                await interaction.followup.send(f"Le dépôt `{repo_name}` n'existe pas ou vous n'y avez pas accès.", ephemeral=True)
                return

            if not issues:
                await interaction.followup.send(f"Aucune issue ouverte trouvée pour `{repo_name}`.", ephemeral=True)
                return

            embed = discord.Embed(title=f"📌 Issues ouvertes pour {repo_name}", color=discord.Color.blue())
            for issue in issues[:5]:
                embed.add_field(name=issue['title'], value=f"[Voir sur GitHub]({issue['html_url']})", inline=False)
            
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await self.log_error("/list_issues", interaction, e)
            await interaction.followup.send("Une erreur s'est produite lors de la récupération des issues.", ephemeral=True)

    async def get_open_issues(self, repo_name, github_token):
        try:
            url = f"https://api.github.com/repos/{repo_name}/issues?state=open"
            headers = {"Authorization": f"token {github_token}", "Accept": "application/vnd.github.v3+json"}
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            await self.log_error("/list_issues - get_open_issues", None, e)
            return None

    async def log_error(self, command, interaction, error):
        if not self.logs_channel:
            print("Erreur : Canal de logs introuvable.")
            return
        embed = discord.Embed(title=f"Erreur dans la commande {command}", color=discord.Color.red())
        error_details = str(error)
        if len(error_details) > 1990:
            error_details = error_details[:1990] + "...\n(tronqué)"
        embed.add_field(name="Détails de l'erreur", value=f"```{error_details}```", inline=False)
        await self.logs_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ListIssues(bot))
