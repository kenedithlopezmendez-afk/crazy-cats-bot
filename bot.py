import discord
from discord.ext import commands, tasks
from flask import Flask
from threading import Thread
import os
import logging
import asyncio
import random
from datetime import datetime, timedelta
import sqlite3

# Configuración de logs básica para ver movimientos en Render
logging.basicConfig(level=logging.INFO)

# ==========================================
# 🌐 FLASK / KEEP ALIVE (Para evitar el apagado en Render)
# ==========================================
app = Flask(__name__)

@app.route("/")
def home():
    return "¡El bot de Crazy Cats está activo y funcionando! 🐾"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()


# Configuración del Bot de Discord
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="?", intents=intents)
TOKEN = os.environ.get("TOKEN")

# 🌟 TU NUEVO ID: Reemplaza este número por el ID real de tu rol de Staff
ROL_STAFF_JUEGO = 937028989854298172
# Reemplaza estos números largos por los IDs REALES de tu servidor
ID_ROL_STAFF = 937028989854298172        # ID de tu rol de Staff
ID_ROL_PARTICIPANTE = 1481390471153717319 # ID del rol Mishi participante

# Variable global para prevenir duplicados por edición o doble evento
ultimo_aviso_tiempo = 0


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
    """Limpia una cantidad específica de mensajes del canal"""
    await ctx.channel.purge(limit=amount + 1)
    
    msg = await ctx.send(f"✅ ¡Se han limpiado {amount} mensajes!")
    await msg.add_reaction("✅")
    await asyncio.sleep(3)
    await msg.delete()


# --- COMANDO 4: EXPULSAR (KICK) ---
@bot.command()
@es_staff_por_id()
async def kick(ctx, member: discord.Member, *, reason="No especificada"):
    """Expulsa a un miembro del servidor"""
    await member.kick(reason=reason)
    await ctx.message.add_reaction("✅")
    await ctx.send(f"👢 **{member.display_name}** fue expulsado del servidor. Razón: *{reason}*")


# --- COMANDO 5: BANEAR (BAN) ---
@bot.command()
@es_staff_por_id()
async def ban(ctx, member: discord.Member, *, reason="No especificada"):
    """Banea permanentemente a un miembro del servidor"""
    await member.ban(reason=reason)
    await ctx.message.add_reaction("✅")
    await ctx.send(f"🔨 **{member.display_name}** fue baneado permanentemente. Razón: *{reason}*")


# --- COMANDO: SILENCIAR USUARIO (MUTE / TIMEOUT) ---
@bot.command(name="mute", aliases=["silenciar", "timeout"])
@es_staff_por_id()  # Candado de seguridad para Staff
async def mute(ctx, miembro: discord.Member = None, tiempo: str = None, *, razon: str = "No especificada"):
    """Silencia a un usuario usando el Timeout nativo de Discord (Ej: ?mute @User 10m Razón)"""
    
    if not miembro or not tiempo:
        await ctx.send("⚠️ **Uso correcto:** `?mute @usuario <tiempo><m/h/d> [razón]`\n*Ejemplo:* `?mute @mishi 10m Comportamiento indebido`", delete_after=10)
        return

    # Verificar que el Staff no intente automutearse o mutear al bot
    if miembro == ctx.author or miembro.bot:
        await ctx.send("❌ No puedes silenciar a este usuario.", delete_after=5)
        return

    # Convertir el tiempo (m = minutos, h = horas, d = días)
    unidad = tiempo[-1].lower()
    try:
        cantidad = int(tiempo[:-1])
    except ValueError:
        await ctx.send("⚠️ El formato de tiempo es inválido. Usa números seguidos de `m` (minutos), `h` (horas) o `d` (días).", delete_after=7)
        return

    # Calcular duración usando timedelta limpio
    if unidad == "m":
        duracion = timedelta(minutes=cantidad)
        tiempo_texto = f"{cantidad} Minuto(s)"
    elif unidad == "h":
        duracion = timedelta(hours=cantidad)
        tiempo_texto = f"{cantidad} Hora(s)"
    elif unidad == "d":
        duracion = timedelta(days=cantidad)
        tiempo_texto = f"{cantidad} Día(s)"
    else:
        await ctx.send("⚠️ Unidad de tiempo desconocida. Usa `m`, `h` o `d`.", delete_after=7)
        return

    # Límite máximo de Discord para un Timeout es de 28 días
    if duracion > timedelta(days=28):
        await ctx.send("❌ Discord no permite aislar a un usuario por más de 28 días.", delete_after=5)
        return

    # 🤫 APLICAR TIMEOUT
    try:
        await miembro.timeout(duracion, reason=razon)
    except discord.Forbidden:
        await ctx.send("❌ No tengo permisos suficientes para silenciar a este miembro (puede que tenga un rol más alto que yo).", delete_after=5)
        return

    # 📥 1. ENVIAR MD AL INFRACTOR (Aviso privado)
    try:
        embed_md = discord.Embed(
            title="🛑 • HAS SIDO SILENCIADO • 🛑",
            description=f"Has recibido una sanción temporal en **{ctx.guild.name}**.",
            color=0xE74C3C,
            timestamp=discord.utils.utcnow()
        )
        embed_md.add_field(name="⏳ Duración:", value=tiempo_texto, inline=True)
        embed_md.add_field(name="💬 Razón:", value=razon, inline=False)
        embed_md.set_footer(text="Por favor, cumple la sanción y respeta las normas.")
        await miembro.send(embed=embed_md)
    except discord.Forbidden:
        pass  # Si el usuario tiene los MD cerrados, el bot continúa sin crashar

    # 📝 2. ENVIAR AVISO PÚBLICO EN EL CANAL (Embed unificado y estético)
    embed_canal = discord.Embed(
        title="💥 • USUARIO AISLADO • 💥",
        description=f"El Staff ha aplicado un correctivo temporal en el servidor.",
        color=0xE67E22,
        timestamp=discord.utils.utcnow()
    )
    embed_canal.add_field(name="👤 Infractor:", value=miembro.mention, inline=True)
    embed_canal.add_field(name="⏳ Tiempo:", value=tiempo_texto, inline=True)
    embed_canal.add_field(name="🛡️ Moderador:", value=ctx.author.mention, inline=True)
    embed_canal.add_field(name="📝 Razón:", value=razon, inline=False)
    
    if miembro.avatar:
        embed_canal.set_thumbnail(url=miembro.avatar.url)
    else:
        embed_canal.set_thumbnail(url=miembro.default_avatar.url)

    await ctx.send(embed=embed_canal)

    # Intentar borrar el mensaje del comando para mantener limpio el chat
    try:
        await ctx.message.delete()
    except Exception:
        pass


# --- COMANDO: RETIRAR SILENCIO (UNMUTE) ---
@bot.command(name="unmute", aliases=["desmutear", "untimeout"])
@es_staff_por_id()
async def unmute(ctx, miembro: discord.Member = None, *, razon: str = "Retirado por el Staff"):
    """Remueve el silencio de un usuario antes de tiempo (Ej: ?unmute @User Razón)"""
    
    if not miembro:
        await ctx.send("⚠️ **Uso correcto:** `?unmute @usuario [razón]`", delete_after=10)
        return

    # Quitar el timeout pasándole None como duración
    try:
        await miembro.timeout(None, reason=razon)
    except discord.Forbidden:
        await ctx.send("❌ No tengo permisos para quitarle el silencio a este miembro.", delete_after=5)
        return

    # Aviso estético en el canal
    embed_unmute = discord.Embed(
        title="✨ • SILENCIO RETIRADO • ✨",
        description=f"Se le han devuelto los permisos de habla a {miembro.mention}.",
        color=0x2ECC71,
        timestamp=discord.utils.utcnow()
    )
    embed_unmute.add_field(name="👤 Usuario:", value=miembro.mention, inline=True)
    embed_unmute.add_field(name="🛡️ Moderador:", value=ctx.author.mention, inline=True)
    embed_unmute.add_field(name="📝 Motivo:", value=razon, inline=False)
    
    if miembro.avatar:
        embed_unmute.set_thumbnail(url=miembro.avatar.url)
    else:
        embed_unmute.set_thumbnail(url=miembro.default_avatar.url)

    await ctx.send(embed=embed_unmute)

    try:
        await ctx.message.delete()
    except Exception:
        pass
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
@bot.command(name="comandos", aliases=["ayuda"])
async def comandos(ctx):
    """Muestra la guía completa de comandos oficiales del servidor Crazy Cats"""
    embed = discord.Embed(
        title="🐾 • GUÍA OFICIAL DE COMANDOS DE CRAZY CATS",
        description=(
            "¡Hola! Aquí tienes el directorio completo de comandos disponibles en el servidor.\n"
            "Recuerda que mi prefijo activo es **`?`**.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=0xFFB6C1  # Color rosa estético 🌸
    )
    
    # Sección 1: Dinámicas (Solo Staff)
    embed.add_field(
        name="🔒 1. CONTROL DE DINÁMICAS (Solo Staff)",
        value=(
            "`?abrir @usuario` • Da el rol de participante para permitirle hablar.\n"
            "`?cerrar @usuario` • Quita el rol de participante al terminar."
        ),
        inline=False
    )
    
    # Sección 2: Little Boxes (Privadas de Staff / Usuarios)
    embed.add_field(
        name="📦 2. SISTEMA DE LITTLE BOXES (Privadas / 20 días)",
        value=(
            "`?crearbox [Tipo] \"Nombre\" [@IDs...]` • Crea un hilo privado con permisos y duración exacta.\n"
            "`?extenderbox [ID_Hilo]` • Extiende +20 días la estancia de una box.\n"
            "`?borrarbox [ID_Hilo]` • Elimina a la fuerza un hilo y su registro."
        ),
        inline=False
    )

    # Sección 3: Minijuegos Automáticos y Leaderboard
    embed.add_field(
        name="🎮 3. MINIJUEGOS Y SISTEMA DE PUNTOS",
        value=(
            "💬 **Palabras Clave Automáticas:** ¡Escribe **`mine`**, **`fish`** o **`work`** (con o sin texto extra) en cualquier canal para iniciar un minijuego aleatorio de botones embed y ganar puntos!\n"
            "`?top` • Muestra la tabla de clasificación de jugadores más activos.\n"
            "`?resetlb` • *(Solo Staff)* Reinicia por completo el leaderboard.\n"
            "`?deluserlb @usuario` • *(Solo Staff)* Elimina a un usuario del ranking.\n"
            "`?addpuntos @usuario [cant]` • *(Solo Staff)* Suma o resta puntos manualmente."
        ),
        inline=False
    )

    # Sección 4: Moderación y Seguridad (Solo Staff)
    embed.add_field(
        name="🛡️ 4. MODERACIÓN Y SEGURIDAD (Solo Staff)",
        value=(
            "`?clear [cantidad]` • Borra mensajes en masa de forma limpia.\n"
            "`?kick @usuario [razón]` • Expulsa a un miembro del servidor.\n"
            "`?ban @usuario [razón]` • Banea permanentemente a un usuario.\n"
            "`?mute @usuario [tiempo] [razón]` • Silencia temporalmente (Ej: `10m`, `2h`, `1d`).\n"
            "`?unmute @usuario [razón]` • Remueve el silencio de un miembro sancionado.\n"
            "`?about` • Muestra información del owner y creador del bot."
        ),
        inline=False
    )
    
    # Detalles visuales y pie de página corregido
    if ctx.guild.icon:
        embed.set_thumbnail(url=ctx.guild.icon.url)
        
    embed.set_footer(
        text=f"🐾 Servidor {ctx.guild.name} • Creado con amor para la comunidad", 
        icon_url=ctx.author.display_avatar.url
    )
    embed.timestamp = discord.utils.utcnow()
    
    await ctx.send(embed=embed)
    
    # Intenta borrar el comando del usuario para mantener limpio el chat
    try:
        await ctx.message.delete()
    except Exception:
        pass


# 🤫 CONFIGURACIÓN DEL FILTRO DE MODERACIÓN
ID_CANAL_LOGS = 926513579652431934  # ⬅️ REEMPLAZA CON EL ID DE TU CANAL PRIVADO DE LOGS/STAFF

# Lista de palabras prohibidas (pon las palabras en minúsculas)
PALABRAS_PROHIBIDAS = ["puta", "pendejo", "pendeja", "gay", "puto", "mierda"] 

@bot.event
async def on_message(message):
    # 🚨 Regla de oro: Ignorar los mensajes del propio bot para evitar bucles infinitos
    if message.author.bot:
        return

    # Convertimos todo el texto a minúsculas para que no evadan el filtro usando Mayúsculas
    contenido_minusculas = message.content.lower()

    # Verificar si alguna palabra prohibida está en el mensaje
    if any(palabra in contenido_minusculas for palabra in PALABRAS_PROHIBIDAS):
        
        # 1. Intentar borrar el mensaje ofensivo inmediatamente
        try:
            await message.delete()
        except discord.Forbidden:
            print("⚠️ El bot no tiene permisos de 'Gestionar Mensajes' para borrar la grosería.")
        except discord.NotFound:
            pass

        # 2. Enviar la llamada de atención en el chat (se auto-elimina en 6 segundos)
        llamada_atencion = f"⚠️ {message.author.mention}, **¡Cuida tu lenguaje!** En **Crazy Cats** mantenemos un ambiente sano y respetuoso. Tu mensaje ha sido eliminado."
        await message.channel.send(llamada_atencion, delete_after=6)

        # 3. Enviar el reporte estético (Log) al canal del Staff
        canal_logs = message.guild.get_channel(ID_CANAL_LOGS)
        if canal_logs:
            embed_log = discord.Embed(
                title="🚨 • SISTEMA ANTI-PROFANIDAD • 🚨",
                description=f"Se ha interceptado y eliminado un mensaje con lenguaje inapropiado.",
                color=0xE74C3C, # Rojo de alerta
                timestamp=datetime.datetime.utcnow()
            )
            embed_log.add_field(name="👤 Usuario infractor:", value=f"{message.author.mention} (`{message.author.id}`)", inline=True)
            embed_log.add_field(name="📍 Canal:", value=message.channel.mention, inline=True)
            embed_log.add_field(name="💬 Mensaje original enviado:", value=f"||{message.content}||", inline=False) # Guardado bajo spoiler por si es muy fuerte
            embed_log.set_footer(text="Crazy Cats Security System")
            
            if message.author.avatar:
                embed_log.set_thumbnail(url=message.author.avatar.url)

            await canal_logs.send(embed=embed_log)

    # 💠 IMPORTANTE: Esta línea permite que tus otros comandos normales (como Dplataformas, Duno, etc.) sigan funcionando perfectamente
    await bot.process_commands(message)

   # 👑 CONFIGURACIÓN DE IDS (Reemplaza con los números reales)
ID_CREADOR_BOT = 1445941380315611146   # ⬅️ Tu ID de Discord (Desarrollador)
ID_DUENO_SERVER = 722608146572509214  # ⬅️ La ID del Dueño del Servidor

# --- COMANDO: SOBRE EL BOT Y DUEÑOS ---
@bot.command(name="creador", aliases=["dueño", "about", "desarrollador"])
async def creador(ctx):
    """Muestra la información del creador del bot y del dueño del servidor"""
    
    # 1. Obtener mención del Creador del Bot de forma segura
    try:
        creador_bot = await bot.fetch_user(ID_CREADOR_BOT)
        mencion_creador = f"{creador_bot.mention} (`{creador_bot.name}`)"
    except Exception:
        mencion_creador = f"<@{ID_CREADOR_BOT}>"

    # 2. Obtener mención del Dueño del Servidor de forma segura (evita el AttributeError)
    try:
        dueno_server = await bot.fetch_user(ID_DUENO_SERVER)
        mencion_dueno = f"{dueno_server.mention} (`{dueno_server.name}`)"
    except Exception:
        mencion_dueno = f"<@{ID_DUENO_SERVER}>"

    # 3. Construir el Embed estético
    embed = discord.Embed(
        title="✨ • ¡CONOCE A MIS CREADORES! • ✨",
        description="A continuación te presento a las mentes maestras detrás de esta gran comunidad y de mi programación:",
        color=0x9B59B6
    )
    
    embed.add_field(
        name="🛠️ Creador & Desarrollador del Bot:",
        value=f"{mencion_creador}\n*¡Quien me dio vida y programó todos mis comandos y minijuegos!*",
        inline=False
    )
    
    embed.add_field(
        name="👑 Dueño del Servidor:",
        value=f"{mencion_dueno}\n*La mami de todos {ctx.guild.name}.*",
        inline=False
    )
    
    embed.set_footer(text=f"{ctx.guild.name} Security & Game Bot • Versión 2.0")
    
    if bot.user.avatar:
        embed.set_thumbnail(url=bot.user.avatar.url)
        
    await ctx.send(embed=embed)

# 📌 CONFIGURACIÓN DE ALIANZAS
ID_CANAL_ALIANZAS = 929001649610059846   # ID del canal exclusivo de alianzas
ID_ROL_ALIADOS = 928883841869951058      # ID del rol autorizado para publicar
ID_ROL_PING = 951331413788065802         # ID del rol al que el bot le hará ping (@Alianzas Babel)

URL_BANNER_CRAZY = "https://cdn.discordapp.com/attachments/926875893421461594/1428741419178131497/40_sin_titulo_20251017104529.png?ex=6ab7cd23&is=6ab67ba3&hm=86c126130accb2f90d4a9c4ba40e760ca20b50f6111b592c33c416b514f43276&"

@bot.event
async def on_message(message):
    # 1. Ignorar mensajes enviados por bots
    if message.author.bot:
        return

    # 2. Verificar si el mensaje se envió en el canal correcto
    if message.channel.id == ID_CANAL_ALIANZAS:
        
        # 3. Verificar si el usuario tiene el rol autorizado
        rol_aliado = message.guild.get_role(ID_ROL_ALIADOS)
        if rol_aliado and rol_aliado in message.author.roles:
            
            # 🔍 4. VALIDACIÓN DE PLANTILLA
            # Convertimos el mensaje a minúsculas para evaluar palabras clave de la plantilla
            contenido = message.content.lower()
            
            # Comprobamos que incluya términos típicos de la plantilla (puedes ajustar estas palabras)
            es_plantilla = "babel" in contenido or "link:" in contenido or "discord.com/invite" in contenido or "https://" in contenido
            
            # Si NO cumple con ser una plantilla, el bot ignora el mensaje y no hace nada
            if not es_plantilla:
                await bot.process_commands(message)
                return

            # --- SI ES UNA PLANTILLA, PROCEDE CON EL RESPUESTA Y PING ---
            rol_ping = message.guild.get_role(ID_ROL_PING)
            texto_ping = rol_ping.mention if rol_ping else "@Alianzas Babel"

            # 🖼️ CONSTRUCCIÓN DEL EMBED RESPUESTA
            embed = discord.Embed(
                description="🐾 **¡NUEVO BABEL ABIERTO!** 🐾\n\nQue esperas mishito, disfruta estas 12h de babel.",
                color=0xFF69B4 # Color rosa/purple estético
            )
            
            # Cabecera con info del usuario
            embed.set_author(
                name=f"{message.author.name}", 
                icon_url=message.author.display_avatar.url
            )
            
            # Miniatura e Imagen Grande
            embed.set_thumbnail(url=message.author.display_avatar.url)
            embed.set_image(url=URL_BANNER_CRAZY)
            
            # Pie de página con comando
            embed.set_footer(text="!capply crazy")

            # Responder directamente al mensaje de la plantilla
            await message.reply(content=texto_ping, embed=embed)

    # NO BORRAR: Necesario para que el bot siga procesando comandos
    await bot.process_commands(message)

# 📌 CONFIGURACIÓN DE IDs Y BANNER
ID_CANAL_AVISOS = 1445524571750138007    # Canal donde el bot publicará los Embeds
ID_ROL_AVENTURA = 957855794869710859    # Rol a etiquetar (@Aventureros)
ID_ROL_STAFF = 937028989854298172       # ⚠️ Reemplaza con el ID del rol de Staff

URL_BANNER_LUNA_SANGRE = "https://cdn.discordapp.com/attachments/1477118463943245875/1557111051886002277/Gemini_Generated_Image_4i8sor4i8sor4i8s.jpg?backend=b2&ex=6ac69c2c&is=6ac54aac&hm=c0b3f4a6541a8ad6580cc0c77880c663863d518706bd70cf0e573ef0033c064c&"


# ==================================================
# 1. COMANDO PREVIA: "SE ACERCA LA LUNA" (SIN IMAGEN)
# ==================================================
@bot.command(name="previa", aliases=["lunasin"])
async def aviso_previa_luna(ctx):
    # 1. Borrar el mensaje del comando inmediatamente
    try:
        await ctx.message.delete()
    except Exception:
        pass

    # 2. Verificar rol de Staff
    rol_staff = ctx.guild.get_role(ID_ROL_STAFF)
    if rol_staff not in ctx.author.roles:
        return

    # 3. Obtener canal de destino
    canal_avisos = ctx.guild.get_channel(ID_CANAL_AVISOS)
    if not canal_avisos:
        print("❌ Error: No se encontró el canal de avisos.")
        return

    # Mencionar rol de aventuras
    rol_ping = ctx.guild.get_role(ID_ROL_AVENTURA)
    mencion_rol = rol_ping.mention if rol_ping else f"<@&{ID_ROL_AVENTURA}>"

    # 🕯️ Embed elegante SIN IMAGEN
    embed_previa = discord.Embed(
        title="⏳ • ¡LA LUNA DE SANGRE SE ACERCA! • ⏳",
        description=(
            f"¡Atención {mencion_rol}!\n\n"
            "🕯️ **Se ha detectado la aproximación de la Luna de Sangre.**\n"
            "Preparen sus mascotas y equipos. ¡El evento iniciará muy pronto!"
        ),
        color=0xFF7518  # Naranja Calabaza
    )
    embed_previa.set_footer(text=f"{ctx.guild.name} • Alerta Preventiva")

    await canal_avisos.send(content=f"🔔 {mencion_rol}", embed=embed_previa)
    print(f"✅ Éxito: Comando !previa ejecutado por {ctx.author.name}")


# ==================================================
# 2. COMANDO EVENTO ACTIVO: "LUNA DE SANGRE" (CON IMAGEN)
# ==================================================
@bot.command(name="luna")
async def activar_luna_sangre(ctx):
    # 1. Borrar el mensaje del comando inmediatamente
    try:
        await ctx.message.delete()
    except Exception:
        pass

    # 2. Verificar rol de Staff
    rol_staff = ctx.guild.get_role(ID_ROL_STAFF)
    if rol_staff not in ctx.author.roles:
        return

    # 3. Obtener canal de destino
    canal_avisos = ctx.guild.get_channel(ID_CANAL_AVISOS)
    if not canal_avisos:
        print("❌ Error: No se encontró el canal de avisos.")
        return

    # Mencionar rol de aventuras
    rol_ping = ctx.guild.get_role(ID_ROL_AVENTURA)
    mencion_rol = rol_ping.mention if rol_ping else f"<@&{ID_ROL_AVENTURA}>"

    # 🎃 🖼️ Embed con BANNER E IMAGEN
    embed_activo = discord.Embed(
        title="🎃🔴 • ¡LA LUNA DE SANGRE HA LLEGADO! • 🔴🎃",
        description=(
            f"¡Atención {mencion_rol}!\n\n"
            "🌕🔴 **¡La Luna de Sangre está activa en estos momentos!**\n\n"
            "⚔️ **Bajo la luna carmesí, las aventuras otorgan mayor probabilidad de objetos raros y valiosos.**\n"
            "¡Envíen a sus mascotas a la aventura ahora mismo antes de que desaparezca!"
        ),
        color=0x8B0000  # Rojo Carmesí
    )
    
    # Se añade la imagen
    embed_activo.set_image(url=URL_BANNER_LUNA_SANGRE)
    embed_activo.set_footer(text=f"{ctx.guild.name} • Evento Oficial de Luna de Sangre")

    await canal_avisos.send(content=f"🚨 {mencion_rol}", embed=embed_activo)
    print(f"✅ Éxito: Comando !luna ejecutado por {ctx.author.name}")

# ==================================================
# 📌 CONFIGURACIÓN DE IDS
# ==================================================
ID_CANAL_LITTLE_BOXES = 1419188163376840784  # Canal principal (#little-boxes)
ID_CANAL_LOGS = 1477110955669323899          # Canal de registros / logs
ID_ROL_STAFF = 955211100700426240            # ⚠️ Reemplaza con la ID real del rol "S-Camita"

# ==================================================
# BASE DE DATOS (SQLite)
# ==================================================
conn = sqlite3.connect("little_boxes.db")
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS boxes (
        thread_id INTEGER PRIMARY KEY,
        owner_id INTEGER,
        nombre TEXT,
        tipo TEXT,
        fecha_adquisicion TEXT,
        fecha_expiracion TEXT,
        aviso_enviado INTEGER DEFAULT 0
    )
''')
conn.commit()


# Función auxiliar para verificar si es Staff por ID
def es_staff(ctx):
    rol_staff = ctx.guild.get_role(ID_ROL_STAFF)
    return (rol_staff in ctx.author.roles) or ctx.author.guild_permissions.administrator


# ==================================================
# 📦 1. COMANDO: CREAR BOX (!crearbox)
# ==================================================

@bot.command(name="crearbox")
async def crear_box(ctx, tipo: str, nombre_box: str, *ids_usuarios: str):
    """
    Sintaxis: !crearbox Tipo "Nombre Box" ID_Dueño ID_Acompañante1 ...
    Ejemplo:  !crearbox Duo "Camas₊˚♡" 123456789012345678 987654321098765432
    """
    if not es_staff(ctx):
        return await ctx.send("❌ No tienes permisos para usar este comando.", delete_after=5)

    if not ids_usuarios:
        return await ctx.send("❌ Debes incluir al menos la ID del dueño.\nEjemplo: `!crearbox Mini \"Mi Box\" 1234567890`", delete_after=8)

    # Limpiar y filtrar IDs de usuarios de forma segura
    ids_limpias = []
    for raw_id in ids_usuarios:
        clean_id = raw_id.replace("<@", "").replace(">", "").replace("!", "")
        if clean_id.isdigit():
            ids_limpias.append(int(clean_id))

    if not ids_limpias:
        return await ctx.send("❌ Ninguna de las IDs ingresadas es válida.", delete_after=8)

    if len(ids_limpias) > 10:
        return await ctx.send("⚠️ El límite máximo de participantes es de 10 personas.", delete_after=8)

    canal_principal = ctx.guild.get_channel(ID_CANAL_LITTLE_BOXES)
    canal_logs = ctx.guild.get_channel(ID_CANAL_LOGS)

    if not canal_principal or not canal_logs:
        return await ctx.send("❌ Error crítico: Verifica los IDs de los canales configurados.", delete_after=8)

    # Búsqueda blindada por API (fetch_member)
    miembros_agregados = []
    dueno = None

    for idx, user_id in enumerate(ids_limpias):
        member = ctx.guild.get_member(user_id)
        if not member:
            try:
                member = await ctx.guild.fetch_member(user_id)
            except Exception:
                member = None

        if member:
            miembros_agregados.append(member)
            if idx == 0:
                dueno = member

    if not dueno:
        return await ctx.send("❌ No se pudo encontrar al usuario dueño con la primera ID provista.", delete_after=8)

    # Fechas y Timestamps (20 días exactos)
    ahora = datetime.now()
    expiracion = ahora + timedelta(days=20)

    ts_adquisicion = int(ahora.timestamp())
    ts_expiracion = int(expiracion.timestamp())

    # Crear el Hilo Privado en Discord (Soporta fuentes y emojis con total libertad en el nombre)
    hilo = await canal_principal.create_thread(
        name=f"📦・{nombre_box}",
        type=discord.ChannelType.private_thread,
        invitable=False
    )

    # 🔐 Asegurar adición y permisos de escritura al Dueño y Acompañantes
    for member in miembros_agregados:
        try:
            await hilo.add_user(member)
        except Exception as e:
            print(f"Error al añadir a {member.name} al hilo: {e}")

    # Asegurar que el Staff (S-Camita por ID) también tenga acceso al hilo creado
    rol_staff = ctx.guild.get_role(ID_ROL_STAFF)
    if rol_staff:
        for member in rol_staff.members:
            try:
                await hilo.add_user(member)
            except Exception:
                pass

    # Guardar en Base de Datos SQLite
    cursor.execute(
        "INSERT INTO boxes VALUES (?, ?, ?, ?, ?, ?, 0)",
        (hilo.id, dueno.id, nombre_box, tipo, ahora.isoformat(), expiracion.isoformat())
    )
    conn.commit()

    # Estructurar texto de integrantes
    if len(miembros_agregados) == 1:
        texto_integrantes = f"👤 **Dueño/a:** {dueno.mention}"
    else:
        acompanantes = [m.mention for m in miembros_agregados[1:]]
        texto_integrantes = f"👑 **Dueño/a:** {dueno.mention}\n👥 **Acompañantes ({len(acompanantes)}):**\n" + "\n".join([f"• {acc}" for acc in acompanantes])

    # ✨ EMBED DE BIENVENIDA ESTÉTICO
    embed_bienvenida = discord.Embed(
        title=f"📦 ✨ ¡Bienvenidos a {nombre_box}! ✨ 📦",
        description=(
            f"¡Felicidades! Su **Little Box** ha sido creada y configurada con éxito.\n\n"
            f"─────────────── Por favor lean las pautas ───────────────\n"
            f"{texto_integrantes}\n\n"
            f"🗓️ **Adquisición:** <t:{ts_adquisicion}:F>\n"
            f"⏳ **Vencimiento:** <t:{ts_expiracion}:F> (<t:{ts_expiracion}:R>)\n\n"
            f"📜 **REGLAS DE LA LITTLE BOX:**\n"
            f"• **1.** Respetar los Términos de Servicio y normas generales de Discord y del servidor.\n"
            f"• **2.** Este espacio es privado y de uso exclusivo para los integrantes autorizados.\n"
            f"• **3.** Para renovar su estancia por +20 días, contacten al Staff antes del vencimiento.\n"
            f"• **4.** Al cumplirse el plazo sin renovación, el hilo se eliminará de forma automática."
        ),
        color=0xFFB6C1
    )
    embed_bienvenida.set_thumbnail(url=dueno.display_avatar.url)
    embed_bienvenida.set_footer(text=f"ID de Little Box: {hilo.id} • Servidor {ctx.guild.name}", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)

    menciones_str = " ".join([m.mention for m in miembros_agregados])
    await hilo.send(content=f"👋 ¡Hola {menciones_str}!", embed=embed_bienvenida)

    # ✨ EMBED DE LOG DE CREACIÓN
    embed_log = discord.Embed(
        title="📥 Nueva Little Box Registrada",
        color=0x2ECC71,
        timestamp=datetime.now()
    )
    embed_log.description = (
        f"• **Nombre:** `{nombre_box}`\n"
        f"• **Tipo:** `{tipo}`\n"
        f"• **Dueño/a:** {dueno.name} ({dueno.mention})\n"
        f"• **Total Integrantes:** `{len(miembros_agregados)}`\n"
        f"• **Expiración:** <t:{ts_expiracion}:f> (`en 20 días`)"
    )
    embed_log.set_footer(text=f"ID Hilo: {hilo.id}", icon_url=dueno.display_avatar.url)

    await canal_logs.send(embed=embed_log)

    try:
        await ctx.message.delete()
    except Exception:
        pass


# ==================================================
# 🔄 2. COMANDO: EXTENDER BOX (!extenderbox)
# ==================================================

@bot.command(name="extenderbox")
async def extender_box(ctx, thread_id: int):
    """Sintaxis: !extenderbox ID_DEL_HILO"""
    if not es_staff(ctx):
        return await ctx.send("❌ No tienes permisos para usar este comando.", delete_after=5)

    cursor.execute("SELECT * FROM boxes WHERE thread_id = ?", (thread_id,))
    box = cursor.fetchone()

    if not box:
        return await ctx.send("❌ No se encontró ninguna Little Box registrada con esa ID.", delete_after=6)

    _, owner_id, nombre, tipo, str_adq, str_exp_iso, _ = box

    fecha_exp_actual = datetime.fromisoformat(str_exp_iso)
    nueva_expiracion = fecha_exp_actual + timedelta(days=20)
    ahora = datetime.now()

    cursor.execute(
        "UPDATE boxes SET fecha_expiracion = ?, aviso_enviado = 0 WHERE thread_id = ?",
        (nueva_expiracion.isoformat(), thread_id)
    )
    conn.commit()

    dueno = ctx.guild.get_member(owner_id)
    mencion_dueno = dueno.mention if dueno else f"<@{owner_id}>"
    nombre_dueno = dueno.name if dueno else "Usuario Desconocido"
    avatar_dueno = dueno.display_avatar.url if dueno else bot.user.display_avatar.url

    ts_nueva_exp = int(nueva_expiracion.timestamp())
    canal_logs = ctx.guild.get_channel(ID_CANAL_LOGS)

    embed_log = discord.Embed(
        title="🔄 Little Box Extendida (+20 días)",
        color=0xE91E63,
        timestamp=datetime.now()
    )
    embed_log.description = (
        f"• **Nombre:** `{nombre}`\n"
        f"• **Dueño/a:** {nombre_dueno} ({mencion_dueno})\n"
        f"• **Tipo:** `{tipo}`\n"
        f"• **Nueva Expiración:** `<t:{ts_nueva_exp}:f>` (`<t:{ts_nueva_exp}:R>`)"
    )
    embed_log.set_footer(text=f"ID Hilo: {thread_id}", icon_url=avatar_dueno)

    if canal_logs:
        await canal_logs.send(embed=embed_log)

    try:
        hilo = await bot.fetch_channel(thread_id)
        if isinstance(hilo, discord.Thread):
            embed_aviso_hilo = discord.Embed(
                title="✨ ¡ESTANCIA RENOVADA! ✨",
                description=(
                    f"¡Buenas noticias! El Staff ha extendido el tiempo de esta **Little Box**.\n\n"
                    f"⏳ **Nuevo Vencimiento:** `<t:{ts_nueva_exp}:F>` (`<t:{ts_nueva_exp}:R>`)"
                ),
                color=0x2ECC71
            )
            await hilo.send(embed=embed_aviso_hilo)
    except Exception:
        pass

    try:
        await ctx.message.delete()
    except Exception:
        pass


# ==================================================
# 🗑️ 3. COMANDO: BORRAR BOX (!borrarbox)
# ==================================================

@bot.command(name="borrarbox")
async def borrar_box(ctx, thread_id: int):
    """Sintaxis: !borrarbox ID_DEL_HILO"""
    if not es_staff(ctx):
        return await ctx.send("❌ No tienes permisos para usar este comando.", delete_after=5)

    try:
        hilo = await bot.fetch_channel(thread_id)
        nombre_hilo = hilo.name
        await hilo.delete()
    except Exception:
        nombre_hilo = "Hilo ya inexistente o inaccesible"

    cursor.execute("SELECT owner_id, tipo FROM boxes WHERE thread_id = ?", (thread_id,))
    cursor.fetchone()
    
    cursor.execute("DELETE FROM boxes WHERE thread_id = ?", (thread_id,))
    conn.commit()

    canal_logs = ctx.guild.get_channel(ID_CANAL_LOGS)
    if canal_logs:
        embed_log = discord.Embed(
            title="🗑️ Little Box Eliminada a la Fuerza",
            color=0xE74C3C,
            timestamp=datetime.now()
        )
        embed_log.description = (
            f"• **Hilo:** `{nombre_hilo}`\n"
            f"• **ID del Hilo:** `{thread_id}`\n"
            f"• **Acción ejecutada por:** {ctx.author.mention}"
        )
        await canal_logs.send(embed=embed_log)

    await ctx.send(f"✅ La Little Box con ID `{thread_id}` ha sido eliminada correctamente.", delete_after=6)
    try:
        await ctx.message.delete()
    except Exception:
        pass


# ==================================================
# ⏰ 4. TAREA AUTOMÁTICA EN SEGUNDO PLANO
# ==================================================

@tasks.loop(minutes=30)
async def sistema_gestion_boxes():
    ahora = datetime.now()
    cursor.execute("SELECT * FROM boxes")
    todas_las_boxes = cursor.fetchall()

    canal_logs = bot.get_channel(ID_CANAL_LOGS)

    for box in todas_las_boxes:
        thread_id, owner_id, nombre, tipo, str_adq, str_exp_iso, aviso_enviado = box
        fecha_expiracion = datetime.fromisoformat(str_exp_iso)
        tiempo_restante = fecha_expiracion - ahora
        ts_exp = int(fecha_expiracion.timestamp())

        # 🔔 Recordatorio 24 horas antes
        if timedelta(hours=0) < tiempo_restante <= timedelta(hours=24) and aviso_enviado == 0:
            try:
                hilo = await bot.fetch_channel(thread_id)
                if hilo:
                    dueno = bot.get_user(owner_id)
                    mencion_dueno = dueno.mention if dueno else "Integrantes"

                    embed_recordatorio = discord.Embed(
                        title="⚠️ ¡SU LITTLE BOX ESTÁ A PUNTO DE VENCER!",
                        description=(
                            f"¡Atención {mencion_dueno} y acompañantes!\n\n"
                            f"⏰ Su Little Box **{nombre}** expirará en menos de **24 horas**.\n"
                            f"🗓️ **Cierre programado:** `<t:{ts_exp}:F>` (`<t:{ts_exp}:R>`)\n\n"
                            f"💡 *Si desean conservar su espacio, contacten al Staff para solicitar una renovación.*"
                        ),
                        color=0xF39C12
                    )
                    embed_recordatorio.set_footer(text="Aviso automático de expiración")
                    await hilo.send(content=f"🔔 {mencion_dueno}", embed=embed_recordatorio)

                    cursor.execute("UPDATE boxes SET aviso_enviado = 1 WHERE thread_id = ?", (thread_id,))
                    conn.commit()
            except Exception as e:
                print(f"Error enviando recordatorio: {e}")

        # ❌ Eliminación automática al cumplirse los 20 días
        elif ahora >= fecha_expiracion:
            try:
                hilo = await bot.fetch_channel(thread_id)
                if hilo:
                    await hilo.delete()
            except Exception:
                pass

            if canal_logs:
                dueno = bot.get_user(owner_id)
                m_dueno = dueno.mention if dueno else f"<@{owner_id}>"

                embed_cerrado = discord.Embed(
                    title="🔒 Little Box Cerrada (Expirada)",
                    color=0x7F8C8D,
                    timestamp=datetime.now()
                )
                embed_cerrado.description = (
                    f"• **Nombre:** `{nombre}`\n"
                    f"• **Dueño/a:** {m_dueno}\n"
                    f"• **Razón:** Plazo de 20 días finalizado sin renovación."
                )
                embed_cerrado.set_footer(text=f"ID de Little Box: {thread_id}")
                await canal_logs.send(embed=embed_cerrado)

            cursor.execute("DELETE FROM boxes WHERE thread_id = ?", (thread_id,))
            conn.commit()

@sistema_gestion_boxes.before_loop
async def antes_de_loop():
    await bot.wait_until_ready()
    
# 📌 CONFIGURACIÓN DE IDs
ID_CANAL_ANUNCIOS_ADV = 1436358970284572723  # Canal donde se enviarán los embeds
ID_ROL_HORA_AVENTURA = 1436361900215500870    # ⚠️ REEMPLAZA con la ID del rol "Hora de Aventura"
ID_ROL_PING_ADV = 1436361900215500870         # ID del rol a etiquetar en el aviso (@Adventure)


# Función auxiliar para validar si el usuario tiene el rol por su ID
def tiene_rol_aventura(ctx):
    rol = ctx.guild.get_role(ID_ROL_HORA_AVENTURA)
    return (rol in ctx.author.roles) or ctx.author.guild_permissions.administrator


# ==================================================
# 1. ZONA: MAGMA (Normal y Buff)
# ==================================================

@bot.command(name="magma")
async def aventura_magma(ctx):
    if not tiene_rol_aventura(ctx):
        return await ctx.send("❌ No tienes el rol autorizado para usar este comando.", delete_after=5)

    try:
        await ctx.message.delete()
    except Exception:
        pass

    canal = ctx.guild.get_channel(ID_CANAL_ANUNCIOS_ADV)
    rol_ping = ctx.guild.get_role(ID_ROL_PING_ADV)
    mencion = rol_ping.mention if rol_ping else f"<@&{ID_ROL_PING_ADV}>"

    embed = discord.Embed(
        title="🌋 Sala de Magma Detectada",
        description="¡Prepara tus mascotas y entra en la zona de magma!",
        color=0xE67E22
    )
    embed.add_field(name="🧭 Aventura Disponible", value="¡Zona activa por tiempo limitado!", inline=False)
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1450135217493901322/1560402211794583573/tumblr_pgq1u9I4r91utevtho1_500-3579210553.gif?ex=6ad2954e&is=6ad143ce&hm=e2b61767f681691aac10a0df88fa5be2aea6343c125b7e874b47c0e3e58a1091")
    embed.set_footer(text=f"{ctx.guild.name} • Sistema de Detección")

    await canal.send(content=f"Ping: {mencion}", embed=embed)


@bot.command(name="magmabuff")
async def aventura_magmabuff(ctx):
    if not tiene_rol_aventura(ctx):
        return await ctx.send("❌ No tienes el rol autorizado para usar este comando.", delete_after=5)

    try:
        await ctx.message.delete()
    except Exception:
        pass

    canal = ctx.guild.get_channel(ID_CANAL_ANUNCIOS_ADV)
    rol_ping = ctx.guild.get_role(ID_ROL_PING_ADV)
    mencion = rol_ping.mention if rol_ping else f"<@&{ID_ROL_PING_ADV}>"

    embed = discord.Embed(
        title="🌋🔥 Sala de Magma [BUFF: Mitad de Cooldown]",
        description="¡El buff de velocidad está activo! Entra a la zona de magma con cooldown reducido.",
        color=0xD35400
    )
    embed.add_field(name="🧭 Aventura con Buff Activo", value="¡Aprovecha al máximo la reducción de tiempo!", inline=False)
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1450135217493901322/1560402211794583573/tumblr_pgq1u9I4r91utevtho1_500-3579210553.gif?ex=6ad2954e&is=6ad143ce&hm=e2b61767f681691aac10a0df88fa5be2aea6343c125b7e874b47c0e3e58a1091")
    embed.set_footer(text=f"{ctx.guild.name} • Sistema de Detección con Buff")

    await canal.send(content=f"Ping: {mencion} ⚡ **[BUFF ACTIVO]**", embed=embed)


# ==================================================
# 2. ZONA: TIERRAS REMOTAS (Normal y Buff)
# ==================================================

@bot.command(name="tierras", aliases=["tierrasremotas"])
async def aventura_tierras(ctx):
    if not tiene_rol_aventura(ctx):
        return await ctx.send("❌ No tienes el rol autorizado para usar este comando.", delete_after=5)

    try:
        await ctx.message.delete()
    except Exception:
        pass

    canal = ctx.guild.get_channel(ID_CANAL_ANUNCIOS_ADV)
    rol_ping = ctx.guild.get_role(ID_ROL_PING_ADV)
    mencion = rol_ping.mention if rol_ping else f"<@&{ID_ROL_PING_ADV}>"

    embed = discord.Embed(
        title="🌲 Sala de Tierras Remotas Detectada",
        description="¡Prepara tus mascotas y adéntrate en las profundidades de las tierras remotas!",
        color=0x27AE60
    )
    embed.add_field(name="🧭 Aventura Disponible", value="¡Nuevos horizontes por explorar!", inline=False)
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1450135217493901322/1560403598876090398/paisajes-del-mundo-nature-1482910422.gif?ex=6ad29698&is=6ad14518&hm=f0004a634d4f0ee95d8daa0573b1e0c0cd14e6aaf970552624d55709b666da8c")
    embed.set_footer(text=f"{ctx.guild.name} • Sistema de Detección")

    await canal.send(content=f"Ping: {mencion}", embed=embed)


@bot.command(name="tierrasbuff")
async def aventura_tierrasbuff(ctx):
    if not tiene_rol_aventura(ctx):
        return await ctx.send("❌ No tienes el rol autorizado para usar este comando.", delete_after=5)

    try:
        await ctx.message.delete()
    except Exception:
        pass

    canal = ctx.guild.get_channel(ID_CANAL_ANUNCIOS_ADV)
    rol_ping = ctx.guild.get_role(ID_ROL_PING_ADV)
    mencion = rol_ping.mention if rol_ping else f"<@&{ID_ROL_PING_ADV}>"

    embed = discord.Embed(
        title="🌲⚡ Sala de Tierras Remotas [BUFF: Mitad de Cooldown]",
        description="¡El buff de velocidad está activo en las Tierras Remotas!",
        color=0x229954
    )
    embed.add_field(name="🧭 Aventura con Buff Activo", value="¡Apresúrate antes de que termine el evento!", inline=False)
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1450135217493901322/1560403598876090398/paisajes-del-mundo-nature-1482910422.gif?ex=6ad29698&is=6ad14518&hm=f0004a634d4f0ee95d8daa0573b1e0c0cd14e6aaf970552624d55709b666da8c")
    embed.set_footer(text=f"{ctx.guild.name} • Sistema de Detección con Buff")

    await canal.send(content=f"Ping: {mencion} ⚡ **[BUFF ACTIVO]**", embed=embed)


# ==================================================
# 3. ZONA: CARNAVAL (Normal y Buff)
# ==================================================

@bot.command(name="carnaval")
async def aventura_carnaval(ctx):
    if not tiene_rol_aventura(ctx):
        return await ctx.send("❌ No tienes el rol autorizado para usar este comando.", delete_after=5)

    try:
        await ctx.message.delete()
    except Exception:
        pass

    canal = ctx.guild.get_channel(ID_CANAL_ANUNCIOS_ADV)
    rol_ping = ctx.guild.get_role(ID_ROL_PING_ADV)
    mencion = rol_ping.mention if rol_ping else f"<@&{ID_ROL_PING_ADV}>"

    embed = discord.Embed(
        title="🎪 Sala de Carnaval Detectada",
        description="¡El evento temporal ha comenzado! Prepara tus mascotas y disfruta del carnaval.",
        color=0x9B59B6
    )
    embed.add_field(name="🧭 Aventura Disponible", value="¡Recompensas especiales por tiempo limitado!", inline=False)
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1450135217493901322/1560403994571178074/full-shot-fireworks-1729999030.gif?ex=6ad296f7&is=6ad14577&hm=37cf72f35dc56a53d5094c6b2f9b9df48d1085ecdc6a7a8d23edf28749e27999")
    embed.set_footer(text=f"{ctx.guild.name} • Sistema de Detección Temporal")

    await canal.send(content=f"Ping: {mencion}", embed=embed)


@bot.command(name="carnavalbuff")
async def aventura_carnavalbuff(ctx):
    if not tiene_rol_aventura(ctx):
        return await ctx.send("❌ No tienes el rol autorizado para usar este comando.", delete_after=5)

    try:
        await ctx.message.delete()
    except Exception:
        pass

    canal = ctx.guild.get_channel(ID_CANAL_ANUNCIOS_ADV)
    rol_ping = ctx.guild.get_role(ID_ROL_PING_ADV)
    mencion = rol_ping.mention if rol_ping else f"<@&{ID_ROL_PING_ADV}>"

    embed = discord.Embed(
        title="🎪⚡ Sala de Carnaval [BUFF: Mitad de Cooldown]",
        description="¡El buff de mitad de cooldown está activo para el Carnaval temporal!",
        color=0x8E44AD
    )
    embed.add_field(name="🧭 Aventura con Buff Activo", value="¡Multiplica tus ganancias antes de que finalice!", inline=False)
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1450135217493901322/1560403994571178074/full-shot-fireworks-1729999030.gif?ex=6ad296f7&is=6ad14577&hm=37cf72f35dc56a53d5094c6b2f9b9df48d1085ecdc6a7a8d23edf28749e27999")
    embed.set_footer(text=f"{ctx.guild.name} • Sistema de Detección con Buff")

    await canal.send(content=f"Ping: {mencion} ⚡ **[BUFF ACTIVO]**", embed=embed)


# ==================================================
# 🗄️ BASE DE DATOS (SQLite para Puntos y Leaderboard)
# ==================================================
conn = sqlite3.connect("minigames.db")
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS minigames_scores (
        user_id INTEGER PRIMARY KEY,
        points INTEGER DEFAULT 0
    )
''')
conn.commit()


# Función auxiliar para sumar puntos
async def sumar_punto(user_id):
    cursor.execute("SELECT points FROM minigames_scores WHERE user_id = ?", (user_id,))
    resultado = cursor.fetchone()
    if resultado:
        nuevos_puntos = resultado[0] + 1
        cursor.execute("UPDATE minigames_scores SET points = ? WHERE user_id = ?", (nuevos_puntos, user_id))
    else:
        cursor.execute("INSERT INTO minigames_scores VALUES (?, 1)", (user_id,))
    conn.commit()


# ==================================================
# 🎣 DETECTOR AUTOMÁTICO DE PALABRAS CLAVE (on_message)
# ==================================================
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    content = message.content.lower()
    keywords = ["mine", "fish", "work"]

    # Detecta si el mensaje contiene mine, fish o work en cualquier parte
    if any(kw in content for kw in keywords):
        await lanzar_minijuego_interactivo(message)
        return  # Evita que interfiera con otros comandos si comparten procesamiento

    await bot.process_commands(message)


# ==================================================
# 🎲 SELECCIONADOR ALEATORIO DE MINIJUEGOS (8 Variantes con Botones)
# ==================================================
async def lanzar_minijuego_interactivo(message):
    juego_id = random.randint(1, 8)
    
    if juego_id == 1:
        await juego_cofre_tesoro(message)
    elif juego_id == 2:
        await juego_cristal_minero(message)
    elif juego_id == 3:
        await juego_anzuelo_magico(message)
    elif juego_id == 4:
        await juego_cables_sistema(message)
    elif juego_id == 5:
        await juego_gatito_oculto(message)
    elif juego_id == 6:
        await juego_pocion_magica(message)
    elif juego_id == 7:
        await juego_estrella_fugaz(message)
    elif juego_id == 8:
        await juego_llave_maestra(message)


# --- 1. COFRE DEL TESORO ---
async def juego_cofre_tesoro(message):
    class View(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=20)
            self.ganador = random.randint(1, 3)
            for i in range(1, 4):
                btn = discord.ui.Button(label=f"Cofre #{i}", style=discord.ButtonStyle.secondary, custom_id=f"cofre_{i}")
                btn.callback = self.callback
                self.add_item(btn)

        async def callback(self, interaction: discord.ui.Interaction):
            if interaction.user != message.author:
                return await interaction.response.send_message("❌ Este juego no es tuyo.", ephemeral=True)
            num = int(interaction.data["custom_id"].split("_")[1])
            if num == self.ganador:
                await sumar_punto(message.author.id)
                await interaction.response.edit_message(content=None, embed=discord.Embed(title="🎉 ¡Tesoro Encontrado!", description=f"¡Felicidades {message.author.mention}! Hallaste monedas valiosas en el cofre #{num}. **(+1 Punto)**", color=0x2ECC71), view=None)
            else:
                await interaction.response.edit_message(content=None, embed=discord.Embed(title="💨 ¡Cofre Vacío!", description=f"El cofre #{num} estaba vacío. ¡Más suerte la próxima!", color=0xE74C3C), view=None)
            self.stop()

    embed = discord.Embed(title="⛏️ Exploración de Minas", description="¡Te adentraste en las profundidades! Elige uno de los 3 cofres antes de que expiren.", color=0xF1C40F)
    await message.channel.send(embed=embed, view=View())


# --- 2. EL CRISTAL MINERO ---
async def juego_cristal_minero(message):
    class View(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=20)
            cristales = [("💎 Diamante", discord.ButtonStyle.success), ("🔴 Rubí", discord.ButtonStyle.danger), ("🔵 Zafiro", discord.ButtonStyle.primary), ("⚫ Carbón", discord.ButtonStyle.secondary)]
            self.ganador = "💎 Diamante"
            random.shuffle(cristales)
            for label, style in cristales:
                btn = discord.ui.Button(label=label, style=style, custom_id=label)
                btn.callback = self.callback
                self.add_item(btn)

        async def callback(self, interaction: discord.ui.Interaction):
            if interaction.user != message.author:
                return await interaction.response.send_message("❌ Este juego no es tuyo.", ephemeral=True)
            if interaction.data["custom_id"] == self.ganador:
                await sumar_punto(message.author.id)
                await interaction.response.edit_message(content=None, embed=discord.Embed(title="✨ ¡Excelente Excavación!", description=f"¡Extrajiste un **Diamante puro** {message.author.mention}! **(+1 Punto)**", color=0x2ECC71), view=None)
            else:
                await interaction.response.edit_message(content=None, embed=discord.Embed(title="💥 ¡Piedra Común!", description=f"Golpeste material sin valor ({interaction.data['custom_id']}).", color=0xE74C3C), view=None)
            self.stop()

    embed = discord.Embed(title="💎 Veta de Minerales", description="Golpea la roca con el pico y selecciona el cristal más valioso.", color=0x3498DB)
    await message.channel.send(embed=embed, view=View())


# --- 3. EL ANZUELO MÁGICO ---
async def juego_anzuelo_magico(message):
    class View(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=20)
            cebos = [("🐟 Pez Dorado", True), ("👢 Bota Vieja", False), ("🦀 Cangrejo", False)]
            random.shuffle(cebos)
            for label, es_valioso in cebos:
                btn = discord.ui.Button(label=label, style=discord.ButtonStyle.primary, custom_id=str(es_valioso))
                btn.callback = self.callback
                self.add_item(btn)

        async def callback(self, interaction: discord.ui.Interaction):
            if interaction.user != message.author:
                return await interaction.response.send_message("❌ Este juego no es tuyo.", ephemeral=True)
            if interaction.data["custom_id"] == "True":
                await sumar_punto(message.author.id)
                await interaction.response.edit_message(content=None, embed=discord.Embed(title="🎣 ¡Gran Pesca!", description=f"¡Atrapaste una magnífica pieza {message.author.mention}! **(+1 Punto)**", color=0x2ECC71), view=None)
            else:
                await interaction.response.edit_message(content=None, embed=discord.Embed(title="💦 ¡Se escapó!", description="Atrapaste basura u objeto inútil del fondo del lago.", color=0xE74C3C), view=None)
            self.stop()

    embed = discord.Embed(title="🎣 Sesión de Pesca", description="¡El agua se mueve! Tira de la cuerda eligiendo el señuelo correcto.", color=0x1ABC9C)
    await message.channel.send(embed=embed, view=View())


# --- 4. DESACTIVAR EL MECANISMO ---
async def juego_cables_sistema(message):
    class View(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=20)
            colores = [("Cable Azul", False), ("Cable Rojo", True), ("Cable Verde", False)]
            random.shuffle(colores)
            for label, correcto in colores:
                btn = discord.ui.Button(label=label, style=discord.ButtonStyle.secondary, custom_id=str(correcto))
                btn.callback = self.callback
                self.add_item(btn)

        async def callback(self, interaction: discord.ui.Interaction):
            if interaction.user != message.author:
                return await interaction.response.send_message("❌ Este juego no es tuyo.", ephemeral=True)
            if interaction.data["custom_id"] == "True":
                await sumar_punto(message.author.id)
                await interaction.response.edit_message(content=None, embed=discord.Embed(title="⚡ ¡Mantenimiento Exitoso!", description=f"Reparaste el sistema a tiempo {message.author.mention}. **(+1 Punto)**", color=0x2ECC71), view=None)
            else:
                await interaction.response.edit_message(content=None, embed=discord.Embed(title="💥 ¡Cortocircuito!", description="Elegiste el cable incorrecto y falló la maquinaria.", color=0xE74C3C), view=None)
            self.stop()

    embed = discord.Embed(title="⚙️ Jornada Laboral", description="Hay un fallo técnico en el taller. Corta el cable correcto para completar tu trabajo.", color=0xE67E22)
    await message.channel.send(embed=embed, view=View())


# --- 5. ENCUENTRA AL GATITO ---
async def juego_gatito_oculto(message):
    class View(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=20)
            self.ganador = random.randint(1, 4)
            for i in range(1, 5):
                btn = discord.ui.Button(label=f"Caja #{i}", style=discord.ButtonStyle.primary, custom_id=f"caja_{i}")
                btn.callback = self.callback
                self.add_item(btn)

        async def callback(self, interaction: discord.ui.Interaction):
            if interaction.user != message.author:
                return await interaction.response.send_message("❌ Este juego no es tuyo.", ephemeral=True)
            num = int(interaction.data["custom_id"].split("_")[1])
            if num == self.ganador:
                await sumar_punto(message.author.id)
                await interaction.response.edit_message(content=None, embed=discord.Embed(title="🐱 ¡Apareció un Gatito!", description=f"¡Encontraste al tierno gatito escondido en la caja #{num} {message.author.mention}! **(+1 Punto)**", color=0xF1C40F), view=None)
            else:
                await interaction.response.edit_message(content=None, embed=discord.Embed(title="📦 ¡Caja Vacia!", description=f"Revisaste la caja #{num} pero solo habia polvo.", color=0x7F8C8D), view=None)
            self.stop()

    embed = discord.Embed(title="🐾 Búsqueda Felina", description="¡Hay gatitos traviesos jugando en el almacén Crazy Cats! Encuentra en qué caja se ocultó.", color=0xFFB6C1)
    await message.channel.send(embed=embed, view=View())


# --- 6. POCIÓN DE LA SUERTE ---
async def juego_pocion_magica(message):
    class View(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=20)
            self.ganador = random.randint(1, 3)
            for i in range(1, 4):
                btn = discord.ui.Button(label=f"Frasco #{i}", style=discord.ButtonStyle.success, custom_id=f"frasco_{i}")
                btn.callback = self.callback
                self.add_item(btn)

        async def callback(self, interaction: discord.ui.Interaction):
            if interaction.user != message.author:
                return await interaction.response.send_message("❌ Este juego no es tuyo.", ephemeral=True)
            num = int(interaction.data["custom_id"].split("_")[1])
            if num == self.ganador:
                await sumar_punto(message.author.id)
                await interaction.response.edit_message(content=None, embed=discord.Embed(title="🧪 ¡Poción Correcta!", description=f"¡Creaste el tónico perfecto {message.author.mention}! **(+1 Punto)**", color=0x2ECC71), view=None)
            else:
                await interaction.response.edit_message(content=None, embed=discord.Embed(title="💨 ¡Efervescencia Fallida!", description="El frasco burbujeó de más y perdió su efecto.", color=0xE74C3C), view=None)
            self.stop()

    embed = discord.Embed(title="🔮 Laboratorio de Pociones", description="Mezcla los ingredientes seleccionando el frasco de esencia correcto.", color=0x9B59B6)
    await message.channel.send(embed=embed, view=View())


# --- 7. ESTRELLA FUGAZ ---
async def juego_estrella_fugaz(message):
    class View(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=20)
            self.ganador = random.randint(1, 3)
            for i in range(1, 4):
                btn = discord.ui.Button(label=f"🌟 Estrella #{i}", style=discord.ButtonStyle.primary, custom_id=f"est_{i}")
                btn.callback = self.callback
                self.add_item(btn)

        async def callback(self, interaction: discord.ui.Interaction):
            if interaction.user != message.author:
                return await interaction.response.send_message("❌ Este juego no es tuyo.", ephemeral=True)
            num = int(interaction.data["custom_id"].split("_")[1])
            if num == self.ganador:
                await sumar_punto(message.author.id)
                await interaction.response.edit_message(content=None, embed=discord.Embed(title="⭐ ¡Deseo Concedido!", description=f"¡Atrapaste la estrella fugaz del cielo nocturno {message.author.mention}! **(+1 Punto)**", color=0xF1C40F), view=None)
            else:
                await interaction.response.edit_message(content=None, embed=discord.Embed(title="🌌 ¡Se desvaneció!", description="La estrella parpadeó y desapareció antes de tocarla.", color=0x34495E), view=None)
            self.stop()

    embed = discord.Embed(title="🌠 Lluvia de Estrellas", description="El cielo nocturno brilla. Atrapa la estrella correcta con un clic.", color=0xF39C12)
    await message.channel.send(embed=embed, view=View())


# --- 8. LLAVE MAESTRA ---
async def juego_llave_maestra(message):
    class View(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=20)
            self.ganador = random.randint(1, 3)
            for i in range(1, 4):
                btn = discord.ui.Button(label=f"Llave #{i}", style=discord.ButtonStyle.secondary, custom_id=f"llave_{i}")
                btn.callback = self.callback
                self.add_item(btn)

        async def callback(self, interaction: discord.ui.Interaction):
            if interaction.user != message.author:
                return await interaction.response.send_message("❌ Este juego no es tuyo.", ephemeral=True)
            num = int(interaction.data["custom_id"].split("_")[1])
            if num == self.ganador:
                await sumar_punto(message.author.id)
                await interaction.response.edit_message(content=None, embed=discord.Embed(title="🗝️ ¡Puerta Abierta!", description=f"¡La llave #{num} giró perfecta en la cerradura {message.author.mention}! **(+1 Punto)**", color=0x2ECC71), view=None)
            else:
                await interaction.response.edit_message(content=None, embed=discord.Embed(title="🔒 ¡Llave Incorrecta!", description="La llave se atascó en la cerradura y no abrió.", color=0xE74C3C), view=None)
            self.stop()

    embed = discord.Embed(title="🗝️ Puerta Secreta", description="En contraste un cofre cerrado con candado antiguo. Prueba la llave correcta.", color=0xD4AC0D)
    await message.channel.send(embed=embed, view=View())


# ==================================================
# 🏆 COMANDOS DE LEADERBOARD Y GESTIÓN PARA EL STAFF
# ==================================================

# 1. Ver Leaderboard (Público)
@bot.command(name="top", aliases=["leaderboard", "puntos"])
async def leaderboard(ctx):
    """Muestra el top de jugadores más activos en minijuegos"""
    cursor.execute("SELECT user_id, points FROM minigames_scores ORDER BY points DESC LIMIT 10")
    top_usuarios = cursor.fetchall()

    if not top_usuarios:
        return await ctx.send("📊 Aún no hay registros en la tabla de clasificación.")

    descripcion = ""
    for idx, (uid, pts) in enumerate(top_usuarios, start=1):
        medalla = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else f"`#{idx}`"
        descripcion += f"{medalla} <@{uid}> — **{pts} puntos**\n"

    embed = discord.Embed(
        title="🏆 Tabla de Clasificación • Mini Juegos",
        description=descripcion,
        color=0xF1C40F,
        timestamp=discord.utils.utcnow()
    )
    embed.set_footer(text=f"Solicitado por {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)


# 2. Staff: Reiniciar Leaderboard por completo
@bot.command(name="resetlb", aliases=["reiniciartop"])
@es_staff_por_id()
async def resetlb(ctx):
    """Limpia la tabla de puntos para iniciar una nueva temporada"""
    cursor.execute("DELETE FROM minigames_scores")
    conn.commit()

    embed = discord.Embed(
        title="🔄 Leaderboard Reiniciado",
        description="Se han borrado todos los puntajes anteriores. ¡Una nueva temporada ha comenzado!",
        color=0xE74C3C,
        timestamp=discord.utils.utcnow()
    )
    await ctx.send(embed=embed)


# 3. Staff: Eliminar a un usuario específico del Leaderboard
@bot.command(name="deluserlb", aliases=["quitaruserlb"])
@es_staff_por_id()
async def deluserlb(ctx, miembro: discord.Member):
    """Elimina los puntos de un usuario del leaderboard"""
    cursor.execute("DELETE FROM minigames_scores WHERE user_id = ?", (miembro.id,))
    conn.commit()
    await ctx.send(f"✅ Se han borrado los datos y puntos de {miembro.mention} del leaderboard.", delete_after=6)


# 4. Staff: Sumar o restar puntos manualmente a alguien
@bot.command(name="addpuntos", aliases=["darapuntos"])
@es_staff_por_id()
async def addpuntos(ctx, miembro: discord.Member, cantidad: int):
    """Ajusta los puntos de un usuario manualmente (ej: ?addpuntos @User 5)"""
    cursor.execute("SELECT points FROM minigames_scores WHERE user_id = ?", (miembro.id,))
    resultado = cursor.fetchone()
    
    if resultado:
        nuevos_puntos = resultado[0] + cantidad
        cursor.execute("UPDATE minigames_scores SET points = ? WHERE user_id = ?", (nuevos_puntos, miembro.id,))
    else:
        cursor.execute("INSERT INTO minigames_scores VALUES (?, ?)", (miembro.id, cantidad))
    conn.commit()

    await ctx.send(f"✨ Se han actualizado los puntos de {miembro.mention}. Ajuste aplicado: `{cantidad:+d}`", delete_after=6)

# EJECUCION INICIAL NO TOCAR NADA
if __name__ == "__main__":
    keep_alive() 
    print("🔥 Conectando con los servicios de Discord...")
    bot.run(TOKEN)