from discord.ext import commands
from .Text import TextImages
from .Avatar import AvatarImages
from discord.utils import MISSING

class ImageProxy(commands.Cog, name="Images"):
    """Image related commands."""
    def __init__(self, bot):
        self.bot = bot

async def setup(bot):
    await bot.add_cog(ImageProxy(bot))
    await TextImages(bot)._inject(bot, False, MISSING, MISSING)
    await AvatarImages(bot)._inject(bot, False, MISSING, MISSING)
