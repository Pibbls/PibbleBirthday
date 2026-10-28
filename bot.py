"""A simple Discord birthday bot.

Commands:
  /setbirthday <month> <day>  - save your birthday
  /removebirthday             - forget your birthday
  /birthdays                  - list everyone's birthday in this server
  /setchannel <channel>       - (admins) choose where announcements go
"""

import json
import os
from datetime import datetime, time

import discord
from discord import app_commands
from discord.ext import tasks

def load_env_file(path=".env"):
    """Read KEY=value lines from a .env file (handy on hosts without environment settings)."""
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip('"'))


load_env_file()
TOKEN = os.environ.get("DISCORD_TOKEN")
DATA_FILE = "birthdays.json"
MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]
DAYS_IN_MONTH = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


# ---------- storage ----------
# Layout: {guild_id: {"channel": id, "users": {user_id: "MM-DD"}, "announced": {user_id: year}}}

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def guild_data(guild_id):
    return data.setdefault(str(guild_id), {"channel": None, "users": {}, "announced": {}})


data = load_data()


# ---------- bot setup ----------

class BirthdayBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()
        check_birthdays.start()


bot = BirthdayBot()


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


# ---------- commands ----------

@bot.tree.command(name="setbirthday", description="Save your birthday")
@app_commands.describe(month="Month (1-12)", day="Day of the month")
async def setbirthday(interaction: discord.Interaction,
                      month: app_commands.Range[int, 1, 12],
                      day: app_commands.Range[int, 1, 31]):
    if day > DAYS_IN_MONTH[month - 1]:
        await interaction.response.send_message(
            f"{MONTHS[month - 1]} doesn't have {day} days!", ephemeral=True)
        return
    g = guild_data(interaction.guild_id)
    g["users"][str(interaction.user.id)] = f"{month:02d}-{day:02d}"
    save_data()
    await interaction.response.send_message(
        f"🎂 Got it! Your birthday is **{MONTHS[month - 1]} {day}**.", ephemeral=True)


@bot.tree.command(name="removebirthday", description="Remove your saved birthday")
async def removebirthday(interaction: discord.Interaction):
    g = guild_data(interaction.guild_id)
    if g["users"].pop(str(interaction.user.id), None):
        save_data()
        await interaction.response.send_message("Your birthday was removed.", ephemeral=True)
    else:
        await interaction.response.send_message("You don't have a birthday saved.", ephemeral=True)


@bot.tree.command(name="birthdays", description="List birthdays in this server")
async def birthdays(interaction: discord.Interaction):
    g = guild_data(interaction.guild_id)
    if not g["users"]:
        await interaction.response.send_message("No birthdays saved yet.")
        return
    lines = []
    for user_id, mmdd in sorted(g["users"].items(), key=lambda item: item[1]):
        month, day = map(int, mmdd.split("-"))
        lines.append(f"<@{user_id}> — {MONTHS[month - 1]} {day}")
    await interaction.response.send_message(
        "🎉 **Birthdays**\n" + "\n".join(lines),
        allowed_mentions=discord.AllowedMentions.none())


@bot.tree.command(name="setchannel", description="Choose the birthday announcement channel")
@app_commands.default_permissions(manage_guild=True)
async def setchannel(interaction: discord.Interaction, channel: discord.TextChannel):
    g = guild_data(interaction.guild_id)
    g["channel"] = channel.id
    save_data()
    await interaction.response.send_message(f"Birthday announcements will go in {channel.mention}.")


# ---------- daily check ----------

def is_birthday_today(mmdd, today):
    if mmdd == today.strftime("%m-%d"):
        return True
    # Feb 29 birthdays get celebrated on Feb 28 in non-leap years.
    is_leap = today.year % 4 == 0 and (today.year % 100 != 0 or today.year % 400 == 0)
    return mmdd == "02-29" and not is_leap and today.strftime("%m-%d") == "02-28"


# Runs a few times a day (in the computer's local time) so a restart never misses a birthday.
LOCAL_TZ = datetime.now().astimezone().tzinfo


@tasks.loop(time=[time(hour=h, tzinfo=LOCAL_TZ) for h in (0, 6, 12, 18)])
async def check_birthdays():
    today = datetime.now()
    for guild in bot.guilds:
        g = guild_data(guild.id)
        channel = guild.get_channel(g["channel"]) if g["channel"] else guild.system_channel
        if channel is None:
            continue
        for user_id, mmdd in g["users"].items():
            if not is_birthday_today(mmdd, today):
                continue
            if g["announced"].get(user_id) == today.year:
                continue  # already announced this year
            await channel.send(f"🎉🎂 Happy birthday <@{user_id}>! Everyone wish them a great day! 🎈")
            g["announced"][user_id] = today.year
            save_data()


@check_birthdays.before_loop
async def before_check():
    await bot.wait_until_ready()
    await check_birthdays.coro()  # also check right away on startup


if __name__ == "__main__":
    if not TOKEN:
        raise SystemExit("Set the DISCORD_TOKEN environment variable first.")
    bot.run(TOKEN)
