import threading
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot activo"

def run_web():
    app.run(host="0.0.0.0", port=10000)

threading.Thread(target=run_web).start()
import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import json
import os

TOKEN = os.environ["TOKEN"]

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

DURACION_DIAS = 20
LOG_CHANNEL_ID = 1477110955669323899  # ⚠️ PON AQUÍ TU ID DE CANAL DE LOGS

# ==========================
# FUNCIONES JSON
# ==========================

def cargar_boxes():
    with open("boxes.json", "r") as f:
        return json.load(f)

def guardar_boxes(data):
    with open("boxes.json", "w") as f:
        json.dump(data, f, indent=4)

# ==========================
# CREAR CAMITA
# ==========================

@bot.command()
@commands.has_permissions(manage_channels=True)
async def box(ctx, nombre: str, *miembros: discord.Member):

    guild = ctx.guild
    fecha_inicio = datetime.now()
    fecha_fin = fecha_inicio + timedelta(days=DURACION_DIAS)

    total_personas = 1 + len(miembros)

    if total_personas == 1:
        tipo = "Mini"
    elif total_personas == 2:
        tipo = "Duplex"
    elif total_personas == 3:
        tipo = "Trio"
    else:
        tipo = "Grupal"

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        ctx.author: discord.PermissionOverwrite(read_messages=True)
    }

    for m in miembros:
        overwrites[m] = discord.PermissionOverwrite(read_messages=True)

    canal = await guild.create_text_channel(nombre, overwrites=overwrites)

    # Embed dentro del canal
    embed = discord.Embed(
        title="🌙 Little Box",
        color=discord.Color.purple()
    )

    embed.add_field(name="Dueño/a", value=ctx.author.mention, inline=False)
    embed.add_field(name="Tipo", value=tipo, inline=False)
    embed.add_field(name="Adquisición", value=fecha_inicio.strftime("%d/%m/%Y %H:%M"), inline=False)
    embed.add_field(name="Expiración", value=f"{fecha_fin.strftime('%d/%m/%Y %H:%M')} (en {DURACION_DIAS} días)", inline=False)
    embed.set_footer(text=f"ID de Little Box: {canal.id}")

    mensaje = await canal.send(embed=embed)
    await mensaje.pin()

    # Guardar en JSON
    boxes = cargar_boxes()

    boxes[str(canal.id)] = {
        "dueno_id": ctx.author.id,
        "miembros": [m.id for m in miembros],
        "expira": fecha_fin.strftime("%Y-%m-%d %H:%M:%S")
    }

    guardar_boxes(boxes)

    await ctx.send(f"✅ Little Box creada correctamente: {canal.mention}")

    # Log
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        log_embed = discord.Embed(title="📦 Little Box creada", color=discord.Color.green())
        log_embed.add_field(name="Nombre", value=nombre)
        log_embed.add_field(name="Tipo", value=tipo)
        log_embed.add_field(name="Staff", value=ctx.author.mention)
        log_embed.add_field(name="Expira", value=fecha_fin.strftime("%d/%m/%Y %H:%M"))
        log_embed.set_footer(text=f"ID: {canal.id}")
        await log_channel.send(embed=log_embed)

# ==========================
# RENOVACIÓN
# ==========================

@bot.command()
@commands.has_permissions(manage_channels=True)
async def renovacion(ctx, box_id: int):

    boxes = cargar_boxes()

    if str(box_id) not in boxes:
        await ctx.send("❌ No existe una Little Box con ese ID.")
        return

    fecha_actual = datetime.strptime(boxes[str(box_id)]["expira"], "%Y-%m-%d %H:%M:%S")
    nueva_fecha = fecha_actual + timedelta(days=DURACION_DIAS)

    boxes[str(box_id)]["expira"] = nueva_fecha.strftime("%Y-%m-%d %H:%M:%S")
    guardar_boxes(boxes)

    canal = bot.get_channel(box_id)

    if canal:
        await canal.send("🌸 ¡Holi! La Little Box ha sido extendida por 20 días.")

    await ctx.send("✅ Renovación aplicada correctamente.")

# ==========================
# VERIFICAR EXPIRACIONES
# ==========================

@tasks.loop(minutes=10)
async def verificar_expiraciones():

    boxes = cargar_boxes()
    ahora = datetime.now()
    eliminadas = []

    for box_id, data in boxes.items():
        fecha_expira = datetime.strptime(data["expira"], "%Y-%m-%d %H:%M:%S")

        if ahora >= fecha_expira:
            canal = bot.get_channel(int(box_id))
            if canal:
                await canal.delete()
            eliminadas.append(box_id)

    for box_id in eliminadas:
        del boxes[box_id]

    guardar_boxes(boxes)

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")
    verificar_expiraciones.start()

bot.run(TOKEN)