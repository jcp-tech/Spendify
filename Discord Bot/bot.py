"""
# PIP's
pip install -U discord.py
pip install python-dotenv
"""

import os, uuid
from dotenv import load_dotenv
import discord
from discord.ext import commands
load_dotenv()

token = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user} (ID: {bot.user.id})')

@bot.command()
async def hello(ctx):
    await ctx.send("Hello there!")

### <Message id=1375158437746442272 channel=<Thread id=1375152189630185513 name='@Spendify Practice Thread!' parent=aig-200-capstone owner_id=686190428634349751 locked=False archived=False> type=<MessageType.default: 0> author=<Member id=686190428634349751 name='jcp99gamer' global_name='Jonathan Chacko' bot=False nick='Dead Ketchup' guild=<Guild id=730471027905134712 name='Maple Masala' shard_id=0 chunked=True member_count=4>> flags=<MessageFlags value=0>>
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # If message has attachments (e.g. image)
    if message.attachments:
        for attachment in message.attachments:
            if attachment.content_type.startswith("image/"):
                session_id = str(uuid.uuid4())
                file_extension = attachment.filename.split('.')[-1]
                file_name = f"{session_id}.{file_extension}"
                file_path = os.path.join(os.getcwd(), file_name)

                await attachment.save(file_path)

                print(f"[📸] Image saved as: {file_name}")
                print(f"[👤] Uploaded by: {message.author.name}")
                # print(message)

    await bot.process_commands(message)

# Run the bot (replace with your token)
bot.run(token)