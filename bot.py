import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import os
from flask import Flask
from threading import Thread

# -----------------------
# SERVIDOR WEB (Render)
# -----------------------

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot Nuevo León RP activo ✅"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    Thread(target=run_web).start()

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
        pais TEXT
    )
    """)

    conn.commit()
    conn.close()

# -----------------------
# CONFIG BOT
# -----------------------

intents = discord.Intents.default()
intents.message_content = True

class NuevoLeonBot(commands.Bot):

    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents
        )

    async def setup_hook(self):
        try:
            await self.tree.sync()
            print("✅ Comandos sincronizados")
        except Exception as e:
            print(f"❌ Error sincronizando comandos: {e}")

bot = NuevoLeonBot()

# -----------------------
# EVENTOS
# -----------------------

@bot.event
async def on_ready():
    print("--------------")
    print(f"BOT ONLINE: {bot.user}")
    print("--------------")

    await bot.change_presence(
        activity=discord.Game("Nuevo León RP 🤠")
    )

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

    try:
        cursor.execute(
            "INSERT INTO ines VALUES (?, ?, ?, ?, ?)",
            (user_id, nombre, edad, nacimiento, pais)
        )

        conn.commit()
        return True

    except sqlite3.IntegrityError:
        return False

    finally:
        conn.close()

# -----------------------
# COMANDOS
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
            f"✅ INE registrada para **{interaction.user.display_name}**"
        )

    else:

        await interaction.response.send_message(
            "⚠️ Ya tienes una INE registrada.",
            ephemeral=True
        )


@bot.tree.command(
    name="ver-ine",
    description="Muestra tu INE"
)
async def ver_ine(interaction: discord.Interaction):

    user_id = str(interaction.user.id)
    datos = obtener_ine(user_id)

    if datos:

        embed = discord.Embed(
            title="📇 INE - Nuevo León RP",
            color=0x1a73e8
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
            value=f"{datos[2]} años",
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

        await interaction.response.send_message(
            embed=embed
        )

    else:

        await interaction.response.send_message(
            "❌ No tienes INE registrada.",
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
