import discord
from discord.ext import commands

class General(commands.Cog):
    """General commands."""
    
    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True)
    async def ping(self, ctx):
        """Pong."""
        await ctx.send("Pong")
    
    @commands.command(hidden=True)
    async def pong(self, ctx):
        """Ping."""
        await ctx.send("Ping")
async def setup(bot):
    await bot.add_cog(General(bot))
