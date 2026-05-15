import discord
from discord.ext import commands
from flask import Flask
from threading import Thread
import os
import logging
import asyncio  # 🌟 ¡Agregado para manejar los tiempos del juego!
import random   # 🌟 ¡Agregado para la aleatoriedad de las plataformas!

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

# 🌟 TU NUEVO ID: Reemplaza este número por el ID real de tu rol de Staff
ROL_STAFF_JUEGO = 937028989854298172

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
        "aventura: magma": {
            "titulo": "🌋 ¡SALA DE MAGMA DETECTADA!",
            "descripcion": "🔥 El calor aumenta, ¡prepara tus mascotas y únete antes de que despegue!",
            "color": 0xFF5500
        },
        "tierras remotas": {
            "titulo": "🏝 ¡SALA DE TIERRAS REMOTAS DETECTADA!",
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
    await bot.process_commands(message) # 🌟 ¡Súper clave para procesar tus comandos!

@bot.event
async def on_message_edit(before, after):
    if after.author == bot.user:
        return

    # Capta el embed cuando la App lo actualiza con los botones de unirse
    await verificar_y_enviar_alerta(after)


# ==================================================
# 🌟 MINIJUEGO: PLATAFORMAS DINÁMICAS (CON SISTEMA ANTITRAMPAS) 🌟
# ==================================================
PLATAFORMAS = {
    "💙": "Cielos (Azul)",
    "❤️": "Fuego (Roja)",
    "💛": "Júpiter (Amarilla)",
    "💗": "Amor (Rosa)"
}

@bot.command()
@commands.has_any_role(ROL_STAFF_JUEGO) # 🔒 Candado estricto por ID de rol
async def plataformas(ctx):
    """Juego de plataformas infinito, antitrampas y hasta que quede un ganador"""
    
    # --- FASE 1: REGISTRO DE PILOTOS ---
    embed_registro = discord.Embed(
        title="🌌 • ¡Plataformas al Ataque!",
        description=(
            "**¡Llegó el momento de escoger!**\n\n"
            "Por favor **Reacciona con ✨** para participar en este emocionante desafío galáctico.\n"
            "Soportamos un máximo de **100 pilotos**.\n"
            "Tienes **20 segundos** para unirte."
        ),
        color=0x9B59B6
    )
    embed_registro.set_footer(text=f"🌙 {ctx.guild.name} • Preparación Estelar")
    
    msg_registro = await ctx.send(embed=embed_registro)
    await msg_registro.add_reaction("✨")
    await asyncio.sleep(20)
    
    # Recuento forzado de reacciones (hasta 100 usuarios)
    msg_registro = await ctx.channel.fetch_message(msg_registro.id)
    pilotos = []
    for reaction in msg_registro.reactions:
        if str(reaction.emoji) == "✨":
            usuarios = [user async for user in reaction.users(limit=100)]
            pilotos = [u for u in usuarios if not u.bot]
            break

    if not pilotos:
        await ctx.send("❌ El juego se canceló porque no se unió ningún piloto.")
        return

    if len(pilotos) > 100:
        pilotos = pilotos[:100]

    ronda_actual = 1
    await ctx.send(f"🚀 **¡Inscripciones cerradas!** Se han detectado **{len(pilotos)}** pilotos en la órbita. ¡El torneo continuará hasta que solo quede un ganador!")
    await asyncio.sleep(3)

    # --- BUCLE PRINCIPAL (RONDAS INFINITAS) ---
    while len(pilotos) > 1:
        
        # 1. Mostrar quiénes siguen con vida en esta ronda
        lista_nombres = "\n".join([f"• {p.mention}" for p in pilotos])
        embed_pilotos = discord.Embed(
            title=f"🌌 • Lista de Pilotos - Ronda {ronda_actual}",
            description=f"**Pilotos en juego ({len(pilotos)}):**\n{lista_nombres}",
            color=0x34495E
        )
        embed_pilotos.set_footer(text=f"🌙 {ctx.guild.name}")
        await ctx.send(embed=embed_pilotos)
        await asyncio.sleep(4)

        # 2. Fase de Selección de Plataforma
        embed_eleccion = discord.Embed(
            title=f"🌌 • Plataformas - Ronda {ronda_actual}",
            description=(
                "⏳ **¡Tiempo para elegir!**\n"
                "Selecciona tu plataforma reaccionando abajo.\n"
                "La plataforma se va a caer en: **15 segundos**.\n\n"
                "💙 • Cielos\n"
                "❤️ • Fuego\n"
                "💛 • Júpiter\n"
                "💗 • Amor"
            ),
            color=0x3498DB
        )
        embed_eleccion.set_footer(text=f"🌙 {ctx.guild.name} • ¡A correr!")
        
        msg_eleccion = await ctx.send(embed=embed_eleccion)
        for emoji in PLATAFORMAS.keys():
            await msg_eleccion.add_reaction(emoji)
            
        await asyncio.sleep(15)
        
        # 3. Conteo de los votos con ANTITRAMPAS
        msg_eleccion = await ctx.channel.fetch_message(msg_eleccion.id)
        elecciones = {p: None for p in pilotos}
        
        for reaction in msg_eleccion.reactions:
            emoji_str = str(reaction.emoji)
            if emoji_str in PLATAFORMAS:
                usuarios_en_emoji = [user async for user in reaction.users(limit=100)]
                for u in usuarios_en_emoji:
                    if u in elecciones:
                        # 🌟 ANTITRAMPAS: Solo le asigna plataforma si aún no ha elegido ninguna.
                        # Si ya tiene una guardada (no es None), ignora cualquier otro emoji secundario.
                        if elecciones[u] is None:
                            elecciones[u] = emoji_str

        # 4. El Colapso: Elegir qué plataforma explota al azar
        emoji_colapsado = random.choice(list(PLATAFORMAS.keys()))
        nombre_colapsado = PLATAFORMAS[emoji_colapsado]
        
        eliminados = []
        sobrevivientes = []
        
        for piloto, em in elecciones.items():
            if em == emoji_colapsado or em is None:
                eliminados.append(piloto)
            else:
                sobrevivientes.append(piloto)

        # 5. Desplegar los resultados de la ronda
        txt_elim = "\n".join([p.mention for p in eliminados]) if eliminados else "*¡Nadie cayó esta vez!*"
        txt_sob = "\n".join([p.mention for p in sobrevivientes]) if sobrevivientes else "*Nadie...*"

        embed_res = discord.Embed(
            title=f"🌌 • 🔥 ¡RONDA {ronda_actual} - COLAPSO CÓSMICO!",
            description=f"La plataforma {emoji_colapsado} **{nombre_colapsado}** ha colapsado y caído al vacío estelar.",
            color=0xE74C3C
        )
        embed_res.add_field(name="🚀 ELIMINADOS", value=f"💥 {txt_elim}", inline=False)
        embed_res.add_field(name="✨ SOBREVIVEN", value=txt_sob, inline=False)
        embed_res.set_footer(text=f"🌙 {ctx.guild.name} • Estado de la órbita")
        await ctx.send(embed=embed_res)
        
        # Guardar sobrevivientes para el siguiente ciclo e incrementar ronda
        pilotos = sobrevivientes
        ronda_actual += 1
        await asyncio.sleep(5)

    # --- FASE FINAL: DETERMINAR AL GANADOR DEFINITIVO ---
    if len(pilotos) == 1:
        await ctx.send(f"👑 **¡TENEMOS UN GANADOR CÓSMICO!** Felicitaciones {pilotos.mention} por sobrevivir a todas las plataformas y ganar el desafío.")
    else:
        await ctx.send("💀 **Colapso Absoluto:** Todos los pilotos cayeron al vacío en la última ronda. No quedó nadie vivo para reclamar la victoria.")

# 🛑 CONTROLADOR DE ERRORES
@plataformas.error
async def plataformas_error(ctx, error):
    if isinstance(error, commands.MissingAnyRole):
        await ctx.send(f"❌ {ctx.author.mention}, **¡Acceso Denegado!** Lo siento, pero solo los miembros del Staff autorizados pueden iniciar el torneo de plataformas.")
# ==================================================
# EJECUCIÓN INICIAL
# ==================================================
if __name__ == "__main__":
    keep_alive() 
    print("🔥 Conectando con los servicios de Discord...")
    bot.run(TOKEN)