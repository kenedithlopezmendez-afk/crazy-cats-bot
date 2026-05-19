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

    # --- FASE FINAL: DETERMINAR AL GANADOR DEFINITIVO ---
    if len(pilotos) == 1:
        ganador = pilotos
        embed_victoria = discord.Embed(
            title="👑 ¡TENEMOS UN GANADOR CÓSMICO!",
            description=f"Felicitaciones supremas para {ganador.mention}.\n\n¡Ha logrado esquivar todos los colapsos y es el único sobreviviente del torneo de plataformas! 🎉",
            color=0xF1C40F
        )
        embed_victoria.set_thumbnail(url=ganador.display_avatar.url)
        embed_victoria.set_footer(text=f"🌙 {ctx.guild.name} • Fin del Desafío")
        await canal_juego.send(content=f"🏆 {ganador.mention}", embed=embed_victoria)
    else:
        await canal_juego.send("💀 **Colapso Absoluto:** Todos los pilotos cayeron al vacío en la última ronda. No quedó nadie vivo para reclamar la victoria.")
# 🛑 CONTROLADOR DE ERRORES
@plataformas.error
async def plataformas_error(ctx, error):
    if isinstance(error, commands.MissingAnyRole):
        await ctx.send(f"❌ {ctx.author.mention}, **¡Acceso Denegado!** Lo siento, pero solo los miembros del Staff autorizados pueden iniciar el torneo de plataformas.")

        # ==================================================
# 🎰 SISTEMA DE JUEGO: CASINO DE RULETA (ROJO/NEGRO - PAR/IMPAR)
# ==================================================

# Configuración matemática de la ruleta (1 al 36)
NUMEROS_ROJOS = [ 1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36 ]
# El resto de los números del 1 al 36 que no estén aquí se considerarán NEGROS automáticamente.

# Diccionario global para almacenar las apuestas de la ronda actual
# Estructura: { ID_USUARIO: {"color": "Rojo"/"Negro"/None, "tipo": "Par"/"Impar"/None, "nombre": "Mención"} }
apuestas_ruleta = {}
inscripcion_ruleta_abierta = False

# --- MENÚ DESPLEGABLE DE APUESTAS ---
class OpcionesRuleta(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="🔴 Apostar a Rojo", description="Ganas si cae número rojo", emoji="🔴", value="Rojo"),
            discord.SelectOption(label="⚫ Apostar a Negro", description="Ganas si cae número negro", emoji="⚫", value="Negro"),
            discord.SelectOption(label="🔢 Apostar a PAR", description="Ganas si cae número par", emoji="⚖️", value="Par"),
            discord.SelectOption(label="Odds Apostar a IMPAR", description="Ganas si cae número impar", emoji="🔮", value="Impar"),
        ]
        super().__init__(placeholder="🎰 ¡Haz tu apuesta aquí!", min_values=1, max_values=2, options=options)

    async def callback(self, interaction: discord.Interaction):
        global inscripcion_ruleta_abierta
        if not inscripcion_ruleta_abierta:
            await interaction.response.send_message("❌ La mesa de apuestas ya está cerrada para esta ronda.", ephemeral=True)
            return

        user_id = interaction.user.id
        
        # Inicializar al usuario si es su primera vez en la ronda
        if user_id not in apuestas_ruleta:
            apuestas_ruleta[user_id] = {"color": None, "tipo": None, "nombre": interaction.user.mention}

        # Procesar lo que seleccionó el usuario (puede elegir hasta 2 cosas: un color y un tipo)
        for seleccion in self.values:
            if seleccion in ["Rojo", "Negro"]:
                apuestas_ruleta[user_id]["color"] = seleccion
            elif seleccion in ["Par", "Impar"]:
                apuestas_ruleta[user_id]["tipo"] = seleccion

        # Generar mensaje de confirmación bonito
        msg_apuesta = "🎰 **Tus apuestas actuales son:**\n"
        if apuestas_ruleta[user_id]["color"]:
            emoji = "🔴" if apuestas_ruleta[user_id]["color"] == "Rojo" else "⚫"
            msg_apuesta += f"{emoji} Color: **{apuestas_ruleta[user_id]['color']}**\n"
        if apuestas_ruleta[user_id]["tipo"]:
            msg_apuesta += f"🔢 Tipo: **{apuestas_ruleta[user_id]['tipo']}**\n"

        await interaction.response.send_message(f"✅ ¡Apuesta registrada, {interaction.user.display_name}!\n{msg_apuesta}", ephemeral=True)


class PanelRuleta(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(OpcionesRuleta())


# --- COMANDO 1: ABRIR LA MESA DE CASINO (Solo Staff) ---
@bot.command()
@commands.has_any_role(ROL_STAFF_JUEGO)
async def ruleta(ctx):
    global apuestas_ruleta, inscripcion_ruleta_abierta
    
    apuestas_ruleta.clear()
    inscripcion_ruleta_abierta = True
    
    embed_casino = discord.Embed(
        title="🎰 • ¡Bienvenidos al Casino Crazy Cats!",
        description=(
            "**¡La Ruleta de la Suerte está abierta!** 💸\n\n"
            "Despliega el menú de abajo para colocar tus apuestas.\n"
            "Puedes seleccionar **hasta dos opciones** (ej. un color y si es par/impar).\n\n"
            "⏳ El Staff usará `?girar` en cualquier momento para lanzar la bola..."
        ),
        color=0x2ECC71
    )
    embed_casino.set_image(url="https://i.imgur.com/83pZf6b.gif") # Un gif estético de casino/ruleta para dar ambiente
    embed_casino.set_footer(text=f"🎲 {ctx.guild.name} • ¡Hagan sus apuestas!")
    
    view = PanelRuleta()
    await ctx.send(embed=embed_casino, view=view)


# --- COMANDO 2: GIRAR LA RULETA Y ANUNCIAR GANADORES (Solo Staff) ---
@bot.command()
@commands.has_any_role(ROL_STAFF_JUEGO)
async def girar(ctx):
    global apuestas_ruleta, inscripcion_ruleta_abierta
    
    if not inscripcion_ruleta_abierta:
        await ctx.send("❌ No hay ninguna ruleta activa en este momento. Usa primero `?ruleta`.")
        return
        
    if not apuestas_ruleta:
        await ctx.send("❌ Nadie ha hecho ninguna apuesta todavía. ¡Dale un momento a los jugadores!")
        return

    # Cerramos la mesa
    inscripcion_ruleta_abierta = False
    canal_juego = ctx.channel

    # --- SIMULACIÓN DE GIRO (Efecto animado por texto) ---
    embed_giro = discord.Embed(
        title="🎰 • ¡Girando la Ruleta Cósmica!",
        description="### 🔄 El crupier lanza la bola... \n\n`[ 🟢 ] Los números empiezan a correr...`",
        color=0xF1C40F
    )
    msg_giro = await canal_juego.send(embed=embed_giro)
    await asyncio.sleep(2)

    embed_giro.description = "### 🎰 ¡La bola está perdiendo velocidad! \n\n`[ 🔴⚫🔴⚫ ] ¡Hagan juego, no va más!`"
    await msg_giro.edit(embed=embed_giro)
    await asyncio.sleep(2)

    # --- GENERAR EL RESULTADO REAL ---
    numero_ganador = random.randint(1, 36)
    color_ganador = "Rojo" if numero_ganador in NUMEROS_ROJOS else "Negro"
    tipo_ganador = "Par" if numero_ganador % 2 == 0 else "Impar"
    
    emoji_color = "🔴" if color_ganador == "Rojo" else "⚫"

    # --- PROCESAR GANADORES ---
    lista_ganadores = []

    for user_id, apuesta in apuestas_ruleta.items():
        aciertos = 0
        pago_texto = []
        
        # Verificar Color
        if apuesta["color"] == color_ganador:
            aciertos += 1
            pago_texto.append(f"{emoji_color} Color")
        # Verificar Par/Impar
        if apuesta["tipo"] == tipo_ganador:
            aciertos += 1
            pago_texto.append(f"🔢 {tipo_ganador}")
            
        if aciertos > 0:
            combinaciones = " y ".join(pago_texto)
            lista_ganadores.append(f"• {apuesta['nombre']} acertó **{combinaciones}** 🎉")

    # --- DISEÑAR EMBED DE RESULTADOS ---
    embed_resultado = discord.Embed(
        title=f"🎰 • ¡RESULTADO DE LA RULETA!",
        description=f"La bola se ha detenido en el número:\n\n# {emoji_color} **{numero_ganador}** ({color_ganador} y {tipo_ganador})",
        color=0x9B59B6 if color_ganador == "Rojo" else "0x34495E"
    )
    
    txt_ganadores = "\n".join(lista_ganadores) if lista_ganadores else "*La casa gana... Nadie acertó sus apuestas esta ronda. 🏛️*"
    embed_resultado.add_field(name="💰 GANADORES DE LA RONDA", value=txt_ganadores, inline=False)
    embed_resultado.set_footer(text=f"🎰 {ctx.guild.name} • ¡Suerte para la próxima!")
    
    # Editamos el mensaje del giro con el resultado definitivo
    await msg_giro.edit(embed=embed_resultado)


# --- CONTROLADOR DE ERRORES ---
@ruleta.error
@girar.error
async def casino_errors(ctx, error):
    if isinstance(error, commands.MissingAnyRole):
        await ctx.send(f"❌ {ctx.author.mention}, solo el Staff autorizado puede operar las mesas de juego de la ruleta.")

        # ==================================================
# 🎲 SISTEMA DE JUEGO: GRAN LOTERÍA AUTOMÁTICA (9 FIGURAS)
# ==================================================

# 🌟 BARAJA AMPLIADA A 30 CARTAS (Para soportar cartones de 9 figuras sin repetirse tanto)
BARAJA_LOTERIA = [
    "🐓 El Gallo", "😈 El Diablito", "🌙 La Luna", "👑 La Corona", 
    "🐟 El Pescado", "🌴 La Palmera", "💀 La Calavera", "❤️ El Corazón",
    "🍉 La Sandía", "⭐ La Estrella", "🔔 La Campana", "🏹 El Archero",
    "🐸 El Rana", "🦂 El Alacrán", "🗺️ El Mapa", "🛡️ El Escudo",
    "🔥 El Fuego", "☀️ El Sol", "🌹 La Rosa", "🧠 El Cerebro", "💎 El Diamante",
    "🦁 El León", "🎈 El Globo", "🍕 La Pizza", "🛸 El Ovni", "🐱 El Gato",
    "🌵 El Cactus", "🦉 El Búho", "🎸 La Guitarra", "🍦 El Helado"
]

# Variables globales para controlar la partida
cartones_jugadores = {}
cartas_cantadas = []
juego_activo = False

class PanelLoteria(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    # Botón 1: El registro secreto
    @discord.ui.button(label="✨ Obtener Cartón", style=discord.ButtonStyle.primary, custom_id="btn_unirse")
    async def unirse(self, interaction: discord.Interaction, button: discord.ui.Button):
        global juego_activo
        if juego_activo:
            await interaction.response.send_message("❌ ¡Demasiado tarde! La lotería ya está en marcha.", ephemeral=True)
            return
            
        user_id = interaction.user.id
        
        # Si ya tiene un cartón, no le damos uno nuevo, solo se lo recordamos
        if user_id in cartones_jugadores:
            format_carton = "\n".join([f"• {figura}" for figura in cartones_jugadores[user_id]])
            await interaction.response.send_message(
                f"⚠️ ¡Ya estás inscrito! Tu cartón asignado es:\n{format_carton}", 
                ephemeral=True
            )
            return
        
        # 🌟 NUEVO CAMBIO: Le generamos un cartón único de 9 figuras al azar
        carton = random.sample(BARAJA_LOTERIA, 9)
        cartones_jugadores[user_id] = carton
        
        format_carton = "\n".join([f"• {figura}" for figura in carton])
        await interaction.response.send_message(
            f"✅ **¡Te has inscrito!**\n\nEste es tu cartón de 9 figuras para la ronda:\n{format_carton}\n\n¡Presta atención al chat!", 
            ephemeral=True
        )

    # Botón 2: El recordatorio efímero del cartón (Para que lo revisen cuando quieran)
    @discord.ui.button(label="📋 Ver mi Cartón", style=discord.ButtonStyle.blurple, custom_id="btn_ver_carton")
    async def ver_carton(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        
        if user_id not in cartones_jugadores:
            await interaction.response.send_message("❌ Aún no has solicitado un cartón. Presiona primero **✨ Obtener Cartón**.", ephemeral=True)
            return
            
        carton_usuario = cartones_jugadores[user_id]
        format_carton = "\n".join([f"• {figura}" for figura in carton_usuario])
        
        await interaction.response.send_message(
            f"📋 **Tus 9 figuras asignadas son:**\n{format_carton}\n\n*Recuerda presionar '¡LOTERÍA!' cuando el bot cante todas estas.*", 
            ephemeral=True
        )

    # Botón 3: El reclamo de victoria
    @discord.ui.button(label="📢 ¡LOTERÍA!", style=discord.ButtonStyle.success, custom_id="btn_loteria")
    async def gritar(self, interaction: discord.Interaction, button: discord.ui.Button):
        global juego_activo, cartas_cantadas, cartones_jugadores
        
        if not juego_activo:
            await interaction.response.send_message("❌ El juego aún no ha comenzado formalmente.", ephemeral=True)
            return

        user_id = interaction.user.id
        if user_id not in cartones_jugadores:
            await interaction.response.send_message("❌ No estás participando en esta partida.", ephemeral=True)
            return
            
        carton_usuario = cartones_jugadores[user_id]
        # Verifica estrictamente si las 9 figuras ya salieron en el chat
        completo = all(carta in cartas_cantadas for carta in carton_usuario)
        
        if completo:
            juego_activo = False  # Detiene el bucle de cartas automáticamente
            await interaction.response.send_message(
                f"🎉 👑 **¡TENEMOS UN GANADOR!** {interaction.user.mention} completó sus 9 figuras y cantó ¡LOTERÍA! legítimamente. Su cartón fue verificado con éxito. ¡Felicidades! 🏆"
            )
            self.stop()
        else:
            await interaction.response.send_message("❌ **¡Falsa alarma!** Aún te faltan figuras por marcar en tu cartón de 9. Sigue atento.", ephemeral=True)


# --- COMANDO 1: ABRIR LA MESA (Solo Staff) ---
@bot.command()
@commands.has_any_role(ROL_STAFF_JUEGO)
async def loteria(ctx):
    global juego_activo, cartas_cantadas, cartones_jugadores
    
    cartones_jugadores.clear()
    cartas_cantadas.clear()
    juego_activo = False
    
    embed = discord.Embed(
        title="🎉 • ¡Gran Lotería de Crazy Cats!",
        description=(
            "**¡Preparen sus frijolitos!** 🐾\n\n"
            "Presiona el botón de abajo para registrarte y recibir tu **cartón secreto con 9 figuras**.\n"
            "Cuando todos estén listos, un moderador usará `?cantar` para empezar el juego."
        ),
        color=0xE67E22
    )
    embed.set_footer(text=f"🌙 {ctx.guild.name} • Modo Inscripción")
    
    view = PanelLoteria()
    await ctx.send(embed=embed, view=view)


# --- COMANDO 2: AUTOMATIZAR EL CANTO (Solo Staff) ---
@bot.command()
@commands.has_any_role(ROL_STAFF_JUEGO)
async def cantar(ctx):
    global juego_activo, cartas_cantadas, cartones_jugadores
    
    if juego_activo:
        await ctx.send("❌ Ya hay una ronda cantándose en este momento.")
        return
        
    if not cartones_jugadores:
        await ctx.send("❌ No hay ningún jugador inscrito todavía. ¡Espera a que saquen sus cartones!")
        return

    juego_activo = True
    await ctx.send("🔥 **¡Se barajea el mazo de 30 cartas! El juego comienza en 5 segundos...**")
    await asyncio.sleep(5)

    mazo_mezclado = BARAJA_LOTERIA.copy()
    random.shuffle(mazo_mezclado)

    # Ciclo automático de cartas
    for carta in mazo_mezclado:
        if not juego_activo: 
            break  
            
        cartas_cantadas.append(carta)
        
        embed_carta = discord.Embed(
            title="🃏 • ¡Se va y se corre con...!",
            description=f"### 📢 **{carta}**",
            color=0x2ECC71
        )
        # Mostramos las últimas 5 cartas cantadas para que lleven mejor el control visual
        historial = ", ".join(cartas_cantadas[-5:])
        embed_carta.add_field(name="📋 Últimas llamadas", value=f"`{historial}`", inline=False)
        embed_carta.set_footer(text=f"Crazy Cats • Cartas cantadas: {len(cartas_cantadas)}/30")
        
        await ctx.send(embed=embed_carta)
        await asyncio.sleep(4) # 4 segundos entre carta y carta para mantenerlo fluido

    if juego_activo:
        juego_activo = False
        await ctx.send("🃏 **¡Se terminó el mazo!** Increíblemente nadie logró completar sus 9 figuras esta vez. ¡Más suerte en la próxima ronda!")


# 🛑 CONTROLADOR DE ERRORES PARA AMBOS COMANDOS
@loteria.error
@cantar.error
async def loteria_errors(ctx, error):
    if isinstance(error, commands.MissingAnyRole):
        await ctx.send(f"❌ {ctx.author.mention}, solo el Staff autorizado puede gestionar la lotería.")
# ==================================================
# EJECUCIÓN INICIAL
# ==================================================
if __name__ == "__main__":
    keep_alive() 
    print("🔥 Conectando con los servicios de Discord...")
    bot.run(TOKEN)