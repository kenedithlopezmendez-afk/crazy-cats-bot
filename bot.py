import discord
from discord.ext import commands
from flask import Flask
from threading import Thread
import os
import logging

# Configuración de logs para Render
logging.basicConfig(level=logging.INFO)

# ==================================================
# FLASK / KEEP ALIVE
# ==================================================
app = Flask(__name__)

@app.route("/")
def home():
    return "Crazy Tracker: Vigilando Aventuras de Nekotina 🐾"

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

# IDs de tu servidor (Mantenemos los que me pasaste)
CANAL_DETECCION =1436358970284572723
CANAL_ALERTAS =1436358970284572723
ROL_AVENTURA =1436361900215500870

# ==================================================
# LÓGICA DE ESCÁNER ULTRA-SENSIBLE
# ==================================================
async def procesar_aventura(message):
    # 1. Filtro de Canal
    if message.channel.id != CANAL_DETECCION:
        return

    # Evitamos que el bot se responda a sí mismo
    if message.author.id == bot.user.id:
        return

    # 2. Recolección de TODO el texto del mensaje
    bolsa_de_texto = ""
    
    # Texto plano (por si escribes la prueba tú)
    if message.content:
        bolsa_de_texto += message.content.lower()
    
    # Contenido de Embeds (Lo que manda Nekotina)
    if message.embeds:
        for emb in message.embeds:
            if emb.title: bolsa_de_texto += f" {emb.title.lower()}"
            if emb.description: bolsa_de_texto += f" {emb.description.lower()}"
            if emb.author and emb.author.name: bolsa_de_texto += f" {emb.author.name.lower()}"
            
            # Revisar campos (donde suele decir Equipo, Despegue, etc.)
            for field in emb.fields:
                bolsa_de_texto += f" {field.name.lower()} {field.value.lower()}"

    # Si no hay texto, no hacemos nada
    if not bolsa_de_texto:
        return

    # DEBUG: Verás esto en Render cuando llegue algo al canal
    print(f"📥 MENSAJE RECIBIDO: {message.author.name} dice: {bolsa_de_texto[:100]}...")

    # 3. Detección de Sala
    palabras_clave = ["sala de aventura", "mascotas", "¡únete"]
    if any(palabra in bolsa_de_texto for palabra in palabras_clave):
        
        zona = "Aventura"
        color = 0x2f3136
        gif = ""

        # Identificar la zona específica
        if "magma" in bolsa_de_texto:
            zona = "MAGMA 🌋"
            color = 0xFF5A1F
            gif = "https://media.tenor.com/7lSun5w8XJAAAAAC/lava.gif"
        elif "outlands" in bolsa_de_texto or "tierras remotas" in bolsa_de_texto:
            zona = "OUTLANDS 🏝"
            color = 0x00BFFF
            gif = "https://media.tenor.com/2uyENRmiUt0AAAAC/anime.gif"
        elif "whispering" in bolsa_de_texto or "susurrante" in bolsa_de_texto:
            zona = "WHISPERING 🌲"
            color = 0x57F287
            gif = "https://media.tenor.com/Ye7Sk9i6Ck0AAAAC/forest.gif"

        canal = bot.get_channel(CANAL_ALERTAS)
        if canal:
            # Crear el embed de alerta para tu server
            embed_alerta = discord.Embed(
                title=f"🚨 ¡SALA DE {zona} DETECTADA!",
                description=f"¡Se ha abierto una nueva sala! <@&{ROL_AVENTURA}>\n\n**Canal:** <#{CANAL_DETECCION}>",
                color=color
            )
            if gif:
                embed_alerta.set_thumbnail(url=gif)
            
            embed_alerta.set_footer(text="Crazy Cats • Tracker Final")
            
            # Mandamos el ping y el embed
            await canal.send(content=f"🔔 <@&{ROL_AVENTURA}>", embed=embed_alerta)
            print(f"✅ ALERTA ENVIADA: {zona}")

# ==================================================
# EVENTOS DEL BOT
# ==================================================
@bot.event
async def on_ready():
    print(f"✅ Crazy Tracker conectado como {bot.user}")

@bot.event
async def on_message(message):
    await procesar_aventura(message)
    await bot.process_commands(message)

@bot.event
async def on_message_edit(before, after):
    # Esto es clave para detectar cuando la gente se une y el embed cambia
    await procesar_aventura(after)

# ==================================================
# INICIO
# ==================================================
if __name__ == "__main__":
    keep_alive()
    print("🔥 Iniciando conexión con Discord...")
    bot.run(TOKEN)