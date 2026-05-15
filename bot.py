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
intents.message_content = True  # ¡Esto es lo que activaste en el panel!

bot = commands.Bot(
    command_prefix="?",
    intents=intents
)

# IDs Globales
NEKOTINA_ID = 701013303063543868
CANAL_DETECCION = 1436358970284572723
CANAL_ALERTAS = 1436358970284572723
ROL_AVENTURA = 1436361900215500870

# ==================================================
# LOGICA DE DETECCION (FUNCIÓN REUTILIZABLE)
# ==================================================
async def procesar_aventura(message):
    if message.author.id != NEKOTINA_ID or message.channel.id != CANAL_DETECCION:
        return

    if not message.embeds:
        return

    for embed_original in message.embeds:
        titulo = str(embed_original.title).lower()
        
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

        if "sala de aventura" in titulo:
            for palabra, datos in aventuras.items():
                if palabra in titulo:
                    logging.info(f"✅ SALA DETECTADA: {palabra}")
                    canal = bot.get_channel(CANAL_ALERTAS)
                    
                    if canal:
                        embed = discord.Embed(
                            title=datos["titulo"],
                            description=datos["descripcion"],
                            color=datos["color"]
                        )
                        embed.set_thumbnail(url=datos["gif"])
                        embed.add_field(
                            name="🔔 Aventureros",
                            value=f"<@&{ROL_AVENTURA}>",
                            inline=False
                        )
                        embed.set_footer(text="Crazy Cats • Tracker")
                        
                        await canal.send(content=f"<@&{ROL_AVENTURA}>", embed=embed)
                    return

# ==================================================
# EVENTOS
# ==================================================
@bot.event
async def on_ready():
    print(f"✅ Conectado como {bot.user}")

@bot.event
async def on_message(message):
    # Detecta cuando la sala aparece por primera vez
    await procesar_aventura(message)
    await bot.process_commands(message)

@bot.event
async def on_message_edit(before, after):
    # Detecta si la sala cambia o se actualiza
    await procesar_aventura(after)

# ==================================================
# INICIO
# ==================================================
keep_alive()
print("🔥 Iniciando bot...")
bot.run(TOKEN)