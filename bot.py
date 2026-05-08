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

CANAL_AVENTURAS = 1502421010274844762
ROL_AVENTURA = 1502421341394042880

# -------- BOT ONLINE --------

@bot.event
async def on_ready():
    print(f'✅ Bot conectado como {bot.user}')

# -------- DETECTOR DE SALAS --------

@bot.event
async def on_message(message):

    # Ignorar mensajes del propio bot
    if message.author == bot.user:
        return

    # Detectar SOLO mensajes de Nekotina
    if message.author.id == 270904126974590976:

        contenido = message.content.lower()

        salas = {
            "magma": {
                "titulo": "🌋 Sala de Magma Detectada",
                "descripcion": "¡Prepara tus mascotas y entra en la zona de magma!",
                "color": 0xFF5500
            },

            "outlands": {
                "titulo": "🏝 Sala de Outlands Detectada",
                "descripcion": "¡Una aventura de Outlands ha aparecido!",
                "color": 0x00AAFF
            },

            "whispering": {
                "titulo": "🌲 Sala de Whispering Detectada",
                "descripcion": "¡El bosque susurra... aventura disponible!",
                "color": 0x55FF55
            }
        }

        for palabra, datos in salas.items():

            if palabra in contenido:

                canal = bot.get_channel(CANAL_AVENTURAS)

                embed = discord.Embed(
                    title=datos["titulo"],
                    description=datos["descripcion"],
                    color=datos["color"]
                )

                embed.add_field(
                    name="📍 Detectado en",
                    value=message.channel.mention,
                    inline=False
                )

                embed.set_footer(
                    text="Sistema de Detección"
                )

                await canal.send(
                    f"<@&{ROL_AVENTURA}>",
                    embed=embed
                )

                break

    await bot.process_commands(message)

# -------- KEEP ALIVE --------

keep_alive()

# -------- INICIAR BOT --------

bot.run(TOKEN)