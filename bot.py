from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot activo"

def run():
    app.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = Thread(target=run)
    t.start()

import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import psycopg2
import os

TOKEN = os.environ["TOKEN"]
DATABASE_URL = os.environ["DATABASE_URL"]

LOG_CHANNEL_ID = 1477110955669323899  # PON AQUI TU CANAL DE LOGS

DURACION_DIAS = 20

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="?", intents=intents)

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()


async def enviar_log(guild, titulo, descripcion):

    canal = bot.get_channel(LOG_CHANNEL_ID)

    embed = discord.Embed(
        title=titulo,
        description=descripcion,
        color=discord.Color.orange()
    )

    embed.timestamp = datetime.now()

    await canal.send(embed=embed)


@bot.event
async def on_ready():

    print(f"Bot conectado como {bot.user}")

    revisar_boxes.start()


# CREAR BOX

@bot.command()
@commands.has_permissions(manage_channels=True)
async def box(ctx, nombre, dueno: discord.Member, *miembros: discord.Member):

    guild = ctx.guild

    inicio = datetime.now()
    fin = inicio + timedelta(days=DURACION_DIAS)

    total = 1 + len(miembros)

    if total == 1:
        tipo = "Mini"
    elif total == 2:
        tipo = "Duo"
    else:
        tipo = "Grupal"

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        dueno: discord.PermissionOverwrite(read_messages=True)
    }

    for m in miembros:
        overwrites[m] = discord.PermissionOverwrite(read_messages=True)

    canal = await guild.create_text_channel(nombre, overwrites=overwrites)

    miembros_ids = ",".join([str(m.id) for m in miembros])

    cursor.execute("""
    INSERT INTO boxes(nombre,tipo,canal_id,dueno_id,staff_id,miembros,inicio,fin)
    VALUES(%s,%s,%s,%s,%s,%s,%s,%s)
    """,(nombre,tipo,canal.id,dueno.id,ctx.author.id,miembros_ids,inicio,fin))

    conn.commit()

    embed = discord.Embed(
        title="📦 Nueva Box",
        description=f"Bienvenido a tu box {dueno.mention}",
        color=discord.Color.green()
    )

    embed.add_field(name="Tipo", value=tipo)
    embed.add_field(name="Duración", value=f"{DURACION_DIAS} días")
    embed.add_field(name="Dueño", value=dueno.mention)

    msg = await canal.send(embed=embed)
    await msg.pin()

    await enviar_log(
        guild,
        "📦 BOX CREADA",
        f"Nombre: {nombre}\nDueño: {dueno.mention}\nStaff: {ctx.author.mention}"
    )


# EXTENDER BOX

@bot.command()
@commands.has_permissions(manage_channels=True)
async def extender(ctx, box_id:int):

    cursor.execute("SELECT canal_id,fin,dueno_id,nombre FROM boxes WHERE id=%s",(box_id,))
    data = cursor.fetchone()

    if not data:
        await ctx.send("❌ Box no encontrada")
        return

    canal_id, fin, dueno_id, nombre = data

    nuevo_fin = fin + timedelta(days=DURACION_DIAS)

    cursor.execute("UPDATE boxes SET fin=%s WHERE id=%s",(nuevo_fin,box_id))
    conn.commit()

    canal = bot.get_channel(canal_id)

    await canal.send(f"✨ Hola <@{dueno_id}>, tu box ha sido extendida {DURACION_DIAS} días más.")

    await enviar_log(
        ctx.guild,
        "🔄 BOX EXTENDIDA",
        f"{nombre} extendida por {ctx.author.mention}"
    )


# VER BOXES

@bot.command()
async def boxes(ctx):

    cursor.execute("SELECT id,nombre,fin FROM boxes")

    datos = cursor.fetchall()

    if not datos:
        await ctx.send("No hay boxes activas")
        return

    embed = discord.Embed(
        title="📦 Boxes activas",
        color=discord.Color.blue()
    )

    for box in datos:

        embed.add_field(
            name=f"{box[1]} (ID {box[0]})",
            value=f"Vence: {box[2]}",
            inline=False
        )

    await ctx.send(embed=embed)


# ELIMINAR BOX

@bot.command()
@commands.has_permissions(manage_channels=True)
async def eliminar(ctx, box_id:int):

    cursor.execute("SELECT canal_id,nombre FROM boxes WHERE id=%s",(box_id,))
    data = cursor.fetchone()

    if not data:
        await ctx.send("❌ No encontrada")
        return

    canal_id, nombre = data

    canal = bot.get_channel(canal_id)

    await canal.delete()

    cursor.execute("DELETE FROM boxes WHERE id=%s",(box_id,))
    conn.commit()

    await enviar_log(
        ctx.guild,
        "🗑 BOX ELIMINADA",
        f"{nombre} eliminada por {ctx.author.mention}"
    )


# RECORDATORIO + ELIMINACION

@tasks.loop(hours=12)
async def revisar_boxes():

    ahora = datetime.now()

    cursor.execute("SELECT id,canal_id,fin,dueno_id,nombre FROM boxes")

    for box in cursor.fetchall():

        box_id, canal_id, fin, dueno_id, nombre = box

        restante = fin - ahora

        canal = bot.get_channel(canal_id)

        if restante.days == 1:

            await canal.send(
                f"⚠️ <@{dueno_id}> tu box vence en 1 día."
            )

        if ahora >= fin:

            await canal.send("❌ Esta box ha expirado.")

            await canal.delete()

            cursor.execute("DELETE FROM boxes WHERE id=%s",(box_id,))
            conn.commit()

keep_alive()
bot.run(TOKEN)