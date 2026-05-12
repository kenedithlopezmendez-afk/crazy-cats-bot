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

    # Ignorar mensajes del propio bot
    if message.author == bot.user:
        return

    # SOLO detectar en el canal específico
    if message.channel.id != CANAL_DETECCION:
        return

    # SOLO detectar mensajes de Nekotina
    if message.author.id != 429457053791158281:
        return

    # Aventuras detectables
    salas = {
        "sala de aventura: 🌋 magma": {
            "titulo": "🌋 Sala de Magma Detectada",
            "descripcion": "¡Una nueva sala de aventura de magma está abierta! ✨",
            "color": 0xFF5500
        },

        "sala de aventura: 🧝 outlands": {
            "titulo": "🏝 Sala de Outlands Detectada",
            "descripcion": "¡Una nueva sala de aventura de Outlands está abierta! ✨",
            "color": 0x00AAFF
        },

        "sala de aventura: 🌲 whispering": {
            "titulo": "🌲 Sala de Whispering Detectada",
            "descripcion": "¡Una nueva sala de Whispering está abierta! ✨",
            "color": 0x55FF55
        }
    }

    # Leer embeds de Nekotina
    for embed in message.embeds:

        texto = ""

        # Leer título
        if embed.title:
            texto += embed.title.lower()

        # Leer descripción
        if embed.description:
            texto += embed.description.lower()

        # Detectar aventuras
        for palabra, datos in salas.items():

            if palabra in texto:

                canal = bot.get_channel(CANAL_AVENTURAS)

                nuevo_embed = discord.Embed(
                    title=datos["titulo"],
                    description=datos["descripcion"],
                    color=datos["color"]
                )

                nuevo_embed.add_field(
                    name="📍 Detectado en",
                    value=message.channel.mention,
                    inline=False
                )

                nuevo_embed.set_footer(
                    text="Crazy Tracker • Sistema de Aventuras"
                )

                await canal.send(
                    f"<@&{ROL_AVENTURA}>",
                    embed=nuevo_embed
                )

                return

    await bot.process_commands(message)

# -------- KEEP ALIVE --------

keep_alive()

# -------- INICIAR BOT --------

bot.run(TOKEN)