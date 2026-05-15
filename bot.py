import discord
from discord.ext import commands
from flask import Flask
from threading import Thread
import os
import logging

# Configuración de logs básica para ver movimientos en Render
logging.basicConfig(level=logging.INFO)

# ==================================================
# FLASK / KEEP ALIVE (Para evitar el apagado en Render)
# ==================================================
app = Flask(__name__)

@app.route("/")
def home():
    return "Crazy Tracker: Escáner de Aventuras Activo 🐾"

def run():
    app.run(host="0.0.0.0", port=10000)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ==================================================
# CONFIGURACIÓN DEL BOT Y SUS INTENTS
# ==================================================
TOKEN = os.environ["TOKEN"]

intents = discord.Intents.default()
intents.message_content = True 
intents.messages = True

bot = commands.Bot(command_prefix="?", intents=intents)

# -------- CONFIGURACIÓN DE IDs DE TU SERVIDOR --------
CANAL_AVENTURAS = 1436358970284572723  # Canal donde el bot enviará el ping
ROL_AVENTURA = 1436361900215500870     # Rol a etiquetar
CANAL_DETECCION = 1436358970284572723  # Canal exclusivo donde juega Nekotina

# ID DE NEKOTINA (Cambia este ID si usas la versión App global o el Bot clásico)
NEKOTINA_ID = 429457053791158281  

# ==================================================
# NÚCLEO DEL DETECTOR
# ==================================================
async def verificar_y_enviar_alerta(message):
    # 1. RESTRICCIÓN: Detectar SOLO en el canal especificado
    if message.channel.id != CANAL_DETECCION:
        return

    # 2. RESTRICCIÓN: Detectar SOLO mensajes que vengan de Nekotina
    if message.author.id != NEKOTINA_ID:
        return

    # Si no contiene embeds, ignoramos
    if not message.embeds:
        return

    # Mapeo de zonas según las palabras clave secundarias
    salas = {
        "magma": {
            "titulo": "🌋 ¡SALA DE MAGMA DETECTADA!",
            "descripcion": "🔥 El calor aumenta, ¡prepara tus mascotas y únete antes de que despegue!",
            "color": 0xFF5500
        },
        "remotas": {
            "titulo": "🏝 ¡SALA DE OUTLANDS DETECTADA!",
            "descripcion": "✨ ¡Una zona misteriosa ha aparecido! Corran a unirse.",
            "color": 0x00AAFF
        },
        "whispering": {
            "titulo": "🌲 ¡SALA DE WHISPERING DETECTADA!",
            "descripcion": "🌲 ¡El bosque susurra... una nueva aventura está disponible!",
            "color": 0x55FF55
        }
    }

    # Leer el contenido de los embeds
    for embed in message.embeds:
        texto = ""

        if embed.title:
            texto += embed.title.lower()

        if embed.description:
            texto += embed.description.lower()

        # Escanear también los campos internos por si el nombre de la zona cae ahí
        for field in embed.fields:
            texto += f" {field.name.lower()} {field.value.lower()}"

        # 3. FILTRO: Debe detectar la palabra "aventura"
        if "aventura" in texto:
            
            zona_encontrada = None
            
            for palabra, datos in salas.items():
                if palabra in texto:
                    zona_encontrada = datos
                    break 
            
            # Formato genérico si no encuentra una zona del diccionario
            if not zona_encontrada:
                zona_encontrada = {
                    "titulo": "⚔️ ¡NUEVA AVENTURA DETECTADA!",
                    "descripcion": "¡Una sala de aventura ha aparecido! Revisen el canal.",
                    "color": 0x2f3136
                }

            canal_alertas = bot.get_channel(CANAL_AVENTURAS)
            if canal_alertas:
                nuevo_embed = discord.Embed(
                    title=zona_encontrada["titulo"],
                    description=zona_encontrada["descripcion"],
                    color=zona_encontrada["color"]
                )

                nuevo_embed.add_field(
                    name="📍 Ubicación de la Sala",
                    value=message.channel.mention,
                    inline=False
                )

                nuevo_embed.set_footer(
                    text="Crazy Cats • Auto-Tracker v3"
                )

                # Realiza el ping al rol fuera del embed
                await canal_alertas.send(
                    content=f"🔔 <@&{ROL_AVENTURA}>",
                    embed=nuevo_embed
                )
                print(f"✅ Éxito: Alerta enviada para formato '{zona_encontrada['titulo']}'")
            return

# ==================================================
# EVENTOS DE ESCUCHA DEL BOT
# ==================================================
@bot.event
async def on_ready():
    print(f"✅ Crazy Tracker en línea como: {bot.user}")

@bot.event
async def on_message(message):
    # Ignorar pings provocados por el propio bot
    if message.author == bot.user:
        return

    await verificar_y_enviar_alerta(message)
    await bot.process_commands(message)

@bot.event
async def on_message_edit(before, after):
    if after.author == bot.user:
        return

    # Capta el embed cuando la App lo actualiza con los botones de unirse
    await verificar_y_enviar_alerta(after)

# ==================================================
# EJECUCIÓN INICIAL
# ==================================================
if __name__ == "__main__":
    keep_alive() 
    print("🔥 Conectando con los servicios de Discord...")
    bot.run(TOKEN)