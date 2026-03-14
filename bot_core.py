import discord
from discord.ext import commands
import yaml
import asyncio
import time

from downloader import download_epicwar, progress_bar
from database import save_map, map_hash_exists

# =========================
# CONFIG
# =========================

with open("config.yml", "r", encoding="utf-8") as f:
    CONFIG = yaml.safe_load(f)

TOKEN = CONFIG["discord"]["token"]
CHANNEL_NAME = CONFIG["discord"]["channel_name"]
BOT_NAME = CONFIG["ui"]["bot_name"]

# =========================
# DISCORD BOT
# =========================

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# =========================
# ESTADOS
# =========================

download_queue = asyncio.Queue()
user_states = {}

STATE_WAIT_MAP = "WAIT_MAP"

# =========================
# PANEL CONTROL
# =========================

last_panel_message = None
panel_lock = asyncio.Lock()


class MainPanel(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Subir mapa", emoji="🗺️", style=discord.ButtonStyle.primary)
    async def upload(self, interaction, button):

        user_states[interaction.user.id] = STATE_WAIT_MAP

        await interaction.response.send_message(
            "📎 Envía el enlace de EpicWar",
            ephemeral=True
        )


# =========================
# PANEL MANAGEMENT
# =========================

async def send_panel(channel):

    global last_panel_message

    async with panel_lock:

        try:
            if last_panel_message:
                await last_panel_message.delete()
        except:
            pass

        msg = await channel.send(
            f"📢 **Panel de mapas – {BOT_NAME}**",
            view=MainPanel()
        )

        last_panel_message = msg


# =========================
# MENSAJES
# =========================

@bot.event
async def on_message(message):

    if message.author.bot:
        return

    uid = message.author.id

    if user_states.get(uid) == STATE_WAIT_MAP:

        await message.reply("📥 Mapa agregado a la cola de descarga")

        await download_queue.put((message.author, message.content, message.channel))

        user_states[uid] = None

    await bot.process_commands(message)


# =========================
# WORKER DESCARGAS
# =========================

async def download_worker():

    await bot.wait_until_ready()

    while not bot.is_closed():

        user, url, channel = await download_queue.get()

        await channel.send("⬇️ Iniciando descarga...")

        last_update = 0

        def progress(percent, downloaded, total, speed, eta):

            nonlocal last_update

            now = time.time()

            if now - last_update < 5:
                return

            last_update = now

            bar = progress_bar(percent)

            text = f"""
⬇️ Descargando mapa

{bar} {percent}%

📦 {downloaded/1024/1024:.1f} MB / {total/1024/1024:.1f} MB
⚡ {speed/1024/1024:.2f} MB/s
⏳ ETA: {int(eta)}s
"""

            bot.loop.create_task(channel.send(text))

        try:

            name, size, file_hash = download_epicwar(url, progress)

            if map_hash_exists(file_hash):

                await channel.send(
                    f"⚠️ Este mapa ya existe\n📁 {name}"
                )

            else:

                save_map(str(user), name, name, url, size, file_hash)

                await channel.send(
                    f"✅ Descarga completada\n📁 {name}"
                )

        except Exception as e:

            await channel.send(f"❌ Error: {e}")

        # volver a mostrar panel
        await send_panel(channel)

        download_queue.task_done()


# =========================
# BOT READY
# =========================

@bot.event
async def on_ready():

    print("Bot conectado:", bot.user)

    bot.loop.create_task(download_worker())

    for guild in bot.guilds:
        for channel in guild.text_channels:

            if channel.name == CHANNEL_NAME:

                await send_panel(channel)


# =========================
# START / STOP
# =========================

def start_bot():
    bot.run(TOKEN)


def stop_bot():
    asyncio.run_coroutine_threadsafe(bot.close(), bot.loop)