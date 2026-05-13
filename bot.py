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

    # Ignorar propio bot
    if message.author == bot.user:
        return

    # SOLO Nekotina
    if message.author.id != NEKOTINA_ID:
        return

    # SOLO canal específico
    if message.channel.id != CANAL_DETECCION:
        return

    print("📩 MENSAJE DETECTADO")

    # =========================================
    # DEBUG TOTAL
    # =========================================

    print("Contenido:", message.content)
    print("Embeds:", len(message.embeds))

    for i, embed in enumerate(message.embeds):

        print(f"\n===== EMBED {i+1} =====")

        print("TITLE:")
        print(embed.title)

        print("DESCRIPTION:")
        print(embed.description)

        print("FIELDS:")

        for field in embed.fields:
            print(field.name)
            print(field.value)

    # =========================================
    # TEXTO TOTAL
    # =========================================

    texto = str(message.embeds).lower()

    print("\nTEXTO FINAL:")
    print(texto)

    aventuras = {

        "magma": {
            "titulo": "🌋 Sala de Magma Detectada",
            "descripcion": "¡Una nueva aventura de Magma ha aparecido!",
            "color": 0xFF5500,
            "gif": "https://media.tenor.com/7lSun5w8XJAAAAAC/lava.gif"
        },

        "outlands": {
            "titulo": "🏝 Sala de Outlands Detectada",
            "descripcion": "¡Una nueva aventura de Outlands ha aparecido!",
            "color": 0x00AAFF,
            "gif": "https://media.tenor.com/2uyENRmiUt0AAAAC/anime.gif"
        },

        "whispering": {
            "titulo": "🌲 Sala de Whispering Detectada",
            "descripcion": "¡Una nueva aventura de Whispering ha aparecido!",
            "color": 0x55FF55,
            "gif": "https://media.tenor.com/Ye7Sk9i6Ck0AAAAC/forest.gif"
        }
    }

    for palabra, datos in aventuras.items():

        if palabra in texto:

            print(f"✅ DETECTADO: {palabra}")

            canal = bot.get_channel(CANAL_ALERTAS)

            if canal:

                embed = discord.Embed(
                    title=datos["titulo"],
                    description=datos["descripcion"],
                    color=datos["color"]
                )

                embed.set_thumbnail(url=datos["gif"])

                embed.add_field(
                    name="🔔 Rol",
                    value=f"<@&{ROL_AVENTURA}>",
                    inline=False
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

bot.run(TOKEN)