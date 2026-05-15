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

    NEKOTINA_ID = 429457053791158281

    CANAL_DETECCION = 1436358970284572723
    CANAL_ALERTAS = 1436358970284572723
    ROL_AVENTURA = 1436361900215500870

    # Ignorar otros bots
    if message.author.bot and message.author.id != NEKOTINA_ID:
        return

    # Solo canal específico
    if message.channel.id != CANAL_DETECCION:
        return

    texto = message.content.lower()

    # =========================================
    # LEER EMBEDS
    # =========================================

    if message.embeds:

        for embed_original in message.embeds:

            titulo = str(embed_original.title).lower()
            descripcion = str(embed_original.description).lower()

            logging.info(f"📌 TITULO: {titulo}")
            logging.info(f"📌 DESC: {descripcion}")

            # =====================================
            # DETECTAR SALAS
            # =====================================

            aventuras = {

                "magma": {
                    "titulo": "🌋 Sala de Magma Detectada",
                    "descripcion": "🔥 ¡Nueva sala de Magma disponible!",
                    "color": 0xFF5A1F,
                    "gif": "https://media.tenor.com/7lSun5w8XJAAAAAC/lava.gif"
                },

                "outlands": {
                    "titulo": "🏝 Sala de Outlands Detectada",
                    "descripcion": "✨ ¡Nueva sala de Outlands disponible!",
                    "color": 0x00BFFF,
                    "gif": "https://media.tenor.com/2uyENRmiUt0AAAAC/anime.gif"
                },

                "whispering": {
                    "titulo": "🌲 Sala de Whispering Detectada",
                    "descripcion": "🌲 ¡Nueva sala de Whispering disponible!",
                    "color": 0x57F287,
                    "gif": "https://media.tenor.com/Ye7Sk9i6Ck0AAAAC/forest.gif"
                }
            }

            for palabra, datos in aventuras.items():

                if (
                    "sala de aventura" in titulo
                    and palabra in titulo
                ):

                    logging.info(f"✅ Sala detectada: {palabra}")

                    canal = bot.get_channel(CANAL_ALERTAS)

                    if canal:

                        embed = discord.Embed(
                            title=datos["titulo"],
                            description=datos["descripcion"],
                            color=datos["color"]
                        )

                        embed.set_thumbnail(
                            url=datos["gif"]
                        )

                        embed.add_field(
                            name="🔔 Aventureros",
                            value=f"<@&{ROL_AVENTURA}>",
                            inline=False
                        )

                        embed.add_field(
                            name="📍 Canal",
                            value=message.channel.mention,
                            inline=True
                        )

                        embed.set_footer(
                            text="Crazy Cats • Tracker"
                        )

                        await canal.send(embed=embed)

                    return

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