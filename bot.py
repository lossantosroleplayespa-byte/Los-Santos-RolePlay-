import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import os
from flask import Flask
from threading import Thread

# 1. SERVIDOR WEB (Para que Render no dé error de puerto)
app = Flask('')

@app.route('/')
def home():
    return "Bot de Nuevo León RP Online ✅"

def run_web():
    # Usamos el puerto 10000 que es el que Render exige
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web)
    t.daemon = True
    t.start()

# 2. CONFIGURACIÓN DEL BOT
intents = discord.Intents.all()

class NuevoLeonBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Sincroniza los comandos de barra (/)
        try:
            await self.tree.sync()
            print("✅ Comandos de barra sincronizados")
        except Exception as e:
            print(f"❌ Error al sincronizar: {e}")

bot = NuevoLeonBot()

# 3. BASE DE DATOS (Sistema de INE)
def init_db():
    conn = sqlite3.connect('nuevoleon_rp.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS ines 
                     (user_id TEXT PRIMARY KEY, nombre TEXT, edad INTEGER, nacimiento TEXT, pais TEXT)''')
    conn.commit()
    conn.close()

# 4. EVENTOS
@bot.event
async def on_ready():
    print(f'---')
    print(f'✅ BOT CONECTADO: {bot.user.name}')
    print(f'---')
    await bot.change_presence(activity=discord.Game(name="Nuevo León RP 🤠"))

# 5. COMANDOS (/)
@bot.tree.command(name="crear-ine", description="Tramita tu INE de Nuevo León RP")
async def crear_ine(interaction: discord.Interaction, nombre: str, edad: int, nacimiento: str, pais: str):
    conn = sqlite3.connect('nuevoleon_rp.db')
    cursor = conn.cursor()
    user_id = str(interaction.user.id)
    try:
        cursor.execute("INSERT INTO ines VALUES (?, ?, ?, ?, ?)", (user_id, nombre, edad, nacimiento, pais))
        conn.commit()
        await interaction.response.send_message(f"✅ **{interaction.user.display_name}**, tu INE ha sido registrada.")
    except sqlite3.IntegrityError:
        await interaction.response.send_message("⚠️ Ya tienes una INE registrada.", ephemeral=True)
    finally:
        conn.close()

@bot.tree.command(name="ver-ine", description="Muestra tu identificación")
async def ver_ine(interaction: discord.Interaction):
    conn = sqlite3.connect('nuevoleon_rp.db')
    cursor = conn.cursor()
    user_id = str(interaction.user.id)
    cursor.execute("SELECT * FROM ines WHERE user_id=?", (user_id,))
    datos = cursor.fetchone()
    conn.close()

    if datos:
        embed = discord.Embed(title="📇 INE - NUEVO LEÓN RP", color=0x1a73e8)
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.add_field(name="👤 Nombre", value=datos[1], inline=False)
        embed.add_field(name="🎂 Edad", value=f"{datos[2]} años", inline=True)
        embed.add_field(name="📅 Nacimiento", value=datos[3], inline=True)
        embed.add_field(name="🌎 País", value=datos[4], inline=False)
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("❌ No tienes INE registrada.", ephemeral=True)

# 6. ARRANQUE
if __name__ == "__main__":
    init_db()
    keep_alive() # Arranca Flask PRIMERO
    
    token = os.getenv('DISCORD_TOKEN')
    if token:
        try:
            bot.run(token)
        except Exception as e:
            print(f"❌ Error de inicio: {e}")
    else:
        print("❌ ERROR: No se encontró la variable DISCORD_TOKEN en Render")
