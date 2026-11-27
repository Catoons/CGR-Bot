# Version 2026.2
import json
import os

import discord

from datetime import datetime, timedelta

from discord import app_commands
from discord.ext import commands, tasks

DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]
READY_TO_EDIT_CHANNEL_ID = int(os.environ["READY_TO_EDIT_CHANNEL_ID"])

# File to store reminders, kept in the same folder as this script
SCRIPT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
REMINDER_FILE = os.path.join(SCRIPT_DIRECTORY, "reminders.json")

# Discord rejects messages longer than this
DISCORD_MESSAGE_LIMIT = 2000

# Intents and bot setup
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True  # Needed for the Google Docs pinning in on_message


class CGRBot(commands.Bot):
    async def setup_hook(self):
        # Register the slash commands with Discord
        synced_commands = await self.tree.sync()
        print(f"Synced {len(synced_commands)} slash command(s)")


bot = CGRBot(command_prefix="!", intents=intents)  # Prefix is unused, but commands.Bot requires one

# Load reminders from file
def load_reminders():
    try:
        with open(REMINDER_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

# Save reminders to file
def save_reminders(reminders):
    with open(REMINDER_FILE, "w") as file:
        json.dump(reminders, file, indent=4)

# Check if a reminder is due
def is_reminder_due(reminder):
    due_date = datetime.fromisoformat(reminder["next_reminder"])
    return datetime.now() >= due_date

# Update the next reminder date
def update_next_reminder(reminder):
    reminder["next_reminder"] = (datetime.now() + timedelta(days=180)).isoformat()

# Task to check and send reminders
@tasks.loop(minutes=1)
async def reminder_task():
    reminders = load_reminders()
    for user_id, reminder in reminders.items():
        if is_reminder_due(reminder):
            channel_id = reminder["channel_id"]
            channel = bot.get_channel(channel_id)
            if channel:
                try:
                    await channel.send(f"Reminder for <@{user_id}>: You're eligible to submit a game for us to review! Within 30 days, respond to this message with the title of the game and the platform(s) on which it is available. A member of our team will get to it shortly!")
                except discord.Forbidden:
                    print(f"Could not send reminder to channel {channel_id}.")
            update_next_reminder(reminder)
    save_reminders(reminders)

@bot.event
async def on_ready():
    print(f"Bot is ready as {bot.user}")
    # on_ready can fire again after a reconnect, so only start the loop if it isn't already running
    if not reminder_task.is_running():
        reminder_task.start()

# Command to set a reminder
@bot.tree.command(name="set_reminder", description="Set a reminder for a user in the current channel.")
@app_commands.describe(user="The user to remind")
async def set_reminder(interaction: discord.Interaction, user: discord.User):
    user_id = str(user.id)  # The selected user's ID
    channel_id = interaction.channel_id
    reminders = load_reminders()

# Reminders go off every 180 days
    reminders[user_id] = {
        "next_reminder": (datetime.now() + timedelta(days=180)).isoformat(),
        "channel_id": channel_id,
    }
    save_reminders(reminders)

    await interaction.response.send_message(f"Reminder set for {user.mention}! I'll remind them in 6 months in this channel.")


# Command to view all reminders
@bot.tree.command(name="view_reminders", description="View all reminders set for everyone.")
async def view_reminders(interaction: discord.Interaction):
    reminders = load_reminders()

    if not reminders:
        await interaction.response.send_message("There are no reminders set.")
        return

    # Build one line per reminder
    reminder_lines = ["Here are all the reminders:"]
    for user_id, reminder in reminders.items():
        channel_id = reminder.get("channel_id", "Unknown Channel")
        next_reminder = datetime.fromisoformat(reminder["next_reminder"]).strftime('%Y-%m-%d %H:%M:%S')
        reminder_lines.append(
            f"- <@{user_id}>: "
            f"(Next Reminder: {next_reminder}, Channel: <#{channel_id}>)"
        )

    # Group the lines into messages that each fit under Discord's limit
    messages_to_send = []
    current_message = ""
    for line in reminder_lines:
        if len(current_message) + len(line) + 1 > DISCORD_MESSAGE_LIMIT:
            messages_to_send.append(current_message)
            current_message = ""
        current_message += line + "\n"
    messages_to_send.append(current_message)

    # A slash command can only be answered once, so the first message is the response and the rest are follow-ups
    # AllowedMentions.none() shows the names without pinging anyone
    await interaction.response.send_message(
        messages_to_send[0],
        allowed_mentions=discord.AllowedMentions.none(),
    )
    for extra_message in messages_to_send[1:]:
        await interaction.followup.send(
            extra_message,
            allowed_mentions=discord.AllowedMentions.none(),
        )

# Command to delete a reminder
@bot.tree.command(name="delete_reminder", description="Delete a reminder for a specific user.")
@app_commands.describe(user="The user whose reminder should be deleted")
async def delete_reminder(interaction: discord.Interaction, user: discord.User):
    user_id = str(user.id)
    reminders = load_reminders()
    if user_id in reminders:
        del reminders[user_id]
        save_reminders(reminders)
        await interaction.response.send_message(f"Reminder for {user.mention} has been deleted.")
    else:
        await interaction.response.send_message(f"There are no reminders set for {user.mention}.")

# Event triggered when a message is sent in a channel
@bot.event
async def on_message(message):

    # Check if the message is in the specified channel and contains a Google Docs link
    if message.channel.id == READY_TO_EDIT_CHANNEL_ID and 'docs.google.com' in message.content:
        try:
            await message.pin()
        except discord.errors.Forbidden:
            await message.channel.send("I don't have permission to pin messages in this channel.")
        except discord.errors.HTTPException:
            await message.channel.send("Failed to pin the message due to an API error.")

# Pings the bot to see if it's still breathing
@bot.tree.command(name="ping_cgr_bot", description="Check if the bot is running.")
async def ping_cgr_bot(interaction: discord.Interaction):
    await interaction.response.send_message("I'm alive :)")

# Run the bot
bot.run(DISCORD_BOT_TOKEN)