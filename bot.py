import discord
from discord.ext import commands, tasks
from flask import Flask
import psycopg2
from datetime import datetime, timedelta
import os
import threading

TOKEN = os.environ["TOKEN"]
DURACION_DIAS = 20
LOG_CHANNEL_ID = 1477110955669323899

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="?", intents=intents)

# ---------------- KEEP ALIVE (RENDER) ----------------

app = Flask('')

@app.route('/')
def home():
    return "Bot activo"

def run():
    app.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = threading.Thread(target=run)
    t.start()

# ---------------- BASE DE DATOS ----------------

DATABASE_URL = os.environ["DATABASE_URL"]

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS boxes(
id SERIAL PRIMARY KEY,
nombre TEXT,
canal_id BIGINT,
dueno_id BIGINT,
staff_id BIGINT,
miembros TEXT,
inicio TIMESTAMP,
fin TIMESTAMP,
avisado BIGINT
)
""")

conn.commit()

# ---------------- FUNCION LOG ----------------

async def log(guild, texto):

    log_channel = bot.get_channel(LOG_CHANNEL_ID)

    if log_channel:
        embed = discord.Embed(
            description=texto,
            color=discord.Color.orange()
        )

        await log_channel.send(embed=embed)
# ---------------- BOT READY ----------------

@bot.event
async def on_ready():
    print(f"Conectado como {bot.user}")
    revisar_boxes.start()

# ---------------- CREAR BOX ----------------

@bot.command()
@commands.has_permissions(manage_channels=True)
async def box(ctx, nombre, dueno: discord.Member, *miembros: discord.Member):

    guild = ctx.guild

    inicio = datetime.now()
    fin = inicio + timedelta(days=DURACION_DIAS)

    personas = [dueno] + list(miembros)

    total = len(personas)

    if total == 1:
        tipo = "Mini"
    elif total == 2:
        tipo = "Duo"
    elif total == 3:
        tipo = "Trio"
    else:
        tipo = "Grupal"

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False)
    }

    for p in personas:
        overwrites[p] = discord.PermissionOverwrite(read_messages=True)

    overwrites[ctx.author] = discord.PermissionOverwrite(read_messages=True)

    canal = await guild.create_text_channel(nombre, overwrites=overwrites)

    miembros_ids = [m.id for m in miembros]

    cursor.execute("""
    INSERT INTO boxes(nombre,canal_id,dueno_id,staff_id,miembros,inicio,fin,avisado)
    VALUES(?,?,?,?,?,?,?,0)
    """,(nombre, canal.id, dueno.id, ctx.author.id, str(miembros_ids), inicio, fin))

    conn.commit()

    box_id = cursor.lastrowid

    embed = discord.Embed(
        title="🛏 Box creada",
        color=discord.Color.green()
    )

    embed.add_field(name="ID", value=box_id)
    embed.add_field(name="Nombre", value=nombre)
    embed.add_field(name="Tipo", value=tipo)
    embed.add_field(name="Dueño", value=dueno.mention)
    embed.add_field(name="Staff", value=ctx.author.mention)
    embed.add_field(name="Expira", value=fin.strftime("%d/%m/%Y"))

    await canal.send(embed=embed)

    await log(guild, f"📦 **BOX CREADA**\nNombre: {nombre}\nDueño: {dueno.mention}\nStaff: {ctx.author.mention}\nTipo: {tipo}")

# ---------------- VER BOXES ----------------

@bot.command()
async def boxes(ctx):

    cursor.execute("SELECT id,nombre,fin FROM boxes")
    data = cursor.fetchall()

    if not data:
        await ctx.send("No hay boxes activas")
        return

    embed = discord.Embed(title="📦 Boxes activas")

    for b in data:

        fin = datetime.strptime(b[2], "%Y-%m-%d %H:%M:%S.%f")
        dias = (fin - datetime.now()).days

        embed.add_field(
            name=f"ID {b[0]} | {b[1]}",
            value=f"Expira en {dias} días",
            inline=False
        )

    await ctx.send(embed=embed)

# ---------------- INFO BOX ----------------

@bot.command()
async def boxinfo(ctx, id_box: int):

    cursor.execute("SELECT * FROM boxes WHERE id=?", (id_box,))
    data = cursor.fetchone()

    if not data:
        await ctx.send("Box no encontrada")
        return

    guild = ctx.guild

    dueno = guild.get_member(data[3])
    staff = guild.get_member(data[4])

    embed = discord.Embed(title=f"📦 Box {data[1]}")

    embed.add_field(name="ID", value=data[0])
    embed.add_field(name="Dueño", value=dueno.mention)
    embed.add_field(name="Staff", value=staff.mention)
    embed.add_field(name="Creación", value=data[6])
    embed.add_field(name="Expira", value=data[7])

    await ctx.send(embed=embed)

# ---------------- RENOVAR ----------------

@bot.command()
@commands.has_permissions(manage_channels=True)
async def renovar(ctx, id_box: int):

    cursor.execute("SELECT fin,nombre FROM boxes WHERE id=?", (id_box,))
    data = cursor.fetchone()

    if not data:
        await ctx.send("Box no encontrada")
        return

    nueva = datetime.strptime(data[0], "%Y-%m-%d %H:%M:%S.%f") + timedelta(days=DURACION_DIAS)

    cursor.execute("UPDATE boxes SET fin=?,avisado=0 WHERE id=?", (nueva,id_box))
    conn.commit()

    await ctx.send("Box renovada")

    await log(ctx.guild, f"🔄 **BOX RENOVADA**\nBox: {data[1]}\nStaff: {ctx.author.mention}")

# ---------------- AÑADIR MIEMBRO ----------------

@bot.command()
async def addbox(ctx, id_box: int, miembro: discord.Member):

    cursor.execute("SELECT canal_id FROM boxes WHERE id=?", (id_box,))
    data = cursor.fetchone()

    canal = bot.get_channel(data[0])

    await canal.set_permissions(miembro, read_messages=True)

    await ctx.send("Miembro añadido")

# ---------------- REMOVER MIEMBRO ----------------

@bot.command()
async def removebox(ctx, id_box: int, miembro: discord.Member):

    cursor.execute("SELECT canal_id FROM boxes WHERE id=?", (id_box,))
    data = cursor.fetchone()

    canal = bot.get_channel(data[0])

    await canal.set_permissions(miembro, overwrite=None)

    await ctx.send("Miembro removido")

# ---------------- ELIMINAR BOX ----------------

@bot.command()
async def deletebox(ctx, id_box: int):

    cursor.execute("SELECT canal_id,nombre FROM boxes WHERE id=?", (id_box,))
    data = cursor.fetchone()

    canal = bot.get_channel(data[0])

    if canal:
        await canal.delete()

    cursor.execute("DELETE FROM boxes WHERE id=?", (id_box,))
    conn.commit()

    await ctx.send("Box eliminada")

# ---------------- REVISAR EXPIRACIÓN ----------------

@tasks.loop(hours=1)
async def revisar_boxes():

    ahora = datetime.now()

    cursor.execute("SELECT id,nombre,canal_id,fin,avisado FROM boxes")
    data = cursor.fetchall()

    for b in data:

        fin = datetime.strptime(b[3], "%Y-%m-%d %H:%M:%S.%f")
        restante = fin - ahora

        guild = bot.guilds[0]

        if restante.days <= 3 and b[4] == 0:

            await log(guild, f"⚠ La box **{b[1]}** vence en {restante.days} días")

            cursor.execute("UPDATE boxes SET avisado=1 WHERE id=?", (b[0],))
            conn.commit()

        if ahora >= fin:

            canal = bot.get_channel(b[2])

            if canal:
                await canal.delete()

            cursor.execute("DELETE FROM boxes WHERE id=?", (b[0],))
            conn.commit()

            await log(guild, f"⛔ Box **{b[1]}** eliminada por expiración")

# ---------------- START ----------------

keep_alive()
bot.run(TOKEN)