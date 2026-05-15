import discord
from discord.ext import commands
from flask import Flask
from threading import Thread
import os
import logging

# Configuración de logs básica para ver qué pasa en Render
logging.basicConfig(level=logging.INFO)

# ==================================================
# FLASK / KEEP ALIVE (Para que Render no lo apague)
# ==================================================
app = Flask(__name__)

@app.route("/")
def home():
    return "Crazy Tracker activo y vigilando 🐾"

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
intents.message_content = True  # IMPORTANTE: Ya lo activaste en el portal

bot = commands.Bot(
    command_prefix="?",
    intents=intents
)

# ==================================================
# CONFIGURACIÓN DE IDs (Verifica que estos sean correctos)
# ==================================================
NEKOTINA_ID = 701013303063543868  # ID Real de Nekotina
CANAL_DETECCION = 1436358970284572723
CANAL_ALERTAS = 1436358970284572723
ROL_AVENTURA = 1436361900215500870

# ==================================================
# LÓGICA DE DETECCIÓN
# ==================================================
async def procesar_aventura(message):
    # Validamos que sea Nekotina y en el canal correcto
    if message.author.id != NEKOTINA_ID:
        return
    if message.channel.id != CANAL_DETECCION:
        return
    if not message.embeds:
        return

    for emb in message.embeds:
        # Extraemos texto de título y descripción para buscar salas
        contenido = ""
        if emb.title: contenido += emb.title.lower()
        if emb.description: contenido += emb.description.lower()
        
        # Log para debug en Render
        print(f"🔍 Analizando embed de Nekotina: {contenido}")

        if "sala de aventura" in contenido or "¡únete con tus mascotas!" in contenido:
            
            # Datos por defecto
            titulo_alerta = "✨ Nueva Sala Detectada"
            desc_alerta = "¡Una nueva aventura ha comenzado!"
            color_alerta = 0x2f3136
            img_alerta = ""

            # Personalización por zona
            if "magma" in contenido:
                titulo_alerta = "🌋 ¡SALA DE MAGMA DETECTADA!"
                desc_alerta = "🔥 El calor aumenta, ¡únete antes de que despegue!"
                color_alerta = 0xFF5A1F
                img_alerta = "https://media.tenor.com/7lSun5w8XJAAAAAC/lava.gif"
            
            elif "outlands" in contenido:
                titulo_alerta = "🏝 ¡SALA DE OUTLANDS DETECTADA!"
                desc_alerta = "✨ ¡Una zona misteriosa ha aparecido!"
                color_alerta = 0x00BFFF
                img_alerta = "https://media.tenor.com/2uyENRmiUt0AAAAC/anime.gif"
            
            elif "whispering" in contenido:
                titulo_alerta = "🌲 ¡SALA DE WHISPERING DETECTADA!"
                desc_alerta = "🌲 ¡Adéntrate en el bosque susurrante!"
                color_alerta = 0x57F287
                img_alerta = "https://media.tenor.com/Ye7Sk9i6Ck0AAAAC/forest.gif"

            # Enviar la alerta
            canal = bot.get_channel(CANAL_ALERTAS)
            if canal:
                embed = discord.Embed(
                    title=titulo_alerta,
                    description=desc_alerta,
                    color=color_alerta
                )
                if img_alerta:
                    embed.set_thumbnail(url=img_alerta)
                
                embed.add_field(name="🔔 Aviso", value=f"¡Corran! <@&{ROL_AVENTURA}>", inline=False)
                embed.set_footer(text="Crazy Cats • Tracker")

                # Mandamos el ping fuera del embed para que notifique al móvil
                await canal.send(content=f"<@&{ROL_AVENTURA}>", embed=embed)
                print(f"✅ Alerta enviada para la zona: {titulo_alerta}")
            return

# ==================================================
# EVENTOS DEL BOT
# ==================================================
@bot.event
async def on_ready():
    print(f"✅ Crazy Tracker conectado como {bot.user}")

@bot.event
async def on_message(message):
    # Detecta cuando la sala se publica (mensaje nuevo)
    await procesar_aventura(message)
    await bot.process_commands(message)

@bot.event
async def on_message_edit(before, after):
    # Detecta si Nekotina edita el mensaje (muy común en sus aventuras)
    await procesar_aventura(after)

# ==================================================
# INICIO DEL SERVICIO
# ==================================================
if __name__ == "__main__":
    keep_alive()
    print("🔥 Iniciando conexión con Discord...")
    try:
        bot.run(TOKEN)
    except Exception as e:
        print(f"❌ Error al iniciar el bot: {e}")