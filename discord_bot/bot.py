import os, uuid
import requests
from dotenv import load_dotenv
import discord
from discord.ext import commands
from datetime import datetime
import asyncio
from functools import partial

load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
API_BASE = os.getenv('API_URL', 'http://127.0.0.1:5000')
OPTIMISE = os.getenv('OPTIMISE', 'True') # This isnt used anymore.
COMMAND_PREFIX = os.getenv('DISCORD_COMMAND_PREFIX', '!')

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)

def get_user_data(primary_id):
    """Fetch user data from the API for a given primary_id."""
    try:
        r = requests.get(f"{API_BASE}/get_user", params={'primary_id': primary_id})
        if r.ok:
            return r.json()
    except Exception:
        pass
    return None

async def ensure_authenticated(ctx, primary):
    """Ensure the user has completed OAuth login."""
    max_attempts = 5  # Prevent infinite loops
    attempt = 0
    # interval = 30  # Check every 30 seconds
    while attempt < max_attempts:
        try:
            user_doc = get_user_data(primary)
            if user_doc:
                if 'auth' in user_doc:
                    if attempt > 0:  # Only show success message if we had to wait
                        await ctx.channel.send("✅ Authentication successful! You can now upload receipts.")
                    return True
                
                # Update session_id from user document (like in Tkinter)
                session_id = user_doc.get('session_id')
            else:
                await ctx.channel.send("❌ Failed to verify authentication.")
                return False
                
        except Exception:
            await ctx.channel.send("❌ Error checking authentication status.")
            return False
        
        # Generate login link
        login_link = f"{API_BASE}/login/TRUE/{session_id}"
        
        if attempt == 0:
            # First attempt - send login link
            try:
                await ctx.author.send(f"❗ Please [Login Here]({login_link}) to authenticate before sending receipts.")
                await ctx.channel.send("🔐 Please check your DM for the login link to complete authentication.")
                await ctx.channel.send("I'll check every 30 seconds for the next 2.5 minutes. Reply 'check' to check immediately.")
            except discord.Forbidden:
                await ctx.channel.send(f"🔐 Please complete authentication: {login_link}")
                await ctx.channel.send("I'll check every 30 seconds for the next 2.5 minutes. Reply 'check' to check immediately.")
        
        # Wait for either timeout or user message
        def check_message(m):
            return (m.author == ctx.author and 
                   m.channel == ctx.channel and 
                   m.content.lower() in ['check', 'done', 'ready'])
        
        try:
            # Wait for either 30 seconds or user message
            await asyncio.wait_for(
                bot.wait_for('message', check=check_message), 
                timeout=30.0
            )
            await ctx.channel.send("🔍 Checking authentication status...")
        except asyncio.TimeoutError:
            # Auto-check after 30 seconds
            await ctx.channel.send(f"🔍 Auto-checking authentication... (Attempt {attempt + 1}/{max_attempts})")
        
        attempt += 1
    
    # Max attempts reached
    await ctx.channel.send("⏰ Authentication timeout reached. Please use the `!auth` command to try again.")
    return False

async def ensure_registered(ctx):
    identifier = ctx.author.name

    # Check if user exists
    try:
        r = requests.get(f"{API_BASE}/get_primary", params={
            'source': 'DISCORD',
            'identifier': identifier
        })
        if r.status_code == 200:
            return r.json().get('primary_id')
    except:
        await ctx.channel.send("❗ Registration check failed.")

    # If not registered
    await ctx.channel.send("You are not registered. Would you like to register now? (yes/no)")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        msg = await bot.wait_for('message', check=check, timeout=60)
        if not msg.content.lower().startswith('y'):
            await ctx.channel.send("Cannot process without registration. Please register later.")
            return None
    except asyncio.TimeoutError:
        await ctx.channel.send("⏰ Registration timed out.")
        return None

    # Choose primary ID
    await ctx.channel.send("Use your Discord username as primary ID? (yes/no)")
    try:
        opt = await bot.wait_for('message', check=check, timeout=60)
    except asyncio.TimeoutError:
        await ctx.channel.send("⏰ Registration timed out.")
        return None

    if opt.content.lower().startswith('y'):
        primary = identifier
    else:
        await ctx.channel.send("Please enter your desired primary ID:")
        try:
            custom = await bot.wait_for('message', check=check, timeout=60)
            primary = custom.content.strip()
        except asyncio.TimeoutError:
            await ctx.channel.send("⏰ Registration timed out.")
            return None

    # Call API to register
    try:
        resp = requests.post(f"{API_BASE}/register", json={
            'source': 'DISCORD',
            'identifier': identifier,
            'primary_id': primary
        })
        resp.raise_for_status()
        # Get the response (session_id)
        data = resp.json()
        session_id = data.get('session_id')
        
        # Check if user is already authenticated (existing user, new source)
        user_doc = get_user_data(primary)
        if user_doc and 'auth' in user_doc:
            await ctx.channel.send(f"✅ Registration complete! You are already authenticated and ready to upload receipts! (Primary ID: `{primary}`)")
        else:
            # New user or existing user without authentication
            if await ensure_authenticated(ctx, primary):
                await ctx.channel.send(f"✅ Registration and authentication complete! You can now upload receipts! (Primary ID: `{primary}`)")
            else:
                login_link = f"{API_BASE}/login/TRUE/{session_id}"
                try:
                    await ctx.author.send(f"✅ You are registered under ID: `{primary}`.\nPlease [Login Here]({login_link}) to Complete Registration.")
                    await ctx.channel.send("✅ Registration complete! Please check your DM for the login link to finish authentication...")
                except discord.Forbidden:
                    await ctx.channel.send(f"✅ Registration complete! Please complete authentication: {login_link}")
        return primary
    except Exception as e:
        await ctx.channel.send(f"❌ Registration failed: {e}")
        return None

@bot.command(name='auth')
async def check_auth(ctx):
    """Command to check authentication status and get login link if needed."""
    identifier = ctx.author.name
    
    # Get primary ID
    try:
        r = requests.get(f"{API_BASE}/get_primary", params={
            'source': 'DISCORD',
            'identifier': identifier
        })
        if r.status_code != 200:
            await ctx.channel.send("❌ You are not registered. Please use `!register` or send an image to start registration.")
            return
        
        primary = r.json().get('primary_id')
        
        # Use the robust authentication checker
        if await ensure_authenticated(ctx, primary):
            await ctx.channel.send(f"✅ You are authenticated and ready to upload receipts! (Primary ID: `{primary}`)")
        else:
            await ctx.channel.send("❌ Authentication incomplete. Please try the `!auth` command again or contact support.")
                
    except Exception as e:
        await ctx.channel.send(f"❌ Error checking authentication: {e}")

@bot.command(name='status')
async def quick_status(ctx):
    """Quick authentication status check without waiting."""
    identifier = ctx.author.name
    
    try:
        r = requests.get(f"{API_BASE}/get_primary", params={
            'source': 'DISCORD',
            'identifier': identifier
        })
        if r.status_code != 200:
            await ctx.channel.send("❌ Not registered. Use `!register` to get started.")
            return
        
        primary = r.json().get('primary_id')
        user_doc = get_user_data(primary)
        
        if not user_doc:
            await ctx.channel.send("❌ Failed to verify your account.")
            return
            
        if 'auth' in user_doc:
            await ctx.channel.send(f"✅ Authenticated and ready! (Primary ID: `{primary}`)")
        else:
            session_id = user_doc.get('session_id')
            login_link = f"{API_BASE}/login/TRUE/{session_id}"
            try:
                await ctx.author.send(f"❌ Not authenticated. [Login Here]({login_link}) to complete authentication.")
                await ctx.channel.send("❌ Not authenticated. Please check your DM for the login link, or use `!auth` for guided assistance.")
            except discord.Forbidden:
                await ctx.channel.send("❌ Not authenticated. Cannot send DM - please check your privacy settings. Use `!auth` for guided assistance.")
                
    except Exception as e:
        await ctx.channel.send(f"❌ Error: {e}")

@bot.command(name='register')
async def manual_register(ctx):
    """Command to manually register without uploading an image."""
    primary = await ensure_registered(ctx)
    # ensure_registered already handles all messaging for both scenarios:
    # 1. New registration with authentication flow
    # 2. Existing user already authenticated
    # No additional messaging needed here

async def process_upload(session_id, file_path, identifier, primary, source, timestamp):
    """
    Background upload to API.
    """
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f, f"image/{{file_path.split('.')[-1]}}")}
            data = {
                'session_id': session_id,
                'identifier': identifier,
                'source': source,
                'timestamp': timestamp,
                'optimize': OPTIMISE,         # Ensure string type for form field (default True)
            }
            requests.post(f"{API_BASE}/upload", files=files, data=data, timeout=30)
    except Exception as e:
        print(f"[❌] Background upload failed for session {session_id}: {e}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Process commands (like !register)
    await bot.process_commands(message)

    if message.attachments:
        # Ensure registration
        primary = await ensure_registered(message)
        if not primary:
            return
        if not await ensure_authenticated(message, primary):
            return

        # Ensure img_content folder exists
        img_dir = os.path.join(os.getcwd(), 'img_content')
        os.makedirs(img_dir, exist_ok=True)

        identifier = message.author.name
        source = 'DISCORD'

        for attachment in message.attachments:
            if attachment.content_type and attachment.content_type.startswith('image/'):
                session_id = str(uuid.uuid4())
                timestamp = message.created_at.isoformat()
                file_extension = attachment.filename.split('.')[-1]
                file_name = f'{session_id}.{file_extension}'
                file_path = os.path.join(img_dir, file_name)
                await attachment.save(file_path)
                await message.channel.send(f"📸 Image saved, session `{session_id}`. Uploading for processing...")

                # Schedule background upload
                asyncio.create_task(process_upload(
                    session_id, file_path, identifier, primary, source, timestamp
                ))

if __name__ == '__main__':
    bot.run(DISCORD_TOKEN)
