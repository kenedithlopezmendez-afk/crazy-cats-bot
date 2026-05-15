import discord
from discord.ext import commands
from flask import Flask
from threading import Thread
import os

# ==================================================
# MANTENER VIVO EN RENDER
# ==================================================
app = Flask(__name__)
@app.route("/")
def home(): return "Servidor de Detección Activo 🐾"

def run(): app.run(host="0.0.0.0", port=10000)
def keep_alive():
    t = Thread(target=run)
    t.start()

# ==================================================
# CONFIGURACIÓN DEL BOT
# ==================================================
TOKEN = os.environ["TOKEN"]

# Necesitamos todos los privilegios de lectura
intents = discord.Intents.default()
intents.message_content = True 
intents.messages = True

bot = commands.Bot(command_prefix="?", intents=intents)

# IDs de tu servidor
CANAL_DETECCION = 1436358970284572723
ROL_AVENTURA = 1436361900215500870

# ==================================================
# NÚCLEO DE DETECCIÓN (LA "TRAMPA")
# ==================================================
async def escanear_novedad(message):
    # Solo miramos tu canal de aventuras
    if message.channel.id != CANAL_DETECCION:
        return

    # Si es nuestro propio mensaje de alerta, lo ignoramos
    if message.author.id == bot.user.id:
        return

    encontrado = False
    zona = "Aventura"
    color = 0x2f3136

    # 1. Buscamos en el texto normal (tus pruebas)
    texto_plano = message.content.lower() if message.content else ""
    
    # 2. Buscamos en los EMBEDS (Lo que manda Nekotina)
    # Analizamos título, descripción y campos del cuadrito
    contenido_embed = ""
    if message.embeds:
        for emb in message.embeds:
            if emb.title: contenido_embed += f" {emb.title.lower()}"
            if emb.description: contenido_embed += f" {emb.description.lower()}"
            for field in emb.fields:
                contenido_embed += f" {field.name.lower()} {field.value.lower()}"

    total_info = texto_plano + contenido_embed

    # CRITERIO: ¿Es una sala de aventura de Nekotina?
    if "sala de aventura" in total_info or "¡únete" in total_info:
        encontrado = True
        if "magma" in total_info:
            zona = "MAGMA 🌋"
            color = 0xFF5A1F
        elif "outlands" in total_info or "tierras remotas" in total_info:
            zona = "OUTLANDS 🏝"
            color = 0x00BFFF
        elif "whispering" in total_info:
            zona = "WHISPERING 🌲"
            color = 0x57F287

    # 3. SI DETECTAMOS ALGO, DISPARAMOS LA ALERTA
    if encontrado:
        canal = bot.get_channel(CANAL_DETECCION)
        if canal:
            # Creamos nuestra propia alerta
            alerta = discord.Embed(
                title=f"🚨 ¡NUEVA SALA EN {zona}!",
                description=f"Se ha detectado actividad de Nekotina.\n¡Vayan rápido! <@&{ROL_AVENTURA}>",
                color=color
            )
            alerta.set_footer(text="Crazy Cats • Auto-Tracker")
            
            # El ping va fuera para que notifique a todos
            await canal.send(content=f"🔔 <@&{ROL_AVENTURA}>", embed=alerta)
            print(f"✅ ¡Sala de {zona} detectada y avisada!")

# ==================================================
# EVENTOS DE ESCUCHA
# ==================================================
@bot.event
async def on_ready():
    print(f"✅ Bot conectado con éxito como {bot.user}")

@bot.event
async def on_message(message):
    # Detecta mensajes nuevos (y tus pruebas de texto)
    await escanear_novedad(message)
    await bot.process_commands(message)

@bot.event
async def on_message_edit(before, after):
    # ¡ESTO ES LO MÁS IMPORTANTE! 
    # Nekotina a veces envía el mensaje y luego lo actualiza con el embed.
    await escanear_novedad(after)

# ==================================================
# EJECUCIÓN
# ==================================================
if __name__ == "__main__":
    keep_alive()
    bot.run(TOKEN)