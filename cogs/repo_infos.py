import discord
from discord.ext import commands
from discord import app_commands
import os
import requests

class RepoInfos(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="repo_infos", description="Obtenez les informations d'un dépôt GitHub.")
    @app_commands.describe(repo_name="Nom du dépôt GitHub (format : owner/repo)")
    async def repo_infos(self, interaction: discord.Interaction, repo_name: str):
        await interaction.response.defer(ephemeral=False)
        try:
            github_token = os.getenv("GITHUB_TOKEN")
            if not github_token:
                await interaction.followup.send("Le token GitHub n'est pas configuré.", ephemeral=True)
                return

            repo_data = await self.get_repo_data(repo_name, github_token)
            if repo_data is None:
                await interaction.followup.send(f"Le dépôt `{repo_name}` n'existe pas ou vous n'y avez pas accès.", ephemeral=True)
                return

            collaborators = await self.get_collaborators(repo_name, github_token)

            embed = discord.Embed(title=f"📋 Informations sur {repo_name}", color=discord.Color.blue())
            embed.add_field(name="Nom", value=repo_data.get("name", "Inconnu"), inline=False)
            embed.add_field(name="Description", value=repo_data.get("description", "Aucune"), inline=False)
            embed.add_field(name="Étoiles ⭐", value=repo_data.get("stargazers_count", 0), inline=True)
            embed.add_field(name="Forks 🍴", value=repo_data.get("forks_count", 0), inline=True)
            embed.add_field(name="Langage Principal", value=repo_data.get("language", "Non spécifié"), inline=True)
            embed.add_field(name="Collaborateurs", value=", ".join(collaborators) if collaborators else "Aucun", inline=False)
            embed.add_field(name="Lien", value=f"[Voir sur GitHub]({repo_data.get('html_url')})", inline=False)

            await interaction.followup.send(embed=embed)
        except Exception as e:
            print(f"❌ Erreur dans la commande /repo_infos : {e}")
            await interaction.followup.send("Une erreur s'est produite lors de la récupération des informations du dépôt.", ephemeral=True)

    async def get_repo_data(self, repo_name, github_token):
        try:
            url = f"https://api.github.com/repos/{repo_name}"
            headers = {"Authorization": f"token {github_token}", "Accept": "application/vnd.github.v3+json"}
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Erreur lors de la récupération des données du dépôt : {e}")
            return None

    async def get_collaborators(self, repo_name, github_token):
        try:
            url = f"https://api.github.com/repos/{repo_name}/collaborators"
            headers = {"Authorization": f"token {github_token}", "Accept": "application/vnd.github.v3+json"}
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                collaborators = response.json()
                return [collab["login"] for collab in collaborators]
            return None
        except Exception as e:
            print(f"Erreur lors de la récupération des collaborateurs : {e}")
            return None

async def setup(bot):
    await bot.add_cog(RepoInfos(bot))
