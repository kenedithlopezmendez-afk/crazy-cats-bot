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
def home(): return "Crazy Tracker Activo 🐾"

def run(): app.run(host="0.0.0.0", port=10000)
def keep_alive():
    t = Thread(target=run)
    t.start()

# ==================================================
# CONFIG BOT
# ==================================================
TOKEN = os.environ["TOKEN"]
intents = discord.Intents.default()
intents.message_content = True 

bot = commands.Bot(command_prefix="?", intents=intents)

CANAL_DETECCION = 1436358970284572723
ROL_AVENTURA = 1436361900215500870

# ==================================================
# LÓGICA DE DETECCIÓN
# ==================================================
async def escanear_novedad(message):
    if message.channel.id != CANAL_DETECCION or message.author.id == bot.user.id:
        return

    bolsa_de_texto = ""
    if message.content:
        bolsa_de_texto += message.content.lower()

    if message.embeds:
        for emb in message.embeds:
            # Capturamos título, descripción y campos
            if emb.title: bolsa_de_texto += f" {emb.title.lower()}"
            if emb.description: bolsa_de_texto += f" {emb.description.lower()}"
            for field in emb.fields:
                bolsa_de_texto += f" {field.name.lower()} {field.value.lower()}"

    # --- AQUÍ ESTÁ EL CAMBIO IMPORTANTE ---
    # Usamos el ID del emoji y el texto exacto. 
    # Nekotina usa: ### <:nk:1423430200430952510> Sala de Aventura
    
    encontrado = False
    # Definimos los disparadores exactos (en minúsculas porque usamos .lower())
    disparador_emoji = "<:nk:1423430200430952510>"
    disparador_texto = "sala de aventura"

    if disparador_texto in bolsa_de_texto or disparador_emoji in bolsa_de_texto:
        encontrado = True
        
        zona = "Aventura"
        color = 0x2f3136

        if "magma" in bolsa_de_texto:
            zona = "MAGMA 🌋"
            color = 0xFF5A1F
        elif "outlands" in bolsa_de_texto or "tierras remotas" in bolsa_de_texto:
            zona = "OUTLANDS 🏝"
            color = 0x00BFFF
        elif "whispering" in bolsa_de_texto:
            zona = "WHISPERING 🌲"
            color = 0x57F287

        if encontrado:
            canal = bot.get_channel(CANAL_DETECCION)
            if canal:
                embed = discord.Embed(
                    title=f"🚨 ¡SALA DE {zona} DETECTADA!",
                    description=f"¡Nekotina ha abierto una sala! <@&{ROL_AVENTURA}>",
                    color=color
                )
                await canal.send(content=f"🔔 <@&{ROL_AVENTURA}>", embed=embed)

# ==================================================
# EVENTOS
# ==================================================
@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")

@bot.event
async def on_message(message):
    await escanear_novedad(message)

@bot.event
async def on_message_edit(before, after):
    await escanear_novedad(after)

if __name__ == "__main__":
    keep_alive()
    bot.run(TOKEN)