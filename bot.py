print("EL BOT ESTA ARRANCANDO")

import discord
from discord.ext import commands
import sqlite3
import os
import random
from flask import Flask
from threading import Thread

# -----------------------
# SERVIDOR WEB (para Render)
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
# BOT CONFIG
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

    await bot.change_presence(
        activity=discord.Game("Nuevo León RP")
    )

# -----------------------
# DB FUNCIONES
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

# -----------------------
# COMANDO CREAR INE
# -----------------------

@bot.tree.command(
    name="crear-ine",
    description="Tramita tu INE"
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

        await interaction.response.send_message(
            f"✅ INE registrada para {interaction.user.display_name}"
        )

    else:

        await interaction.response.send_message(
            "⚠️ Ya tienes una INE registrada.",
            ephemeral=True
        )

# -----------------------
# COMANDO VER INE
# -----------------------

@bot.tree.command(
    name="ver-ine",
    description="Muestra tu INE"
)
async def ver_ine(interaction: discord.Interaction):

    user_id = str(interaction.user.id)
    datos = obtener_ine(user_id)

    if datos:

        embed = discord.Embed(
            title="🪪 Instituto Nacional Electoral",
            description="Credencial de Identificación • Nuevo León RP",
            color=0x006847
        )

        embed.set_thumbnail(
            url=interaction.user.display_avatar.url
        )

        embed.add_field(
            name="Nombre",
            value=datos[1],
            inline=False
        )

        embed.add_field(
            name="Edad",
            value=str(datos[2]),
            inline=True
        )

        embed.add_field(
            name="Nacimiento",
            value=datos[3],
            inline=True
        )

        embed.add_field(
            name="País",
            value=datos[4],
            inline=False
        )

        embed.add_field(
            name="ID INE",
            value=datos[5],
            inline=True
        )

        embed.add_field(
            name="CURP",
            value=datos[6],
            inline=True
        )

        embed.set_footer(
            text="Gobierno de Nuevo León RP"
        )

        await interaction.response.send_message(
            embed=embed
        )

    else:

        await interaction.response.send_message(
            "❌ No tienes INE registrada",
            ephemeral=True
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
