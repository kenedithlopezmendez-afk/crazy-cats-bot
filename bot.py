import discord
from discord.ext import commands
from flask import Flask
from threading import Thread
import os

# -------- FLASK PARA RENDER --------

app = Flask('')

@app.route('/')
def home():
    return "Bot activo"

def run():
    app.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = Thread(target=run)
    t.start()

# -------- CONFIG BOT --------

TOKEN = os.environ['TOKEN']

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="?",
    intents=intents
)

# -------- IDs --------

CANAL_AVENTURAS = 1436358970284572723
ROL_AVENTURA = 1436361900215500870

# Canal donde Nekotina manda aventuras
CANAL_DETECCION = 1436358970284572723

# -------- BOT ONLINE --------

@bot.event
async def on_ready():
    print(f'✅ Bot conectado como {bot.user}')

# -------- BOT DETECCION ------

@bot.event
async def on_message(message):

    print("MENSAJE DETECTADO")

# -------- KEEP ALIVE --------

keep_alive()

# -------- INICIAR BOT --------

bot.run(TOKEN)