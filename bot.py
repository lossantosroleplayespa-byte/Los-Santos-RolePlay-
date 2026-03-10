import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import os
from flask import Flask
from threading import Thread

# 1. SERVIDOR WEB (Mantiene el bot vivo en Render)
app = Flask('')

@app.route('/')
def home():
    return "Servidor de Nuevo León RP Encendido"

def run_web():
    # Render usa el puerto 10000 por defecto
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# 2. CONFIGURACIÓN DEL BOT DE DISCORD
# Activamos todos los permisos para que no haya errores de conexión
intents = discord.Intents.all()

class NuevoLeonBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Sincroniza los comandos / con Discord
        try:
            synced = await self.tree.sync()
            print(f"✅ {len(synced)} comandos sincronizados correctamente")
        except Exception as e:
            print(f"❌ Error al sincronizar comandos: {e}")

bot = NuevoLeonBot()

# 3. BASE DE DATOS (Sistema de INEs)
def init_db():
    conn = sqlite3.connect('nuevoleon_rp.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS ines 
                     (user_id TEXT PRIMARY KEY, nombre TEXT, edad INTEGER, nacimiento TEXT, pais TEXT)''')
    conn.commit()
    conn.close()

# 4. EVENTOS Y COMANDOS
@bot.event
async def on_ready():
    print(f'---')
    print(f'✅ BOT CONECTADO: {bot.user.name}')
    print(f'✅ ID: {bot.user.id}')
    print(f'---')
    # Cambia el estado del bot en Discord
    await bot.change_presence(activity=discord.Game(name="Nuevo León RP 🤠"))

@bot.tree.command(name="crear-ine", description="Registra tu identificación oficial")
async def crear_ine(interaction: discord.Interaction, nombre: str, edad: int, nacimiento: str, pais: str):
    conn = sqlite3.connect('nuevoleon_rp.db')
    cursor = conn.cursor()
    user_id = str(interaction.user.id)
    try:
        cursor.execute("INSERT INTO ines VALUES (?, ?, ?, ?, ?)", (user_id, nombre, edad, nacimiento, pais))
        conn.commit()
        await interaction.response.send_message(f"✅ **{interaction.user.display_name}**, tu INE ha sido registrada.")
    except sqlite3.IntegrityError:
        await interaction.response.send_message("⚠️ Ya tienes una INE registrada. Usa `/ver-ine`.", ephemeral=True)
    finally:
        conn.close()

@bot.tree.command(name="ver-ine", description="Muestra tu INE actual")
async def ver_ine(interaction: discord.Interaction):
    conn = sqlite3.connect('nuevoleon_rp.db')
    cursor = conn.cursor()
    user_id = str(interaction.user.id)
    cursor.execute("SELECT * FROM ines WHERE user_id=?", (user_id,))
    datos = cursor.fetchone()
    conn.close()

    if datos:
        embed = discord.Embed(title="📇 IDENTIFICACIÓN OFICIAL - NUEVO LEÓN RP", color=0x008000)
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.add_field(name="👤 Nombre Completo", value=datos[1], inline=False)
        embed.add_field(name="🎂 Edad", value=f"{datos[2]} años", inline=True)
        embed.add_field(name="📅 Fecha de Nac.", value=datos[3], inline=True)
        embed.add_field(name="🌎 Nacionalidad", value=datos[4], inline=False)
        embed.set_footer(text="Estado de Nuevo León - Sistema de Registro")
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("❌ No tienes una INE. Tramítala con `/crear-ine`.", ephemeral=True)

# 5. ARRANQUE DEL SISTEMA
if __name__ == "__main__":
    init_db()
    # Iniciamos el servidor web en un hilo secundario
    web_thread = Thread(target=run_web)
    web_thread.start()
    
    # Iniciamos el bot de Discord (Usa el token de las variables de entorno de Render)
    token = os.getenv('DISCORD_TOKEN')
    if token:
        try:
            bot.run(token)
        except Exception as e:
            print(f"❌ Error crítico de inicio: {e}")
    else:
        print("❌ ERROR: No se encontró DISCORD_TOKEN en Render -> Environment")
