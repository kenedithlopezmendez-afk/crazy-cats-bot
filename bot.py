import discord
from discord.ext import commands
from flask import Flask
from threading import Thread
import os

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
CANAL_DETECCION = 1436358970284572723

# Canal donde el bot enviará alertas
CANAL_ALERTAS = 1436358970284572723

# Rol a mencionar
ROL_AVENTURA = 1436361900215500870

# ID Nekotina
NEKOTINA_ID = 429457053791158281

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

    print("📩 MENSAJE RECIBIDO")

    await bot.process_commands(message)
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