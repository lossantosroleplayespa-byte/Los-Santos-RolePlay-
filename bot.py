print("EL BOT ESTA ARRANCANDO")

import discord
from discord.ext import commands
import sqlite3
import os
import random
from flask import Flask
from threading import Thread

from PIL import Image, ImageDraw
import requests
from io import BytesIO

# -----------------------
# SERVIDOR WEB (Render)
# -----------------------

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot Nuevo León RP activo"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run_web)
    t.daemon = True
    t.start()

# -----------------------
# BASE DE DATOS
# -----------------------

def init_db():

    conn = sqlite3.connect("nuevoleon_rp.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ines (
        user_id TEXT PRIMARY KEY,
        nombre TEXT,
        edad INTEGER,
        nacimiento TEXT,
        pais TEXT,
        ine_id TEXT,
        curp TEXT
    )
    """)

    conn.commit()
    conn.close()

# -----------------------
# GENERADORES
# -----------------------

def generar_ine_id():
    return f"NL-{random.randint(100000,999999)}"

def generar_curp(nombre, nacimiento):

    inicial = nombre[0].upper()
    fecha = nacimiento.replace("-", "")

    letras = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    extra = "".join(random.choice(letras) for _ in range(3))

    return f"{inicial}{fecha}{extra}"

# -----------------------
# GENERAR IMAGEN INE
# -----------------------

def generar_ine_imagen(usuario, datos):

    img = Image.new("RGB", (600,350), (255,255,255))
    draw = ImageDraw.Draw(img)

    draw.text((20,20),"INSTITUTO NACIONAL ELECTORAL",(0,120,0))

    response = requests.get(usuario.display_avatar.url)
    avatar = Image.open(BytesIO(response.content))
    avatar = avatar.resize((120,120))

    img.paste(avatar,(20,80))

    draw.text((180,80),f"Nombre: {datos[1]}",(0,0,0))
    draw.text((180,110),f"Edad: {datos[2]}",(0,0,0))
    draw.text((180,140),f"Nacimiento: {datos[3]}",(0,0,0))
    draw.text((180,170),f"Pais: {datos[4]}",(0,0,0))
    draw.text((180,200),f"ID: {datos[5]}",(0,0,0))
    draw.text((180,230),f"CURP: {datos[6]}",(0,0,0))

    ruta = f"ine_{usuario.id}.png"
    img.save(ruta)

    return ruta

# -----------------------
# CONFIG BOT
# -----------------------

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

# -----------------------
# EVENTO READY
# -----------------------

@bot.event
async def on_ready():

    print("-------------------")
    print(f"BOT ONLINE: {bot.user}")
    print("-------------------")

    try:
        synced = await bot.tree.sync()
        print(f"Comandos sincronizados: {len(synced)}")
    except Exception as e:
        print(e)

# -----------------------
# FUNCIONES DB
# -----------------------

def obtener_ine(user_id):

    conn = sqlite3.connect("nuevoleon_rp.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM ines WHERE user_id=?",
        (user_id,)
    )

    datos = cursor.fetchone()
    conn.close()

    return datos


def crear_ine_db(user_id, nombre, edad, nacimiento, pais):

    conn = sqlite3.connect("nuevoleon_rp.db")
    cursor = conn.cursor()

    ine_id = generar_ine_id()
    curp = generar_curp(nombre, nacimiento)

    try:

        cursor.execute(
            "INSERT INTO ines VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, nombre, edad, nacimiento, pais, ine_id, curp)
        )

        conn.commit()
        return True

    except sqlite3.IntegrityError:
        return False

    finally:
        conn.close()


def eliminar_ine_db(user_id):

    conn = sqlite3.connect("nuevoleon_rp.db")
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM ines WHERE user_id=?",
        (user_id,)
    )

    conn.commit()
    conn.close()

# -----------------------
# CREAR INE
# -----------------------

@bot.tree.command(
    name="crear-ine",
    description="Registrar tu INE"
)
async def crear_ine(
    interaction: discord.Interaction,
    nombre: str,
    edad: int,
    nacimiento: str,
    pais: str
):

    user_id = str(interaction.user.id)

    creada = crear_ine_db(
        user_id,
        nombre,
        edad,
        nacimiento,
        pais
    )

    if creada:

        datos = obtener_ine(user_id)

        embed = discord.Embed(
            title="🪪 INE registrada",
            description="Tu credencial fue registrada en el sistema.",
            color=0x2ecc71
        )

        embed.add_field(name="Nombre", value=datos[1])
        embed.add_field(name="ID", value=datos[5])
        embed.add_field(name="CURP", value=datos[6])

        await interaction.response.send_message(embed=embed)

    else:

        await interaction.response.send_message(
            "⚠️ Ya tienes una INE registrada.",
            ephemeral=True
        )

# -----------------------
# VER INE
# -----------------------

@bot.tree.command(
    name="ver-ine",
    description="Mostrar tu INE"
)
async def ver_ine(interaction: discord.Interaction):

    user_id = str(interaction.user.id)
    datos = obtener_ine(user_id)

    if datos:

        archivo = generar_ine_imagen(interaction.user, datos)

        await interaction.response.send_message(
            file=discord.File(archivo)
        )

    else:

        await interaction.response.send_message(
            "❌ No tienes INE registrada",
            ephemeral=True
        )

# -----------------------
# ELIMINAR INE
# -----------------------

@bot.tree.command(
    name="eliminar-ine",
    description="Eliminar tu INE"
)
async def eliminar_ine(interaction: discord.Interaction):

    user_id = str(interaction.user.id)

    datos = obtener_ine(user_id)

    if not datos:

        await interaction.response.send_message(
            "❌ No tienes INE registrada",
            ephemeral=True
        )
        return

    eliminar_ine_db(user_id)

    await interaction.response.send_message(
        "🗑️ Tu INE fue eliminada del sistema."
    )

# -----------------------
# ARRANQUE
# -----------------------

if __name__ == "__main__":

    init_db()
    keep_alive()

    token = os.getenv("DISCORD_TOKEN")

    if not token:
        print("❌ No existe DISCORD_TOKEN")
    else:
        bot.run(token)
