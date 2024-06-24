import asyncio
import json
import os
import sys
from pathlib import Path
import discord
from discord.ext import commands

BASE_DIR = Path(os.path.abspath(__file__)).parent

with open(BASE_DIR/"settings.json", 'r') as f:
    Settings = json.loads(f.read())

intents = discord.Intents.all()
intents.members = True
bot = commands.Bot(command_prefix=Settings["PREFIX"], description=Settings["DESCRIPTION"],
                   owner_id=Settings["OWNERID"], intents=intents)


@bot.event
async def on_ready():
    # File COGS
    for x in Path(BASE_DIR/"Cogs").glob("*.py"):
        await bot.load_extension(f"Cogs.{x.stem}")
    # Dir COGS
    for x in Path(BASE_DIR/"Cogs").glob("*/__init__.py"):
        await bot.load_extension(f"Cogs.{x.parent.stem}")
    print('Logged in as : ')
    print("Name :", bot.user.name)
    print("ID :", bot.user.id)
    print("In guilds :", [g.name for g in bot.guilds])
    print('-'*20)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, (commands.MissingRequiredArgument, commands.BadArgument)):
        await ctx.send_help(ctx.command)
        print(error)
    elif isinstance(error, (commands.CommandNotFound, commands.CheckFailure)):
        print(error)
    elif isinstance(error, (commands.MaxConcurrencyReached, commands.CommandOnCooldown)):
        await ctx.send("Hey chill, chill!")
    elif isinstance(error, commands.NoPrivateMessage):
        await ctx.send("That command is not available in DM's.")
    else:
        print(error)


if __name__ == '__main__':
    bot.run(Settings["TOKEN"])
