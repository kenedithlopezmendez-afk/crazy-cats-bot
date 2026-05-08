# --- CONFIGURACIÓN DE ROLES Y CANALES ---
# Sustituye estos números por los IDs reales de tu servidor
CONFIG_AVENTURAS = {
    "Canto de las Hadas": {
        "rol_id": 1502422568408322181,  # ID del rol para Hadas
        "canal_id": 1502420350519087154, # ID del canal donde avisará Hadas
        "imagen": "https://cdn.nekotina.com/res/zones/adventure/whispering-grove.gif",
        "color": discord.Color.purple()
    },
    "Magma": {
        "rol_id": 1502421341394042880,  # ID del rol para Magma (@Adventure quizá?)
        "canal_id": 1502421010274844762, # ID del canal de salas de aventura
        "imagen": "https://cdn.nekotina.com/res/zones/adventure/magma.gif",
        "color": discord.Color.red()
    }
}

@bot.event
async def on_message(message):
    if message.author.id == NEKOTINA_ID and message.embeds:
        embed_neko = message.embeds[0]
        contenido = ""
        if embed_neko.title: contenido += embed_neko.title
        if embed_neko.description: contenido += embed_neko.description

        # Recorremos nuestra configuración
        for nombre_sala, datos in CONFIG_AVENTURAS.items():
            if nombre_sala in contenido:
                # 1. Buscamos el canal específico donde el bot debe enviar el aviso
                canal_destino = bot.get_channel(datos["canal_id"])
                
                if canal_destino:
                    # 2. Creamos el embed personalizado
                    nuevo_embed = discord.Embed(
                        title=f"✨ {nombre_sala} Detectada",
                        description=f"**Aventura Disponible**\n¡Prepara tus mascotas!",
                        color=datos["color"]
                    )
                    nuevo_embed.set_thumbnail(url=datos["imagen"])
                    nuevo_embed.set_footer(text="Latin Empire • Sistema de Detección")

                    # 3. Enviamos el ping al rol correcto y el embed al canal correcto
                    await canal_destino.send(
                        content=f"<@&{datos['rol_id']}>", 
                        embed=nuevo_embed
                    )
                break # Deja de buscar si ya encontró la sala

    await bot.process_commands(message)

bot.run(TOKEN)