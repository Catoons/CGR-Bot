# CGR Bot v4.0
# 94% ChatGPT, 6% Catoons

import discord
from discord.ext import commands, tasks
import asyncio
import json
import time


# Event triggered when a message is sent in a channel
@bot.event
async def on_message(message):
    # Define the specific channel where the bot will pin Google Docs links
    specific_channel_id = 746003305372581918
    
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
