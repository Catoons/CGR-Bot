# CGR Bot v4.0
# 94% ChatGPT, 6% Catoons

import discord
from discord.ext import commands, tasks
import asyncio
import json
import time

intents = discord.Intents.all()
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Path to the reminders data file
REMINDERS_FILE = "reminders.json"

# Load reminders from the data file
def load_reminders():
    try:
        with open(REMINDERS_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

# Save reminders to the data file
def save_reminders():
    with open(REMINDERS_FILE, "w") as file:
        json.dump(reminders, file)

# Dictionary to store user reminders
reminders = load_reminders()

# Event triggered when the bot is ready
@bot.event
async def on_ready():
    print(f'Bot is ready. Logged in as {bot.user.name}')

    
    reminder_loop.start()

# Command to start the reminder for a user
@bot.command()
async def start_reminder(ctx, user: discord.User):
    reminders[str(user.id)] = {
        "channel_id": ctx.channel.id,
        "start_time": time.time()
    }
    save_reminders()
    await ctx.send(f'Reminder started for {user.name}.')

# Command to cancel the reminder for a user
@bot.command()
async def cancel_reminder(ctx, user: discord.User):
    if str(user.id) in reminders:
        del reminders[str(user.id)]
        save_reminders()
        await ctx.send(f'Reminder canceled for {user.name}.')
    else:
        await ctx.send(f'No active reminder found for {user.name}.')

# Background task to check and send reminders every 6mo
@tasks.loop(minutes=60)  # Check every hour for simplicity, adjust as needed
async def reminder_loop():
    current_time = time.time()
    for user_id, data in reminders.items():
        user = await bot.fetch_user(int(user_id))
        channel = bot.get_channel(data["channel_id"])
        start_time = data["start_time"]
        elapsed_time = current_time - start_time
        # Check if 6 months (or any desired duration) have passed
        if elapsed_time >= 15724800:  # 182 days in seconds
            await channel.send(f"""Hey {user.mention}! You're eligible to submit a game for us to review!
Within 30 days, respond to this message with the title of the game and the platform(s) on which it is availible.
A member of our team will get to it shortly!""")
            # Update the start time for the next reminder
            data["start_time"] = current_time
            save_reminders()


# Event triggered when a message is sent in a channel
@bot.event
async def on_message(message):
    # Define the specific channel where the bot will pin Google Docs links
    specific_channel_id = 1288633281046380705
    
    # Check if the message is in the specific channel and contains a Google Docs link
    if message.channel.id == specific_channel_id and 'docs.google.com' in message.content:
        try:
            await message.pin()
        except discord.errors.Forbidden:
            await message.channel.send("I don't have permission to pin messages in this channel.")
        except discord.errors.HTTPException:
            await message.channel.send("Failed to pin the message due to an API error.")
    
    # Don't forget to process other commands
    await bot.process_commands(message)


# Pings the bot to see if it's still breathing
@bot.command()
async def ping_pusher(ctx):
    await ctx.send("I'm alive :)")

# Start the bot. String is bot token
bot.run('MTExMjQ2NDI5MDI1MTgxMjg5NA.GO6o9N._59DuHyWFrmg4nLUVMPE-pi_-8k4MMg_Jxtu0Q')
