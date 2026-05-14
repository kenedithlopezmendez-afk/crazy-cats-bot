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

    # =========================================
    # IGNORAR OTROS BOTS EXCEPTO NEKOTINA
    # =========================================

    NEKOTINA_ID = 429457053791158281

    if message.author.bot and message.author.id != NEKOTINA_ID:
        return

    # =========================================
    # SOLO LEER ESTE CANAL
    # =========================================

    CANAL_DETECCION = 1436358970284572723

    if message.channel.id != CANAL_DETECCION:
        return

    # =========================================
    # IDS
    # =========================================

    CANAL_ALERTAS = 1436358970284572723
    ROL_AVENTURA = 1436361900215500870

    # =========================================
    # LEER TEXTO Y EMBEDS
    # =========================================

    texto = (
        message.content +
        " " +
        str(message.embeds)
    ).lower()

    logging.info(f"📩 TEXTO DETECTADO: {texto}")

    # =========================================
    # CONFIG AVENTURAS
    # =========================================

    aventuras = {

        "magma": {
            "titulo": "🌋 Sala de Magma Detectada",
            "descripcion": (
                "🔥 Una aventura de **Magma** ha aparecido.\n"
                "¡Entren rápido aventureros!"
            ),
            "color": 0xFF5A1F,
            "gif": "https://media.tenor.com/7lSun5w8XJAAAAAC/lava.gif"
        },

        "outlands": {
            "titulo": "🏝 Sala de Outlands Detectada",
            "descripcion": (
                "✨ Una aventura de **Outlands** ha aparecido.\n"
                "¡Hora de explorar nuevas tierras!"
            ),
            "color": 0x00BFFF,
            "gif": "https://media.tenor.com/2uyENRmiUt0AAAAC/anime.gif"
        },

        "whispering": {
            "titulo": "🌲 Sala de Whispering Detectada",
            "descripcion": (
                "🌲 Una aventura de **Whispering** ha aparecido.\n"
                "Los bosques misteriosos esperan..."
            ),
            "color": 0x57F287,
            "gif": "https://media.tenor.com/Ye7Sk9i6Ck0AAAAC/forest.gif"
        }
    }

    # =========================================
    # DETECCIÓN
    # =========================================

    for palabra, datos in aventuras.items():

        if palabra in texto:

            logging.info(f"✅ Detectado: {palabra}")

            canal = bot.get_channel(CANAL_ALERTAS)

            if canal:

                embed = discord.Embed(
                    title=datos["titulo"],
                    description=datos["descripcion"],
                    color=datos["color"]
                )

                # GIF ARRIBA DERECHA
                embed.set_thumbnail(
                    url=datos["gif"]
                )

                # PING DENTRO DEL EMBED
                embed.add_field(
                    name="🔔 Aventureros",
                    value=f"<@&{ROL_AVENTURA}>",
                    inline=False
                )

                # CANAL DETECTADO
                embed.add_field(
                    name="📍 Canal Detectado",
                    value=message.channel.mention,
                    inline=True
                )

                embed.add_field(
                    name="🤖 Sistema",
                    value="Crazy Tracker",
                    inline=True
                )

                embed.set_footer(
                    text="Crazy Cats • Sistema Automático"
                )

                await canal.send(embed=embed)

            break

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