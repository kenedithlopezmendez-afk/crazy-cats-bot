import discord
from discord.ext import commands
from flask import Flask
from threading import Thread
import os

# =========================================
# FLASK / KEEP ALIVE PARA RENDER
# =========================================

app = Flask(__name__)

@app.route("/")
def home():
    return "Crazy Tracker activo"

def run():
    app.run(host="0.0.0.0", port=10000)

def keep_alive():
    t = Thread(target=run)
    t.start()

# =========================================
# CONFIGURACIÓN DEL BOT
# =========================================

TOKEN = os.environ["TOKEN"]

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="?",
    intents=intents
)

# =========================================
# IDs
# =========================================

# Canal EXACTO donde Nekotina manda aventuras
CANAL_DETECCION = 1436358970284572723

# Canal donde tu bot enviará las alertas
CANAL_ALERTAS = 1436358970284572723

# Rol a mencionar
ROL_AVENTURA = 1436361900215500870

# ID de Nekotina
NEKOTINA_ID = 429457053791158281

# =========================================
# BOT ONLINE
# =========================================

@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")

# =========================================
# DETECTOR DE AVENTURAS
# =========================================

@bot.event
async def on_message(message):

    # Ignorar mensajes propios
    if message.author == bot.user:
        return

    # SOLO mensajes de Nekotina
    if message.author.id != NEKOTINA_ID:
        return

    # SOLO detectar en canal específico
    # Esto evita detectar privados u otros canales
    if message.channel.id != CANAL_DETECCION:
        return

    # =========================================
    # LEER TODO EL TEXTO POSIBLE
    # =========================================

    texto = message.content.lower()

    # Leer TODOS los embeds
    for embed in message.embeds:

        # Título
        if embed.title:
            texto += " " + embed.title.lower()

        # Descripción
        if embed.description:
            texto += " " + embed.description.lower()

        # Fields/campos
        for field in embed.fields:
            texto += " " + field.name.lower()
            texto += " " + field.value.lower()

    print(texto)

    # =========================================
    # AVENTURAS
    # =========================================

    salas = {
        "magma": {
            "titulo": "🌋 Sala de Magma Detectada",
            "descripcion": "¡Una nueva sala de aventura de Magma ha aparecido!",
            "color": 0xFF5500,
            "gif": "https://media.tenor.com/7lSun5w8XJAAAAAC/lava.gif"
        },

        "outlands": {
            "titulo": "🏝 Sala de Outlands Detectada",
            "descripcion": "¡Una nueva sala de aventura de Outlands ha aparecido!",
            "color": 0x00AAFF,
            "gif": "https://media.tenor.com/2uyENRmiUt0AAAAC/anime.gif"
        },

        "whispering": {
            "titulo": "🌲 Sala de Whispering Detectada",
            "descripcion": "¡Una nueva sala de aventura de Whispering ha aparecido!",
            "color": 0x55FF55,
            "gif": "https://media.tenor.com/Ye7Sk9i6Ck0AAAAC/forest.gif"
        }
    }

       # =========================================
    # DETECTAR AVENTURAS
    # =========================================

    for palabra, datos in salas.items():

        if (
            "sala de aventura" in texto
            and palabra in texto
        ):

            canal = bot.get_channel(CANAL_ALERTAS)

            if canal:

                nuevo_embed = discord.Embed(
                    title=datos["titulo"],
                    description=datos["descripcion"],
                    color=datos["color"]
                )

                # GIF
                nuevo_embed.set_thumbnail(
                    url=datos["gif"]
                )

                nuevo_embed.add_field(
                    name="📍 Canal Detectado",
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

# =========================================
# KEEP ALIVE
# =========================================

keep_alive()

# =========================================
# INICIAR BOT
# =========================================

bot.run(TOKEN)