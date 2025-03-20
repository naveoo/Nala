import discord
from discord.ext import commands
from discord import app_commands
import os
import requests

class LastCommits(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.logs_channel = self.bot.get_channel(int(os.getenv("LOGS_CHANNEL")))

    @app_commands.command(name="last_commits", description="Liste les derniers commits d'un dépôt GitHub.")
    @app_commands.describe(repo_name="Nom du dépôt GitHub (format : owner/repo)")
    async def last_commits(self, interaction: discord.Interaction, repo_name: str):
        await interaction.response.defer(ephemeral=False)
        try:
            github_token = os.getenv("GITHUB_TOKEN")
            if not github_token:
                await interaction.followup.send("Le token GitHub n'est pas configuré.", ephemeral=True)
                return

            commits = await self.get_last_commits(interaction, repo_name, github_token)
            if commits is None:
                await interaction.followup.send(f"Le dépôt `{repo_name}` n'existe pas ou vous n'y avez pas accès.", ephemeral=True)
                return

            if not commits:
                await interaction.followup.send(f"Aucun commit trouvé pour `{repo_name}`.", ephemeral=True)
                return

            embed = discord.Embed(title=f"📝 Derniers commits pour {repo_name}", color=discord.Color.blue())
            for commit in commits[:5]:
                commit_message = commit['commit']['message']
                commit_author = commit['commit']['author']['name']
                commit_url = commit['html_url']
                embed.add_field(
                    name=f"Commit by {commit_author}",
                    value=f"**Message:** {commit_message}\n[Voir sur GitHub]({commit_url})",
                    inline=False
                )
            
            await interaction.followup.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(title="Erreur dans /last_commits", description="Une erreur est apparue à l'éxecution de la commande", color=discord.Color.red())
            embed.add_field(name="Détails de l'erreur", value=f"Utilisateur : {interaction.user.name} ({interaction.user.id})\nServeur : {interaction.guild.name} ({interaction.guild.id})")
            embed.add_field(name="Retour console", value=e[:1000])
            print(f"❌ Erreur dans la commande /last_commits : {e}")
            await interaction.followup.send("Une erreur s'est produite lors de la récupération des commits.", ephemeral=True)

    async def get_last_commits(self, interaction, repo_name, github_token):
        try:
            url = f"https://api.github.com/repos/{repo_name}/commits?per_page=5"
            headers = {"Authorization": f"token {github_token}", "Accept": "application/vnd.github.v3+json"}
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Erreur dans l'appel Github.")
                return None
        except Exception as e:
            embed = discord.Embed(title="Erreur dans /last_commits", description="Une erreur est apparue à l'éxecution de la commande", color=discord.Color.red())
            embed.add_field(name="Détails de l'erreur", value=f"Utilisateur : {interaction.user.name} ({interaction.user.id})\nServeur : {interaction.guild.name} ({interaction.guild.id})")
            embed.add_field(name="Retour console", value=e[:1000])
            print(f"❌ Erreur dans la commande /last_commits : {e}")
            return None

async def setup(bot):
    await bot.add_cog(LastCommits(bot))
