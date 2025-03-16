import discord
import os
from discord.ext import commands
from discord import app_commands, ui
import sqlite3

# Connexion à la base de données
DATABASE_PATH = os.path.join("database", "database.db")
conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
cursor = conn.cursor()

class NotifyView(ui.View):
    def __init__(self, discord_id):
        super().__init__(timeout=None)  # Pas de timeout pour que les boutons restent actifs
        self.discord_id = discord_id

    @ui.button(label="Activer", style=discord.ButtonStyle.success, custom_id="enable_notifications")
    async def enable_notifications(self, interaction: discord.Interaction, button: ui.Button):
        # Mettre à jour les notifications dans la base de données
        cursor.execute('''
        UPDATE Users
        SET notifications_enabled = ?
        WHERE id = ?
        ''', (True, self.discord_id))
        conn.commit()

        # Mettre à jour l'embed
        embed = discord.Embed(
            title="🔔 Notifications",
            description="Les notifications sont maintenant **activées**.",
            color=discord.Color.green()
        )
        await interaction.response.edit_message(embed=embed, view=self)

    @ui.button(label="Désactiver", style=discord.ButtonStyle.danger, custom_id="disable_notifications")
    async def disable_notifications(self, interaction: discord.Interaction, button: ui.Button):
        # Mettre à jour les notifications dans la base de données
        cursor.execute('''
        UPDATE Users
        SET notifications_enabled = ?
        WHERE id = ?
        ''', (False, self.discord_id))
        conn.commit()

        # Mettre à jour l'embed
        embed = discord.Embed(
            title="🔔 Notifications",
            description="Les notifications sont maintenant **désactivées**.",
            color=discord.Color.red()
        )
        await interaction.response.edit_message(embed=embed, view=self)

class Notify(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="notify", description="Activez ou désactivez les notifications.")
    async def notify(self, interaction: discord.Interaction):
        discord_id = str(interaction.user.id)

        # Récupérer l'état actuel des notifications
        cursor.execute('''
        SELECT notifications_enabled FROM Users WHERE id = ?
        ''', (discord_id,))
        result = cursor.fetchone()

        if result:
            notifications_enabled = result[0]

            # Créer un embed pour afficher l'état des notifications
            embed = discord.Embed(
                title="🔔 Notifications",
                description=f"Les notifications sont actuellement **{'activées' if notifications_enabled else 'désactivées'}**.",
                color=discord.Color.blue()
            )

            # Créer une vue avec des boutons pour activer/désactiver les notifications
            view = NotifyView(discord_id)

            # Envoyer l'embed et les boutons
            await interaction.response.send_message(embed=embed, view=view, ephemeral=False)
        else:
            await interaction.response.send_message("Vous n'êtes pas encore enregistré.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Notify(bot))