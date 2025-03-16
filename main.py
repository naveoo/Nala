import discord
import os
from discord.ext import commands
from dotenv import load_dotenv
import asyncio
from threading import Thread
from flask_server import app

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

def run_flask():
    app.run(host="0.0.0.0", port=5000, debug=False)

@bot.event
async def on_ready():
    print(f"✅ {bot.user} est en ligne.")
    try:
        await bot.tree.sync()
        print(f"✅ Commandes slash synchronisées: {len(bot.tree.get_commands())}")
    except Exception as e:
        print(f"❌ Erreur lors de la synchronisation des commandes : {e}")

@bot.event
async def setup_hook():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")
    print(f"Commandes chargées : {[cmd.name for cmd in bot.tree.get_commands()]}")

async def main():
    flask_thread = Thread(target=run_flask)
    flask_thread.start()

    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())