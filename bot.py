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

    # Ignorar mensajes propios
    if message.author == bot.user:
        return

    # SOLO detectar Nekotina
    if message.author.id != NEKOTINA_ID:
        return

    # SOLO detectar en canal específico
    if message.channel.id != CANAL_DETECCION:
        return

    # ==========================================
    # LEER TODO EL TEXTO POSIBLE
    # ==========================================

    texto = message.content.lower()

    for embed in message.embeds:

        if embed.title:
            texto += " " + embed.title.lower()

        if embed.description:
            texto += " " + embed.description.lower()

        for field in embed.fields:
            texto += " " + field.name.lower()
            texto += " " + field.value.lower()

    print(texto)

    # ==========================================
    # CONFIG AVENTURAS
    # ==========================================

    aventuras = {

        "magma": {
            "titulo": "🌋 Sala de Magma Detectada",
            "descripcion": (
                "Una nueva aventura de **Magma** ha aparecido.\n"
                "¡Prepárense para entrar a la sala! 🔥"
            ),
            "color": 0xFF5A1F,
            "gif": "https://media.tenor.com/7lSun5w8XJAAAAAC/lava.gif"
        },

        "outlands": {
            "titulo": "🏝 Sala de Outlands Detectada",
            "descripcion": (
                "Una nueva aventura de **Outlands** ha aparecido.\n"
                "¡Hora de explorar nuevas zonas! ✨"
            ),
            "color": 0x00BFFF,
            "gif": "https://media.tenor.com/2uyENRmiUt0AAAAC/anime.gif"
        },

        "whispering": {
            "titulo": "🌲 Sala de Whispering Detectada",
            "descripcion": (
                "Una nueva aventura de **Whispering** ha aparecido.\n"
                "El bosque misterioso espera... 🌲"
            ),
            "color": 0x57F287,
            "gif": "https://media.tenor.com/Ye7Sk9i6Ck0AAAAC/forest.gif"
        }
    }

    # ==========================================
    # DETECCIÓN
    # ==========================================

    for palabra, datos in aventuras.items():

        # Debe contener:
        # "sala"
        # y además magma/outlands/whispering

        if "sala" in texto and palabra in texto:

            canal = bot.get_channel(CANAL_ALERTAS)

            if canal:

                embed = discord.Embed(
                    title=datos["titulo"],
                    description=datos["descripcion"],
                    color=datos["color"]
                )

                # GIF elegante
                embed.set_thumbnail(
                    url=datos["gif"]
                )

                # Ping dentro embed
                embed.add_field(
                    name="🔔 Notificación",
                    value=f"<@&{ROL_AVENTURA}>",
                    inline=False
                )

                embed.add_field(
                    name="📍 Detectado en",
                    value=message.channel.mention,
                    inline=True
                )

                embed.add_field(
                    name="🤖 Sistema",
                    value="Crazy Tracker",
                    inline=True
                )

                embed.set_footer(
                    text="Crazy Tracker • Sistema Automático"
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