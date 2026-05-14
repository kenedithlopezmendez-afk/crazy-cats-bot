import discord
from discord.ext import commands
from flask import Flask
from threading import Thread
import os
import logging
logging.basicConfig(level=logging.INFO)

# ==================================================
# FLASK / KEEP ALIVE
# ==================================================

app = Flask(__name__)

@app.route("/")
def home():
    return "Crazy Tracker activo"

def run():
    app.run(host="0.0.0.0", port=10000)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ==================================================
# CONFIG BOT
# ==================================================

TOKEN = os.environ["TOKEN"]

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="?",
    intents=intents
)

# ==================================================
# IDs
# ==================================================

# Canal donde Nekotina manda aventuras

# ==================================================
# BOT ONLINE
# ==================================================

@bot.event
async def on_ready():
    print(f"✅ Conectado como {bot.user}")

# ==================================================
# DETECTOR DE AVENTURAS
# ==================================================
@bot.event
async def on_message(message):

    logging.info(f"📩 MENSAJE: {message.author} | {message.content}")

    await bot.process_commands(message)
# ==================================================
# KEEP ALIVE
# ==================================================

keep_alive()

# ==================================================
# INICIAR BOT
# ==================================================
print("🔥 Iniciando bot...")

bot.run(TOKEN)