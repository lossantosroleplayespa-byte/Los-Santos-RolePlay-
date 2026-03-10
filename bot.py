import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import os
from flask import Flask
from threading import Thread

# 1. SERVIDOR WEB DE MENTIRA (Para que Render no apague el bot)
app = Flask('')

@app.route('/')
def home():
    return "El servidor de Nuevo León RP está activo."

def run():
    # Render usa el puerto 10000 por defecto en servicios web
    app.run(host='0.0.0.0', port=10000)

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
        print(f"✅ Comandos sincronizados")

bot = NuevoLeonBot()

# 3. BASE DE DATOS
conn = sqlite3.connect('nuevoleon_rp.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS ines 
                 (user_id TEXT PRIMARY KEY, nombre TEXT, edad INTEGER, nacimiento TEXT, pais TEXT)''')
conn.commit()

# 4. COMANDOS
@bot.tree.command(name="crear-ine", description="Tramita tu INE de Nuevo León RP")
async def crear_ine(interaction: discord.Interaction, nombre: str, edad: int, nacimiento: str, pais: str):
    user_id = str(interaction.user.id)
    try:
        cursor.execute("INSERT INTO ines VALUES (?, ?, ?, ?, ?)", (user_id, nombre, edad, nacimiento, pais))
        conn.commit()
        await interaction.response.send_message(f"✅ **{interaction.user.display_name}**, tu INE ha sido registrada.")
    except sqlite3.IntegrityError:
        await interaction.response.send_message("⚠️ Ya tienes una INE. Usa `/eliminar-ine`.", ephemeral=True)

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
        await interaction.response.send_message("❌ No tienes INE.", ephemeral=True)

@bot.tree.command(name="eliminar-ine", description="Borra tu INE")
async def eliminar_ine(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    cursor.execute("DELETE FROM ines WHERE user_id=?", (user_id,))
    conn.commit()
    await interaction.response.send_message("🗑️ INE eliminada.", ephemeral=True)

# 5. ENCENDIDO
if __name__ == "__main__":
    keep_alive() # Esto arranca la "página web" de mentira
    token = os.getenv('DISCORD_TOKEN')
    bot.run(token)
 
