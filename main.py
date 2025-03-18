import discord
import os
from discord.ext import commands
from dotenv import load_dotenv
import asyncio
from flask_server import run_flask_in_thread

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

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
    print("Chargement des cogs...")
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"✅ Chargé : {filename}")
            except Exception as e:
                print(f"❌ Erreur lors du chargement de {filename} : {e}")
    print(f"Commandes chargées : {[cmd.name for cmd in bot.tree.get_commands()]}")

async def main():
    print("Lancement du serveur Flask et du bot Discord...")
    
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, run_flask_in_thread, bot)

    await bot.start(TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❌ Une erreur s'est produite : {e}")
