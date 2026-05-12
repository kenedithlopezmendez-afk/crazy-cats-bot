import discord
from discord.ext import commands
from flask import Flask
from threading import Thread
import os

# =========================
# FLASK PARA RENDER
# =========================

app = Flask(__name__)

@app.route("/")
def home():
    return "Crazy Tracker activo"

def run():
    app.run(host="0.0.0.0", port=10000)

def keep_alive():
    t = Thread(target=run)
    t.start()

# =========================
# CONFIG BOT
# =========================

TOKEN = os.environ["TOKEN"]

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="?",
    intents=intents
)

# =========================
# IDs
# =========================

# Canal donde Nekotina manda aventuras
CANAL_DETECCION = 1436358970284572723

# Canal donde tu bot enviará alertas
CANAL_AVENTURAS = 1436358970284572723

# Rol a mencionar
ROL_AVENTURA = 1436361900215500870

# =========================
# BOT ONLINE
# =========================

@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")

# =========================
# DETECTOR DE AVENTURAS
# =========================

@bot.event
async def on_message(message):

    # Ignorar mensajes propios
    if message.author == bot.user:
        return

    # SOLO detectar en canal específico
    if message.channel.id != CANAL_DETECCION:
        return

    # SOLO mensajes de Nekotina
    if message.author.id != 429457053791158281:
        return

    # Texto del mensaje
    texto = message.content.lower()

    # Leer embeds
    for embed in message.embeds:

        if embed.title:
            texto += " " + embed.title.lower()

        if embed.description:
            texto += " " + embed.description.lower()

        for field in embed.fields:
            texto += " " + field.name.lower()
            texto += " " + field.value.lower()

    print(texto)

    salas = {
        
        "¡Únete con tus mascotas! ¡Nya!": {
            "titulo": "🌲 Sala de aventura Detectada",
            "descripcion": "¡Una nueva sala de aventura ha aparecido!",
            "color": 0x55FF55
        }
    }

    # Detectar aventuras
    for palabra, datos in salas.items():

        if palabra in texto:

            canal = bot.get_channel(CANAL_AVENTURAS)

            if canal:

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

            break

    await bot.process_commands(message)

# =========================
# KEEP ALIVE
# =========================

keep_alive()

# =========================
# INICIAR BOT
# =========================

bot.run(TOKEN)