import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import os

# Configuración del Bot para Nuevo León RP
class NuevoLeonBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Esto sincroniza los comandos / para que aparezcan en Discord
        await self.tree.sync()
        print(f"✅ Comandos sincronizados para {self.user}")

bot = NuevoLeonBot()

# Conectar a la base de datos (se crea sola)
conn = sqlite3.connect('nuevoleon_rp.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS ines 
                 (user_id TEXT PRIMARY KEY, nombre TEXT, edad INTEGER, nacimiento TEXT, pais TEXT)''')
conn.commit()

# 1. COMANDO: /crear-ine
@bot.tree.command(name="crear-ine", description="Tramita tu INE de Nuevo León RP")
@app_commands.describe(nombre="Tu nombre completo", edad="Tu edad", nacimiento="Día/Mes/Año", pais="Tu país")
async def crear_ine(interaction: discord.Interaction, nombre: str, edad: int, nacimiento: str, pais: str):
    user_id = str(interaction.user.id)
    try:
        cursor.execute("INSERT INTO ines VALUES (?, ?, ?, ?, ?)", 
                       (user_id, nombre, edad, nacimiento, pais))
        conn.commit()
        await interaction.response.send_message(f"✅ **{interaction.user.display_name}**, tu INE ha sido registrada con éxito.")
    except sqlite3.IntegrityError:
        await interaction.response.send_message("⚠️ Ya tienes una INE registrada. Usa `/eliminar-ine` para borrarla.", ephemeral=True)

# 2. COMANDO: /ver-ine
@bot.tree.command(name="ver-ine", description="Muestra tu INE de Nuevo León RP")
async def ver_ine(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    cursor.execute("SELECT * FROM ines WHERE user_id=?", (user_id,))
    datos = cursor.fetchone()

    if datos:
        embed = discord.Embed(
            title="📇 INE - NUEVO LEÓN RP", 
            description="Documento oficial de identidad",
            color=0x004c99
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.add_field(name="👤 Nombre", value=datos[1], inline=False)
        embed.add_field(name="🎂 Edad", value=f"{datos[2]} años", inline=True)
        embed.add_field(name="📅 Fecha de Nacimiento", value=datos[3], inline=True)
        embed.add_field(name="🌎 País", value=datos[4], inline=False)
        embed.set_footer(text="Estado de Nuevo León | Trámite de INE")
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("❌ No tienes una INE registrada. Usa `/crear-ine`.", ephemeral=True)

# 3. COMANDO: /eliminar-ine
@bot.tree.command(name="eliminar-ine", description="Elimina tu registro de INE")
async def eliminar_ine(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    cursor.execute("DELETE FROM ines WHERE user_id=?", (user_id,))
    conn.commit()
    await interaction.response.send_message("🗑️ Tu INE ha sido eliminada del sistema de Nuevo León RP.", ephemeral=True)

# Esto lee el token desde las variables de Koyeb
token = os.getenv('DISCORD_TOKEN')
bot.run(token)

