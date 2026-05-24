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

bot = commands.Bot(command_prefix="D", intents=intents)

# -------- CONFIGURACIÓN DE IDs DE TU SERVIDOR --------
CANAL_AVENTURAS = 1436358970284572723  # Canal donde el bot enviará el ping
ROL_AVENTURA = 1436361900215500870     # Rol a etiquetar
CANAL_DETECCION = 1436358970284572723  # Canal exclusivo donde juega Nekotina

# ID DE NEKOTINA (Cambia este ID si usas la versión App global o el Bot clásico)
NEKOTINA_ID = 429457053791158281  

# 🌟 TU NUEVO ID: Reemplaza este número por el ID real de tu rol de Staff
ROL_STAFF_JUEGO = 937028989854298172
# Reemplaza estos números largos por los IDs REALES de tu servidor
ID_ROL_STAFF = 937028989854298172        # ID de tu rol de Staff
ID_ROL_PARTICIPANTE = 1481390471153717319 # ID del rol Mishi participante

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
            "titulo": "🌋 ¡SALA DEL INFIERNO DETECTADA XD!",
            "descripcion": "🔥 El calor aumenta, ¡prepara tus mascotas y únete para ir al infierno!",
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
# 🌟 MINIJUEGO: PLATAFORMAS DINÁMICAS (1 MIN REGISTRO + 15 SEG ELECCIÓN) 🌟
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
    
    # Guardamos el canal exacto para asegurar que los mensajes finales se envíen ahí sí o sí
    canal_juego = ctx.channel
    
    # --- FASE 1: REGISTRO DE PILOTOS (1 MINUTO) ---
    embed_registro = discord.Embed(
        title="🌌 • ¡Plataformas al Ataque!",
        description=(
            "**¡Llegó el momento de escoger!**\n\n"
            "Por favor **Reacciona con ✨** para participar en este emocionante desafío galáctico.\n"
            "Soportamos un máximo de **100 pilotos**.\n"
            "Tienes **1 MINUTO** para unirte." # 🌟 Aviso de 1 minuto
        ),
        color=0x9B59B6
    )
    embed_registro.set_footer(text=f"🌙 {ctx.guild.name} • Preparación Estelar")
    
    msg_registro = await canal_juego.send(embed=embed_registro)
    await msg_registro.add_reaction("✨")
    
    # 🌟 NUEVO CAMBIO: Espera 60 segundos completos para que todos se unan
    await asyncio.sleep(60)
    
    # Recuento forzado de reacciones (hasta 100 usuarios)
    msg_registro = await canal_juego.fetch_message(msg_registro.id)
    pilotos = []
    for reaction in msg_registro.reactions:
        if str(reaction.emoji) == "✨":
            usuarios = [user async for user in reaction.users(limit=100)]
            pilotos = [u for u in usuarios if not u.bot]
            break

    if not pilotos:
        await canal_juego.send("❌ El juego se canceló porque no se unió ningún piloto.")
        return

    if len(pilotos) > 100:
        pilotos = pilotos[:100]

    ronda_actual = 1
    await canal_juego.send(f"🚀 **¡Inscripciones cerradas!** Se han detectado **{len(pilotos)}** pilotos en la órbita. ¡El torneo continuará hasta que solo quede un ganador!")
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
        await canal_juego.send(embed=embed_pilotos)
        await asyncio.sleep(4)

        # 2. Fase de Selección de Plataforma (15 SEGUNDOS)
        embed_eleccion = discord.Embed(
            title=f"🌌 • Plataformas - Ronda {ronda_actual}",
            description=(
                "⏳ **¡Tiempo para elegir!**\n"
                "Selecciona tu plataforma reaccionando abajo.\n"
                "La plataforma se va a caer en: **15 segundos**.\n\n" # 🌟 Regresa a 15 segundos rápidos
                "💙 • Cielos\n"
                "❤️ • Fuego\n"
                "💛 • Júpiter\n"
                "💗 • Amor"
            ),
            color=0x3498DB
        )
        embed_eleccion.set_footer(text=f"🌙 {ctx.guild.name} • ¡A correr!")
        
        msg_eleccion = await canal_juego.send(embed=embed_eleccion)
        for emoji in PLATAFORMAS.keys():
            await msg_eleccion.add_reaction(emoji)
            
        # 🌟 REGRESÓ A 15 SEGUNDOS: Acción rápida para correr a la plataforma
        await asyncio.sleep(15)
        
        # 3. Conteo de los votos con ANTITRAMPAS
        msg_eleccion = await canal_juego.fetch_message(msg_eleccion.id)
        elecciones = {p: None for p in pilotos}
        
        for reaction in msg_eleccion.reactions:
            emoji_str = str(reaction.emoji)
            if emoji_str in PLATAFORMAS:
                usuarios_en_emoji = [user async for user in reaction.users(limit=100)]
                for u in usuarios_en_emoji:
                    if u in elecciones:
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
        await canal_juego.send(embed=embed_res)
        
        # Guardar sobrevivientes para el siguiente ciclo e incrementar ronda
        pilotos = sobrevivientes
        ronda_actual += 1
        await asyncio.sleep(5)

    # --- FASE FINAL: DETERMINAR AL GANADOR DEFINITIVO (¡VERSIÓN BLINDADA!) ---
    if len(pilotos) == 1:
        ganador = pilotos  # Sacamos al usuario real de la lista
        
        embed_victoria = discord.Embed(
            title="👑 ¡TENEMOS UN GANADOR CÓSMICO!",
            description=f"Felicitaciones supremas para {ganador.mention}.\n\n¡Ha logrado esquivar todos los colapsos y es el único sobreviviente del torneo de plataformas! 🎉",
            color=0xF1C40F
        )
        
        # 🛡️ OBTENCIÓN ULTRA SEGURA DEL AVATAR (Evita crasheos ocultos)
        try:
            if ganador.avatar:
                embed_victoria.set_thumbnail(url=ganador.avatar.url)
            else:
                embed_victoria.set_thumbnail(url=ganador.default_avatar.url)
        except Exception:
            pass # Si falla el avatar por cualquier cosa, el bot continúa sin trabarse

        embed_victoria.set_footer(text=f"🌙 {ctx.guild.name} • Fin del Desafío")
        
        # Enviamos el mensaje al canal
        await canal_juego.send(content=f"🏆 {ganador.mention}", embed=embed_victoria)
        
    else:
        await canal_juego.send("💀 **Colapso Absoluto:** Todos los pilotos cayeron al vacío en la última ronda. No quedó nadie vivo para reclamar la victoria.")

# 🛑 CONTROLADOR DE ERRORES
@plataformas.error
async def plataformas_error(ctx, error):
    if isinstance(error, commands.MissingAnyRole):
        await ctx.send(f"❌ {ctx.author.mention}, **¡Acceso Denegado!** Lo siento, pero solo los miembros del Staff autorizados pueden iniciar el torneo de plataformas.")



        # ==================================================
# 🛡️ SISTEMA DE MODERACIÓN Y CONTROL POR ID
# ==================================================

# Verificador personalizado para usar el ID del Staff de forma rápida
def es_staff_por_id():
    async def predicate(ctx):
        # Verifica si el autor del mensaje tiene el rol con el ID de Staff
        staff_role = ctx.guild.get_role(ID_ROL_STAFF)
        if staff_role in ctx.author.roles:
            return True
        raise commands.MissingAnyRole([staff_role.name if staff_role else "Staff"])
    return commands.check(predicate)


# --- COMANDO 1: ABRIR PARTICIPANTE ---
@bot.command()
@es_staff_por_id()
async def abrir(ctx, member: discord.Member):
    # Buscamos el rol directamente usando su ID único
    role = ctx.guild.get_role(ID_ROL_PARTICIPANTE)
    
    if not role:
        await ctx.send("❌ No se encontró el rol de participante con el ID configurado.")
        return

    if role in member.roles:
        await ctx.send(f"⚠️ {member.mention} ya tiene acceso abierto.")
        return

    # Le añadimos el rol y reaccionamos con un check verde
    await member.add_roles(role)
    await ctx.message.add_reaction("✅")


# --- COMANDO 2: CERRAR PARTICIPANTE ---
@bot.command()
@es_staff_por_id()
async def cerrar(ctx, member: discord.Member):
    role = ctx.guild.get_role(ID_ROL_PARTICIPANTE)
    
    if not role:
        await ctx.send("❌ No se encontró el rol de participante con el ID configurado.")
        return

    if role not in member.roles:
        await ctx.send(f"⚠️ {member.mention} no tenía el acceso abierto.")
        return

    # Le quitamos el rol y reaccionamos con una cruz roja
    await member.remove_roles(role)
    await ctx.message.add_reaction("❌")


# --- COMANDO 3: PURGAR MENSAJES (CLEAR) ---
@bot.command()
@es_staff_por_id()
async def clear(ctx, amount: int):
    await ctx.channel.purge(limit=amount + 1)
    
    msg = await ctx.send(f"✅ ¡Se han limpiado {amount} mensajes!")
    await msg.add_reaction("✅")
    await asyncio.sleep(3)
    await msg.delete()


# --- COMANDO 4: EXPULSAR (KICK) ---
@bot.command()
@es_staff_por_id()
async def kick(ctx, member: discord.Member, *, reason="No especificada"):
    await member.kick(reason=reason)
    await ctx.message.add_reaction("✅")
    await ctx.send(f"👢 **{member.display_name}** fue expulsado del servidor. Razón: *{reason}*")


# --- COMANDO 5: BANEAR (BAN) ---
@bot.command()
@es_staff_por_id()
async def ban(ctx, member: discord.Member, *, reason="No especificada"):
    await member.ban(reason=reason)
    await ctx.message.add_reaction("✅")
    await ctx.send(f"🔨 **{member.display_name}** fue baneado permanentemente. Razón: *{reason}*")


# ==================================================
# 🚨 GESTOR UNIVERSAL DE ERRORES (ACCESO DENEGADO)
# ==================================================
@abrir.error
@cerrar.error
@clear.error
@kick.error
@ban.error
async def moderacion_errors(ctx, error):
    if isinstance(error, commands.CheckFailure) or isinstance(error, commands.MissingAnyRole) or isinstance(error, commands.MissingPermissions):
        embed_error = discord.Embed(
            title="🚫 • Acceso Denegado",
            description=f"Lo siento {ctx.author.mention}, pero no tienes los permisos o rangos de **Staff** necesarios para utilizar este comando.",
            color=0xE74C3C
        )
        embed_error.set_footer(text=f"Crazy Cats Security • {ctx.guild.name}")
        await ctx.send(embed=embed_error)

        # --- COMANDO: LISTA DE COMANDOS OFICIALES ---
@bot.command()
async def comandos(ctx):
    embed = discord.Embed(
        title="🐾 • GUÍA DE COMANDOS DE CRAZY CATS",
        description=(
            "¡Hola! Aquí tienes la lista oficial de comandos disponibles. "
            "Recuerda que mi prefijo actual es **`D`**.\n\n"
            "---"
        ),
        color=0xFFB6C1  # Color rosa estético 🌸
    )
    
    # Sección de Dinámicas
    embed.add_field(
        name="🔒 1. CONTROL DE DINÁMICAS Y APERTURA BABEL (Solo Staff)",
        value=(
            "`Dabrir @usuario` -> Da el rol de participante para permitirle hablar.\n"
            "`Dcerrar @usuario` -> Quita el rol de participante al terminar."
        ),
        inline=False
    )
    
    # Sección de Moderación
    embed.add_field(
        name="🛡️ 2. MODERACIÓN Y SEGURIDAD (Solo Staff)",
        value=(
            "`Dclear [cantidad]` -> Borra mensajes en masa de forma limpia.\n"
            "`Dkick @usuario [razón]` -> Expulsa a un miembro del servidor.\n"
            "`Dban @usuario [razón]` -> Banea permanentemente a un usuario."
        ),
        inline=False
    )
    
    # Sección de Entretenimiento
    embed.add_field(
        name="🎮 3. MINIJUEGOS COMPLETOS",
        value=(

            "**Torneo Espacial (Solo Staff inicia):**\n"
            "• `Dplataformas` -> Inicia el juego de supervivencia extrema por rondas."
        ),
        inline=False
    )
    
    # Detalles visuales
    embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/112233445566778899.png") # Si tienes un emoji de patita en tu server, puedes poner su link aquí
    embed.set_footer(text=f"🐾 {ctx.guild.name} • Creado con amor para la comunidad")
    
    await ctx.send(embed=embed)

    # ==================================================
# 🪙 CONFIGURACIÓN DE SUBASTAS: LAS 10 LISTAS
# ==================================================
ID_ROL_SUBASTAS = 1061055717429219469  # ID de tu rol de subastas (@Subastas)
ID_CANAL_PAGO = 1422336904308719667    # ID de tu canal de pagos o reclamos

# Modifica los datos de cada lista aquí adentro antes del evento:
SUBASTAS_DATA = {
    1: {"item": "🎒 Shiny Congelado x110", "dueno": "<@753471584500580365>", "precio_inicial": "emp", "imagen": "https://i.imgur.com/Ejemplo1.png"},
    2: {"item": "👑 Manzana Corrompida x20", "dueno": "<@1454737746152128698>", "precio_inicial": "emp", "imagen": ""},
    3: {"item": "🐱 Huevo de Laplace y Solace", "dueno": "<@806387649245872139>", "precio_inicial": "5 emp", "imagen": ""},
    4: {"item": "📦 Canastita III y 50 loot box", "dueno": "<@1071566219783716904>", "precio_inicial": "5 emp", "imagen": ""},
    5: {"item": "💎 Canastita IIi y 15 Picas Shiva", "dueno": "<@1071566219783716904>", "precio_inicial": "5 emp", "imagen": ""},
    6: {"item": "🎫 Calavera Pirata x3", "dueno": "<@1012552938520060005>", "precio_inicial": "5 emp", "imagen": ""},
    7: {"item": "⚔️ Huevo de Santa Slime y Canastita III", "dueno": "<@1058990006930259999>", "precio_inicial": "5 emp", "imagen": ""},
    8: {"item": "🍏 Lingote de Magmaria", "dueno": "<@1431792426435088557>", "precio_inicial": "5 emp", "imagen": ""},
    9: {"item": "⚡ Haste Scroll x115", "dueno": "<@837765625656508447>", "precio_inicial": "emp", "imagen": ""},
    10: {"item": "🔥 Pez Shiny x105", "dueno": "<@1477848205570867244>", "precio_inicial": "emp", "imagen": ""}
}

# Variables de control de memoria interna
subasta_activa = False
item_en_subasta = ""
dueno_del_item = ""
ultima_puja = 0
ultimo_pujador = None

import asyncio

# --- FUNCIÓN INTERNA: REGISTRAR E INICIAR UNA LISTA ESPECÍFICA ---
async def iniciar_subasta_lista(ctx, numero_lista: int):
    global subasta_activa, ultima_puja, ultimo_pujador, item_en_subasta, dueno_del_item
    
    datos = SUBASTAS_DATA[numero_lista]
    
    subasta_activa = True
    item_en_subasta = datos["item"]
    dueno_del_item = datos["dueno"]
    ultima_puja = datos["precio_inicial"]
    ultimo_pujador = None
    
    rol_subastas = ctx.guild.get_role(ID_ROL_SUBASTAS)
    ping = rol_subastas.mention if rol_subastas else "@Subastas"
    
    embed = discord.Embed(
        title=f"🔨 • ¡NUEVA SUBASTA INICIADA (Lista {numero_lista})!",
        description=(
            f"**Ítem:** {datos['item']}\n"
            f"**Dueño:** {datos['dueno']}\n"
            f"**Precio Inicial:** `{datos['precio_inicial']}`\n\n" # <-- ¡Corregido aquí! Ya sin el ":,"
            f"▶️ Toda la comunidad puede usar **`Dpujar [cantidad]`** para mejorar la oferta."
        ),
        color=0x9B59B6
    )
    if datos["imagen"]:
        embed.set_thumbnail(url=datos["imagen"])
    embed.set_footer(text=f"Crazy Cats Auctions • Oferta de apertura: {ultima_puja}")
    
    await ctx.send(content=ping, embed=embed)

# --- CREACIÓN AUTOMÁTICA DE COMANDOS: Dlista1 hasta Dlista10 (SOLO STAFF) ---
def crear_comando_lista(num):
    @bot.command(name=f"lista{num}")
    @es_staff_por_id()
    async def _lista(ctx):
        await iniciar_subasta_lista(ctx, num)
    return _lista

# Registramos los 10 comandos en el bot de golpe
for i in range(1, 11):
    crear_comando_lista(i)


# --- COMANDO: PUJAR (¡REGISTRA AUTOMÁTICAMENTE AL JUGADOR!) ---
@bot.command(name="pujar")
async def pujar(ctx, *, oferta_texto: str):
    global subasta_activa, ultima_puja, ultimo_pujador
    
    if not subasta_activa:
        await ctx.send(f"❌ {ctx.author.mention}, no hay ninguna subasta corriendo en este momento.", delete_after=5)
        return

    # Guardamos tanto el texto de la oferta como al usuario que la hizo
    ultima_puja = oferta_texto
    ultimo_pujador = ctx.author

    embed_puja = discord.Embed(
        title="💰 • ¡NUEVA PUJA MÁS ALTA!",
        description=f"**{ctx.author.mention}** ofrece **`{oferta_texto}`** por el ítem.",
        color=0x2ECC71
    )
    embed_puja.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
    embed_puja.set_image(url="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExM3V6Ym94ZnM3N3Y0b3E4ZXN4ZHY4Y3ZpZ3B3dzBwYm9pZnZidSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3orif2v1B99t8E1SgM/giphy.gif")
    embed_puja.set_footer(text="¡La oferta sigue subiendo! ¿Alguien da más?")

    await ctx.send(embed=embed_puja)

# --- COMANDO: CONTADOR EDITABLE EN TIEMPO REAL (SOLO STAFF) ---
@bot.command(name="contar")
@es_staff_por_id()
async def contar(ctx):
    if not subasta_activa:
        await ctx.send("❌ No hay una subasta activa para cronometrar.")
        return

    mensaje_cronometro = await ctx.send("⏱️ **Iniciando cuenta regresiva de la subasta...**")
    
    for tiempo in range(12, 0, -1):
        if tiempo > 5:
            await mensaje_cronometro.edit(content=f"⏳ **¡La subasta se va a cerrar! Quedan: {tiempo} segundos...**")
        else:
            await mensaje_cronometro.edit(content=f"🚨 **¡ÚLTIMOS SEGUNDOS! Quedan: {tiempo} segundos...**")
        await asyncio.sleep(1)
        
    await mensaje_cronometro.edit(content="🔨 **¡TIEMPO AGOTADO! La subasta se ha cerrado oficialmente.**")


# --- COMANDO: DECLARAR GANADOR AUTOMÁTICO (¡YA NO PIDES USER!) ---
@bot.command(name="pago")
@es_staff_por_id()
async def pago(ctx):
    global subasta_activa, ultima_puja, ultimo_pujador, item_en_subasta, dueno_del_item
    
    if not subasta_activa:
        await ctx.send("❌ No hay una subasta activa para cerrar con pago.")
        return
        
    # 🚨 Validación de seguridad por si nadie llegó a pujar durante la lista
    if ultimo_pujador is None:
        await ctx.send("⚠️ No se puede cerrar la subasta porque **nadie ha realizado ninguna puja** todavía.")
        return
        
    canal_pago = ctx.guild.get_channel(ID_CANAL_PAGO)
    mencion_canal = canal_pago.mention if canal_pago else "#canal-de-pagos"
    
    embed_ganador = discord.Embed(
        title="🎉 🏆 ¡SUBASTA FINALIZADA COMTEMPORÁNEA! 🏆 🎉",
        description=(
            f"¡Felicidades {ultimo_pujador.mention} por haber ganado la subasta!\n\n"
            f"📦 **Ítem ganado:** {item_en_subasta}\n"
            f"💵 **Favor de pagar:** `{ultima_puja}`\n"
            f"👤 **A favor de:** {dueno_del_item} (Dueño original)\n" # <-- Formato corregido para menciones limpias
            f"📍 **Canal de transferencia:** {mencion_canal}"
        ),
        color=0xF1C40F
    )
    if ultimo_pujador.avatar:
        embed_ganador.set_thumbnail(url=ultimo_pujador.avatar.url)
    embed_ganador.set_footer(text=f"Crazy Cats Auctions • ¡Gracias por comerciar con nosotros!")
    
    subasta_activa = False  # Apagamos la subasta para dejar todo listo para la siguiente lista
    await ctx.send(embed=embed_ganador)

   # --- COMANDO: CARTELERA CON PING Y EMOJIS ANIMADOS (SOLO STAFF) ---
@bot.command(name="subastas")
@es_staff_por_id()
async def subastas(ctx):
    try:
        await ctx.message.delete()
    except discord.Forbidden:
        pass

    # 🔔 OBTENER EL ROL PARA EL PING
    rol_subastas = ctx.guild.get_role(ID_ROL_SUBASTAS)
    ping_texto = rol_subastas.mention if rol_subastas else "@Subastas"

    # EMOJIS ANIMADOS (Reemplaza con tus IDs reales usando \:emoji:)
    emoji_titulo = "<a:cc_moneyy:1039727783766671411>" 
    emoji_flecha = "<a:emoji_358:1457417225920315544>"  

    embed = discord.Embed(
        title=f"{emoji_titulo} • ¡CARTELERA OFICIAL DE SUBASTAS! • {emoji_titulo}",
        description=(
            "¡Atención comunidad! Los motores ya están calientes. 🔥\n"
            "Aquí tienen la lista completa de los ítems que se disputarán hoy junto a sus dueños.\n\n"
            "⚠️ *Los precios iniciales son secretos hasta que el Staff abra cada lista con `Dlista`.* \n"
            "---"
        ),
        color=0xE67E22
    )

    for num, datos in SUBASTAS_DATA.items():
        item_nombre = datos["item"] if datos["item"] else "Por anunciar..."
        dueno_nombre = datos["dueno"] if datos["dueno"] else "Anónimo"
        
        embed.add_field(
            name=f"🛑 Lista #{num}",
            value=f"{emoji_flecha} **Ítem:** {item_nombre}\n👤 **Dueño:** {dueno_nombre}",
            inline=False
        )

    embed.set_footer(text=f"🐾 {ctx.guild.name} • ¡Preparen sus billeteras!")
    embed.set_image(url="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExM3V6Ym94ZnM3N3Y0b3E4ZXN4ZHY4Y3ZpZ3B3dzBwYm9pZnZidSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/l0HlVJpG6N9YshF8k/giphy.gif")

    # Envía el contenido del ping primero y el embed pegado abajo
    await ctx.send(content=ping_texto, embed=embed)
# ==================================================
# EJECUCIÓN INICIAL
# ==================================================
if __name__ == "__main__":
    keep_alive() 
    print("🔥 Conectando con los servicios de Discord...")
    bot.run(TOKEN)