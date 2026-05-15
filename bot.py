import discord
from discord.ext import commands
from flask import Flask
from threading import Thread
import os
import logging

# Configuración de logs para ver el rastro en Render
logging.basicConfig(level=logging.INFO)

# ==================================================
# FLASK / KEEP ALIVE
# ==================================================
app = Flask(__name__)

@app.route("/")
def home():
    return "Crazy Tracker: Escaneando Aventuras 🐾"

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

# IDs de tu servidor (Verifica que sean estos)
CANAL_DETECCION = 1436358970284572723
CANAL_ALERTAS = 1436358970284572723
ROL_AVENTURA = 1436361900215500870

# ==================================================
# LÓGICA DE ESCÁNER DE AVENTURAS
# ==================================================
async def procesar_aventura(message):
    # 1. Filtro de Canal (Vital para no leer todo el server)
    if message.channel.id != CANAL_DETECCION:
        return

    # 2. Verificar si tiene Embeds (Las salas de Nekotina siempre son embeds)
    if not message.embeds:
        return

    for emb in message.embeds:
        # Extraemos todo el texto posible
        contenido = ""
        if emb.title: contenido += emb.title.lower()
        if emb.description: contenido += emb.description.lower()
        if emb.author and emb.author.name: contenido += emb.author.name.lower()
        
        # Este log es para que tú veas en Render que el bot está leyendo
        print(f"📡 ESCÁNER: Leyendo contenido de {message.author.name}...")

        # 3. Detectar si es una Sala de Aventura
        if "sala de aventura" in contenido or "¡únete con tus mascotas!" in contenido:
            
            # Valores por defecto
            zona_nombre = "Aventura Desconocida"
            color_hex = 0x2f3136
            gif_url = ""

            # 4. Clasificar por Zona
            if "magma" in contenido:
                zona_nombre = "MAGMA 🌋"
                color_hex = 0xFF5A1F
                gif_url = "https://media.tenor.com/7lSun5w8XJAAAAAC/lava.gif"
            elif "outlands" in contenido or "tierras remotas" in contenido:
                zona_nombre = "OUTLANDS 🏝"
                color_hex = 0x00BFFF
                gif_url = "https://media.tenor.com/2uyENRmiUt0AAAAC/anime.gif"
            elif "whispering" in contenido:
                zona_nombre = "WHISPERING 🌲"
                color_hex = 0x57F287
                gif_url = "https://media.tenor.com/Ye7Sk9i6Ck0AAAAC/forest.gif"

            # 5. Enviar la Alerta
            canal = bot.get_channel(CANAL_ALERTAS)
            if canal:
                embed_alerta = discord.Embed(
                    title=f"🚨 ¡SALA DE {zona_nombre} DETECTADA!",
                    description=f"Se ha abierto una nueva sala en el canal <#{CANAL_DETECCION}>.\n¡Únanse rápido!",
                    color=color_hex
                )
                if gif_url:
                    embed_alerta.set_thumbnail(url=gif_url)
                
                embed_alerta.set_footer(text="Crazy Cats • Tracker v2")
                
                # Ping al rol fuera del embed
                await canal.send(content=f"🔔 <@&{ROL_AVENTURA}>", embed=embed_alerta)
                print(f"✅ Alerta enviada para {zona_nombre}")
            return

# ==================================================
# EVENTOS
# ==================================================
@bot.event
async def on_ready():
    print(f"✅ Crazy Tracker conectado como {bot.user}")

@bot.event
async def on_message(message):
    # Detección en mensajes nuevos
    await procesar_aventura(message)
    await bot.process_commands(message)

@bot.event
async def on_message_edit(before, after):
    # Detección en mensajes editados (Nekotina edita mucho)
    await procesar_aventura(after)

# ==================================================
# INICIO
# ==================================================
if __name__ == "__main__":
    keep_alive()
    print("🔥 Iniciando conexión...")
    bot.run(TOKEN)