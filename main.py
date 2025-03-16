# main.py
import discord
import os
from discord.ext import commands
from dotenv import load_dotenv
import asyncio
from threading import Thread
from flask_server import create_flask_app  # Importer la fonction create_flask_app

# Charger les variables d'environnement
load_dotenv()

# Configuration du bot
TOKEN = os.getenv("BOT_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))

# Initialisation du bot Discord
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Fonction pour exécuter Flask dans un thread séparé
def run_flask(bot):
    app = create_flask_app(bot)  # Créer l'application Flask avec l'objet bot
    app.run(host="0.0.0.0", port=5000, debug=False)

# Événement lorsque le bot est prêt
@bot.event
async def on_ready():
    print(f"✅ {bot.user} est en ligne.")
    try:
        await bot.tree.sync()
        print(f"✅ Commandes slash synchronisées: {len(bot.tree.get_commands())}")
    except Exception as e:
        print(f"❌ Erreur lors de la synchronisation des commandes : {e}")

# Événement pour charger les cogs (extensions)
@bot.event
async def setup_hook():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")
    print(f"Commandes chargées : {[cmd.name for cmd in bot.tree.get_commands()]}")

# Fonction principale
async def main():
    # Démarrer Flask dans un thread séparé
    flask_thread = Thread(target=run_flask, args=(bot,))  # Passer bot à run_flask
    flask_thread.start()

    # Démarrer le bot Discord
    await bot.start(TOKEN)

# Point d'entrée
if __name__ == "__main__":
    asyncio.run(main())