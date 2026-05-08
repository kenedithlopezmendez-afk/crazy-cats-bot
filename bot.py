from flask import Flask
from threading import Thread
# -------- DETECTOR DE SALAS --------

CANAL_AVENTURAS = 1502421010274844762
ROL_AVENTURA = 1502421341394042880

@bot.event
async def on_message(message):

    # Ignorar mensajes del propio bot
    if message.author == bot.user:
        return

    # Solo detectar mensajes de otros bots
    if message.author.bot:

        contenido = message.content.lower()

        salas = {
            "magma": {
                "titulo": "🌋 Sala de Magma Detectada",
                "descripcion": "¡Prepara tus mascotas y entra en la zona de magma!",
                "color": 0xFF5500
            },

            "outlands": {
                "titulo": "🏝 Sala de Outlands Detectada",
                "descripcion": "¡Una aventura de Outlands ha aparecido!",
                "color": 0x00AAFF
            },

            "whispering": {
                "titulo": "🌲 Sala de Whispering Detectada",
                "descripcion": "¡El bosque susurra... aventura disponible!",
                "color": 0x55FF55
            }
        }

        for palabra, datos in salas.items():

            if palabra in contenido:

                canal = bot.get_channel(CANAL_AVENTURAS)

                embed = discord.Embed(
                    title=datos["titulo"],
                    description=datos["descripcion"],
                    color=datos["color"]
                )

                embed.add_field(
                    name="📍 Detectado en",
                    value=message.channel.mention,
                    inline=False
                )

                embed.set_footer(
                    text="Sistema de Detección"
                )

                await canal.send(
                    f"<@&{ROL_AVENTURA}>",
                    embed=embed
                )

                break

    await bot.process_commands(message)
    keep_alive()
    bot.run(TOKEN)