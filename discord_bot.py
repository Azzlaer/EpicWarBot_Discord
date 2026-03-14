import discord
from discord.ext import commands
import yaml
from downloader import download_epicwar
from database import save_map

with open("config.yml", "r", encoding="utf-8") as f:
    CONFIG = yaml.safe_load(f)

TOKEN = CONFIG["discord"]["token"]

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print("Bot conectado:", bot.user)


@bot.event
async def on_message(message):

    if message.author.bot:
        return

    if "epicwar.com/maps/" in message.content:

        msg = await message.reply("⬇️ Descargando mapa...")

        try:

            name, size = download_epicwar(message.content)

            save_map(
                str(message.author),
                name,
                name,
                message.content,
                size
            )

            await msg.edit(
                content=f"✅ Mapa descargado\n📁 {name}"
            )

        except Exception as e:

            await msg.edit(
                content=f"❌ Error: {e}"
            )

    await bot.process_commands(message)


def start_bot():
    bot.run(TOKEN)