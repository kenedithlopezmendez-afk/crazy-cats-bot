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
    embed_casino.set_image(url="https://media3.giphy.com/media/v1.Y2lkPTZjMDliOTUya3JzZGk0N24xbTc1bzlmZ3I2dWUxY2V4NXduYTd2cWRjcmRvNHA1eSZlcD12MV9naWZzX3NlYXJjaCZjdD1n/xUn3CftPBajoflzROU/source.gif") # Un gif estético de casino/ruleta para dar ambiente
    embed_casino.set_footer(text=f"🎲 {ctx.guild.name} • ¡Hagan sus apuestas!")
    
    view = PanelRuleta()
    await ctx.send(embed=embed_casino, view=view)


# --- COMANDO 2: GIRAR LA RULETA Y ANUNCIAR GANADORES (CORREGIDO) ---
@bot.command()
@commands.has_any_role(ROL_STAFF_JUEGO)
async def girar(ctx):
    global apuestas_ruleta, inscripcion_ruleta_abierta
    
    if not list(apuestas_ruleta.keys()) and inscripcion_ruleta_abierta:
        # Por seguridad si estás testeando solo, te dejamos girar aunque no haya apuestas largas
        pass
    elif not inscripcion_ruleta_abierta:
        await ctx.send("❌ No hay ninguna ruleta activa en este momento. Usa primero `?ruleta`.")
        return
        
    # Cerramos la mesa de inmediato
    inscripcion_ruleta_abierta = False
    canal_juego = ctx.channel

    # --- SIMULACIÓN DE GIRO ---
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
        
        if apuesta["color"] == color_ganador:
            aciertos += 1
            pago_texto.append(f"{emoji_color} Color")
        if apuesta["tipo"] == tipo_ganador:
            aciertos += 1
            pago_texto.append(f"🔢 {tipo_ganador}")
            
        if aciertos > 0:
            combinaciones = " y ".join(pago_texto)
            lista_ganadores.append(f"• {apuesta['nombre']} acertó **{combinaciones}** 🎉")

    # --- DISEÑAR EMBED DE RESULTADOS ---
    # 🌟 CORRECCIÓN AQUÍ: Quitamos las comillas molestas del color para evitar el crash
    color_final = 0xE74C3C if color_ganador == "Rojo" else 0x2C3E50

    embed_resultado = discord.Embed(
        title=f"🎰 • ¡RESULTADO DE LA RULETA!",
        description=f"La bola se ha detenido en el número:\n\n# {emoji_color} **{numero_ganador}** ({color_ganador} y {tipo_ganador})",
        color=color_final
    )
    
    txt_ganadores = "\n".join(lista_ganadores) if lista_ganadores else "*La casa gana... Nadie acertó sus apuestas esta ronda. 🏛️*"
    embed_resultado.add_field(name="💰 GANADORES DE LA RONDA", value=txt_ganadores, inline=False)
    embed_resultado.set_footer(text=f"🎰 {ctx.guild.name} • ¡Suerte para la próxima!")
    
    # Editamos el mensaje original para mostrar el flamante ganador
    await msg_giro.edit(embed=embed_resultado)


# --- CONTROLADOR DE ERRORES ---
@ruleta.error
@girar.error
async def casino_errors(ctx, error):
    if isinstance(error, commands.MissingAnyRole):
        await ctx.send(f"❌ {ctx.author.mention}, solo el Staff autorizado puede operar las mesas de juego de la ruleta.")

       # # ==================================================
# 🎲 SISTEMA DE JUEGO: GRAN LOTERÍA INTERACTIVA (9 FIGURAS)
# ==================================================

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
carta_actual = None
juego_activo = False

# --- INTERFAZ DINÁMICA DE BOTONES (Se envía abajo de cada carta cantada) ---
class InterfazLoteria(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    # 📋 Botón: Ver mi Cartón
    @discord.ui.button(label="📋 Ver mi Cartón", style=discord.ButtonStyle.blurple, custom_id="btn_ver_carton")
    async def ver_carton(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        if user_id not in cartones_jugadores:
            await interaction.response.send_message("❌ No estás inscrito en esta partida. ¡Dale al botón azul de la inscripción original!", ephemeral=True)
            return
            
        datos = cartones_jugadores[user_id]
        format_carton = []
        
        for figura in datos["figuras"]:
            status = "✅" if figura in datos["marcadas"] else "🔹"
            format_carton.append(f"{status} {figura}")
            
        lista_visual = "\n".join(format_carton)
        await interaction.response.send_message(
            f"📋 **Progreso de tu cartón:**\n{lista_visual}\n\n*¡Presiona '📌 Marcar Figura' cuando salga una tuya!*", 
            ephemeral=True
        )

    # 📌 Botón: Marcar la figura actual en juego
    @discord.ui.button(label="📌 Marcar Figura", style=discord.ButtonStyle.primary, custom_id="btn_marcar_figura")
    async def marcar_figura(self, interaction: discord.Interaction, button: discord.ui.Button):
        global juego_activo, carta_actual
        if not juego_activo or not carta_actual:
            await interaction.response.send_message("❌ El juego no ha comenzado o no hay una carta activa para marcar.", ephemeral=True)
            return

        user_id = interaction.user.id
        if user_id not in cartones_jugadores:
            await interaction.response.send_message("❌ No estás participando en esta partida.", ephemeral=True)
            return

        datos = cartones_jugadores[user_id]
        
        if carta_actual in datos["figuras"]:
            if carta_actual not in datos["marcadas"]:
                datos["marcadas"].append(carta_actual)
                await interaction.response.send_message(f"🎯 ¡Anotado! Has marcado **{carta_actual}** en tu cartón.", ephemeral=True)
            else:
                await interaction.response.send_message(f"⚠️ Ya habías marcado **{carta_actual}** anteriormente.", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ La carta **{carta_actual}** no está en tu cartón. ¡Presta más atención!", ephemeral=True)

    # 📢 Botón: Reclamar Victoria
    @discord.ui.button(label="📢 ¡LOTERÍA!", style=discord.ButtonStyle.success, custom_id="btn_loteria")
    async def gritar(self, interaction: discord.Interaction, button: discord.ui.Button):
        global juego_activo, cartones_jugadores
        
        if not juego_activo:
            await interaction.response.send_message("❌ La lotería no está activa.", ephemeral=True)
            return

        user_id = interaction.user.id
        if user_id not in cartones_jugadores:
            await interaction.response.send_message("❌ No estás participando en esta partida.", ephemeral=True)
            return
            
        datos = cartones_jugadores[user_id]
        completo = len(datos["marcadas"]) == 9 and all(f in cartas_cantadas for f in datos["marcadas"])
        
        if completo:
            juego_activo = False  
            await interaction.response.send_message(
                f"🎉 👑 **¡TENEMOS UN GANADOR!** {interaction.user.mention} llenó sus 9 casillas perfectamente y cantó ¡LOTERÍA! legítimamente. ¡Felicidades! 🏆"
            )
            self.stop()
        else:
            await interaction.response.send_message("❌ **¡Falsa alarma!** Aún no has marcado tus 9 figuras válidas en el cartón. ¡Sigue revisando!", ephemeral=True)


# --- INTERFAZ EXCLUSIVA PARA EL BOTÓN DE INSCRIPCIÓN ---
class PanelInscripcion(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="✨ Obtener Cartón (9 Figuras)", style=discord.ButtonStyle.primary, custom_id="btn_unirse_inicial")
    async def unirse(self, interaction: discord.Interaction, button: discord.ui.Button):
        global juego_activo
        if juego_activo:
            await interaction.response.send_message("❌ ¡Demasiado tarde! Las cartas ya se están cantando.", ephemeral=True)
            return
            
        user_id = interaction.user.id
        
        if user_id in cartones_jugadores:
            format_carton = "\n".join([f"• {f}" for f in cartones_jugadores[user_id]["figuras"]])
            await interaction.response.send_message(f"⚠️ Ya estás inscrito. Tu cartón es:\n{format_carton}", ephemeral=True)
            return
        
        carton_aleatorio = random.sample(BARAJA_LOTERIA, 9)
        cartones_jugadores[user_id] = {"figuras": carton_aleatorio, "marcadas": []}
        
        format_carton = "\n".join([f"• {f}" for f in carton_aleatorio])
        await interaction.response.send_message(
            f"✅ **¡Inscrito con éxito!**\n\nTu cartón secreto de 9 figuras es:\n{format_carton}\n\n¡Cada carta que mande el bot llevará los botones abajo para interactuar!", 
            ephemeral=True
        )


# --- COMANDO 1: ABRIR LA MESA DE INSCRIPCIÓN (Usa el validador de Staff por ID) ---
@bot.command()
@commands.has_any_role(ROL_STAFF_JUEGO)
async def loteria(ctx):
    global juego_activo, cartas_cantadas, cartones_jugadores, carta_actual
    
    cartones_jugadores.clear()
    cartas_cantadas.clear()
    carta_actual = None
    juego_activo = False
    
    embed = discord.Embed(
        title="🎉 • ¡Gran Lotería de Crazy Cats!",
        description=(
            "**¡Preparen sus frijolitos!** 🐾\n\n"
            "Presiona el botón de abajo para registrarte y recibir tu **cartón secreto con 9 figuras**.\n"
            "Cuando todos estén inscritos, un moderador usará `Dcantar` para lanzar el juego automático."
        ),
        color=0xE67E22
    )
    embed.set_footer(text=f"🌙 {ctx.guild.name} • Fase de Registros")
    
    await ctx.send(embed=embed, view=PanelInscripcion())


# --- COMANDO 2: CANTAR AUTOMÁTICAMENTE CON BOTONES INYECTADOS ---
@bot.command()
@commands.has_any_role(ROL_STAFF_JUEGO)
async def cantar(ctx):
    global juego_activo, cartas_cantadas, cartones_jugadores, carta_actual
    
    if juego_activo:
        await ctx.send("❌ Ya hay una ronda en proceso.")
        return
        
    if not cartones_jugadores:
        await ctx.send("❌ No hay jugadores inscritos todavía.")
        return

    juego_activo = True
    await ctx.send("🔥 **¡Se barajea el mazo! Las cartas saldrán automáticamente con botones incorporados...**")
    await asyncio.sleep(4)

    mazo_mezclado = BARAJA_LOTERIA.copy()
    random.shuffle(mazo_mezclado)

    for carta in mazo_mezclado:
        if not juego_activo: 
            break  
            
        carta_actual = carta
        cartas_cantadas.append(carta)
        
        embed_carta = discord.Embed(
            title="🃏 • ¡Se va y se corre con...!",
            description=f"# 📢 **{carta}**",
            color=0x2ECC71
        )
        historial = ", ".join(cartas_cantadas[-4:])
        embed_carta.add_field(name="📋 Últimas llamadas", value=f"`{historial}`", inline=False)
        embed_carta.set_footer(text=f"Crazy Cats • Cartas cantadas: {len(cartas_cantadas)}/30")
        
        view_actual = InterfazLoteria()
        await ctx.send(embed=embed_carta, view=view_actual)
        
        await asyncio.sleep(5)

    if juego_activo:
        juego_activo = False
        await ctx.send("🃏 **¡Se terminó el mazo!** El juego ha concluido sin ganadores esta vez.")


# 🛑 GESTOR DE ERRORES DE LOTERÍA
@loteria.error
@cantar.error
async def loteria_errors(ctx, error):
    if isinstance(error, commands.CheckFailure) or isinstance(error, commands.MissingAnyRole):
        embed_error = discord.Embed(
            title="🚫 • Acceso Denegado",
            description=f"Lo siento {ctx.author.mention}, pero necesitas rango de **Staff** para gestionar la lotería.",
            color=0xE74C3C
        )
        await ctx.send(embed=embed_error)

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
        name="🔒 1. CONTROL DE DINÁMICAS (Solo Staff)",
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
            "**Gran Lotería (Solo Staff inicia):**\n"
            "• `Dloteria` -> Abre registros con cartones de 9 figuras.\n"
            "• `Dcantar` -> Lanza las cartas automáticamente con botones interactivos.\n\n"
            "**Casino Ruleta (Solo Staff inicia):**\n"
            "• `Druleta` -> Abre el panel de apuestas interactivo.\n"
            "• `Dgirar` -> Cierra apuestas, gira la ruleta y anuncia ganadores.\n\n"
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
    1: {"item": "🎒 Lingote de Magmaria", "dueno": "<@822895885566345216>", "precio_inicial": "5 emp", "imagen": "https://i.imgur.com/Ejemplo1.png"},
    2: {"item": "👑 Corona Imperial (Ítem)", "dueno": "MishiStaff", "precio_inicial": 10000, "imagen": ""},
    3: {"item": "🐱 Gato Místico Level 100", "dueno": "Dawee", "precio_inicial": 7500, "imagen": ""},
    4: {"item": "📦 Caja de Suministros Épica", "dueno": "Moderador1", "precio_inicial": 3000, "imagen": ""},
    5: {"item": "💎 500 Gemas Nekotina", "dueno": "Dawee", "precio_inicial": 15000, "imagen": ""},
    6: {"item": "🎫 Ticket de Cambio de Nombre", "dueno": "StaffCat", "precio_inicial": 2000, "imagen": ""},
    7: {"item": "⚔️ Espada Legendaria", "dueno": "Dawee", "precio_inicial": 8000, "imagen": ""},
    8: {"item": "🍏 Manzana Dorada x5", "dueno": "AdminMishi", "precio_inicial": 4000, "imagen": ""},
    9: {"item": "⚡ Poción de Experiencia x10", "dueno": "Dawee", "precio_inicial": 6000, "imagen": ""},
    10: {"item": "🔥 Súper Pack Sorpresa Final", "dueno": "Dawee", "precio_inicial": 25000, "imagen": ""}
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

    # --- COMANDO: MOSTRAR CARTELERA COMPLETA EN SECRETO (SOLO STAFF) ---
@bot.command(name="subastas")
@es_staff_por_id()
async def subastas(ctx):
    # 🤫 BORRADO SECRETO: Elimina el mensaje del Staff de inmediato
    try:
        await ctx.message.delete()
    except discord.Forbidden:
        pass  # Si el bot no tiene permisos para borrar mensajes, no crashea

    embed = discord.Embed(
        title="🔨 • ¡CARTELERA OFICIAL DE SUBASTAS! • 🪙",
        description=(
            "¡Atención Mishitos! Los motores preparen esos emps. 🔥\n"
            "Aquí tienen la lista completa de los ítems que se disputarán hoy junto a sus dueños.\n\n"
            "⚠️ *Los precios iniciales son secretos hasta que el Staff abra cada lista con `Dlista`.* \n"
            "---"
        ),
        color=0xE67E22  # Color naranja llamativo para el evento 🐈
    )

    # 🔄 Recorremos las 10 listas de forma automática
    for num, datos in SUBASTAS_DATA.items():
        # Si tienes campos vacíos en tu configuración, evita que se rompa el embed
        item_nombre = datos["item"] if datos["item"] else "Por anunciar..."
        dueno_nombre = datos["dueno"] if datos["dueno"] else "Anónimo"
        
        # Agregamos cada lista como un campo en el Embed (sin el precio inicial)
        embed.add_field(
            name=f"📦 Lista #{num}",
            value=f"**Ítem:** {item_nombre}\n👤 **Dueño:** {dueno_nombre}",
            inline=False
        )

    embed.set_footer(text=f"🐾 {ctx.guild.name} • ¡Preparen sus billeteras!")
    
    # Si quieres poner una imagen general de cartelera o banner abajo, pon su link aquí:
    embed.set_image(url="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExM3Z6Ym94ZnM3N3Y0b3E4ZXN4ZHY4Y3ZpZ3B3dzBwYm9pZnZidSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/l0HlVJpG6N9YshF8k/giphy.gif")

    await ctx.send(embed=embed)
# ==================================================
# EJECUCIÓN INICIAL
# ==================================================
if __name__ == "__main__":
    keep_alive() 
    print("🔥 Conectando con los servicios de Discord...")
    bot.run(TOKEN)