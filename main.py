import discord
import os
from discord.ext import commands
from dotenv import load_dotenv
import asyncio
from flask_server import create_quart_app

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Fonction pour démarrer Quart
async def run_quart():
    print("Démarrage du serveur Quart...")  # Journal pour vérifier le lancement
    app = create_quart_app(bot)
    await app.run_task(host="0.0.0.0", port=5000, debug=True)
    print("Serveur Quart lancé.")  # Devrait s'afficher si tout fonctionne

@bot.event
async def on_ready():
    print(f"✅ {bot.user} est en ligne.")
    try:
        await bot.tree.sync()
        print(f"✅ Commandes slash synchronisées : {len(bot.tree.get_commands())}")
    except Exception as e:
        print(f"❌ Erreur lors de la synchronisation des commandes : {e}")

@bot.event
async def setup_hook():
    print("Chargement des cogs...")  # Journal pour le débogage
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"✅ Chargé : {filename}")
            except Exception as e:
                print(f"❌ Erreur lors du chargement de {filename} : {e}")
    print(f"Commandes chargées : {[cmd.name for cmd in bot.tree.get_commands()]}")

async def main():
    print("Lancement des processus...")  # Journal initial
    try:
        quart_task = asyncio.create_task(run_quart())
        bot_task = asyncio.create_task(bot.start(TOKEN))
        await asyncio.gather(quart_task, bot_task)
    except Exception as e:
        print(f"❌ Une erreur s'est produite dans main() : {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❌ Échec lors de l'exécution du programme principal : {e}")
