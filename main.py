import discord
import os
from discord.ext import commands
from dotenv import load_dotenv
import asyncio
from flask_server import create_flask_app
from datetime import datetime
from threading import Thread
from colorama import init, Fore

init(autoreset=True)

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

def log_info(message):
    print(f"{Fore.GREEN}[INFO] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}")

def log_warning(message):
    print(f"{Fore.YELLOW}[WARN] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}")

def log_error(message):
    print(f"{Fore.RED}[ERROR] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}")

@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.online, activity=discord.Game(name="/help"))
    log_info(f"{bot.user} est en ligne.")
    try:
        await bot.tree.sync()
        log_info(f"Commandes slash synchronisées : {len(bot.tree.get_commands())}")
        loaded_cogs = [cmd.name for cmd in bot.tree.get_commands()]
        log_info(f"Commandes synchronisées : {loaded_cogs}")
    except Exception as e:
        log_error(f"Erreur lors de la synchronisation des commandes : {e}")

@bot.event
async def setup_hook():
    log_info("Chargement des cogs...")
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                log_info(f"Chargé : {filename}")
            except Exception as e:
                log_error(f"Erreur lors du chargement de {filename} : {e}")
                raise e
    log_info(f"Commandes chargées : {[cmd.name for cmd in bot.tree.get_commands()]}")

def run_flask():
    flask_app = create_flask_app(bot)
    flask_app.run(debug=True, use_reloader=False)

async def main():
    log_info("Lancement du serveur Flask et du bot Discord...")
    
    Thread(target=run_flask).start()

    await bot.start(TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        log_error(f"Une erreur s'est produite : {e}")