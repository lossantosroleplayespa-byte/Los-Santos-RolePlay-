import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import os
from flask import Flask
from threading import Thread

# 1. SERVIDOR WEB PARA RENDER (Engañamos al sistema para que no se apague)
app = Flask('')

@app.route('/')
def home():
    return "Bot de Nuevo León RP Activo"

def run():
    # Render asigna un puerto automáticamente, aquí lo leemos
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# 2. CONFIGURACIÓN DEL BOT
class NuevoLeonBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print(f"✅ Comandos sincronizados en Discord")

bot = NuevoLeonBot()

# 3. BASE DE DATOS (INEs)
conn = sqlite3.connect('nuevoleon_rp.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS ines 
                 (user_id TEXT PRIMARY KEY, nombre TEXT, edad INTEGER, nacimiento TEXT, pais TEXT)''')
conn.commit()

# 4. COMANDOS DE ROL
@bot.tree.command(name="crear-ine", description="Tramita tu INE de Nuevo León RP")
async def crear_ine(interaction: discord.Interaction, nombre: str, edad: int, nacimiento: str, pais: str):
    user_id = str(interaction.user.id)
    try:
        cursor.execute("INSERT INTO ines VALUES (?, ?, ?, ?, ?)", (user_id, nombre, edad, nacimiento, pais))
        conn.commit()
        await interaction.response.send_message(f"✅ **{interaction.user.display_name}**, tu INE ha sido registrada.")
    except sqlite3.IntegrityError:
        await interaction.response.send_message("⚠️ Ya tienes una INE registrada.", ephemeral=True)

@bot.tree.command(name="ver-ine", description="Muestra tu INE")
async def ver_ine(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    cursor.execute("SELECT * FROM ines WHERE user_id=?", (user_id,))
    datos = cursor.fetchone()
    if datos:
        embed = discord.Embed(title="📇 INE - NUEVO LEÓN RP", color=0x004c99)
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.add_field(name="👤 Nombre", value=datos[1], inline=False)
        embed.add_field(name="🎂 Edad", value=f"{datos[2]} años", inline=True)
        embed.add_field(name="📅 Nacimiento", value=datos[3], inline=True)
        embed.add_field(name="🌎 País", value=datos[4], inline=False)
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("❌ No tienes INE. Usa `/crear-ine`.", ephemeral=True)

@bot.tree.command(name="eliminar-ine", description="Borra tu INE")
async def eliminar_ine(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    cursor.execute("DELETE FROM ines WHERE user_id=?", (user_id,))
    conn.commit()
    await interaction.response.send_message("🗑️ Registro eliminado.", ephemeral=True)

# 5. ARRANQUE
if __name__ == "__main__":
    keep_alive() # Inicia el servidor web
    token = os.getenv('DISCORD_TOKEN') # Lee el token de Render
    if token:
        bot.run(token)
    else:
        print("❌ ERROR: No se encontró la variable DISCORD_TOKEN en Render")

