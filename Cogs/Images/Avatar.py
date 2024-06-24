import io, os, asyncio
from pathlib import Path
import httpx, cv2, numpy as np
from PIL import Image
import discord
from discord.ext import commands

BASE_DIR = Path(os.path.abspath(__file__)).parent
IMG_DIR = BASE_DIR/"Data/"

class AvatarImages(commands.Cog, name="Images"):

    def __init__(self, bot):
        self.bot = bot
        self.avatarMemeData = {
            "slam_to" : [(100,100), 0, (85,190)],
            "poke_to" : [(80,80), 0, (335,150)],
        }
    
    def getAvatarMeme(self, name, url_to=None, url_from=None):
        img = Image.open(IMG_DIR/(name + ".jpg"))
        for s, url in [("from", url_from), ("to", url_to)]:
            if url is None:
                continue
            r = httpx.get(url)
            with io.BytesIO(r.content) as buffer, Image.open(buffer) as avatar:
                memeData = self.avatarMemeData[f"{name}_{s}"]
                avatar = (avatar.convert("RGBA").resize(memeData[0])
                    .rotate(memeData[1], resample=Image.BILINEAR, expand=True))
                img.paste(avatar, memeData[2], avatar)
        return img
    
    async def sendAvatarMeme(self, ctx, user:discord.Member, meme, fallback_msg, inc_user_from=False):
        author = ctx.author
        if not user.avatar:
            await ctx.send("{} has no avatar".format(user.mention))
            return
        if inc_user_from and not author.avatar:
            await ctx.send("{} has no avatar".format(ctx.author.mention))
            return
        
        if user == ctx.me:
            user, author = author, user
            await ctx.send(fallback_msg)
        else:
            await ctx.send("{}".format(user.mention))
        await ctx.trigger_typing()
        url_from = str(author.avatar.with_format("jpeg").url) if inc_user_from else None
        img = self.getAvatarMeme(meme, str(user.avatar.with_format("jpeg").url), url_from)
        with io.BytesIO() as buffer:
            img.save(buffer, format="JPEG")
            buffer.seek(0)
            await ctx.send(file=discord.File(fp=buffer, filename="meme.jpeg"))
    
    @commands.command()
    async def slam(self, ctx, user:discord.Member):
        """Smashes a user against the floor"""
        await self.sendAvatarMeme(ctx, user, "slam", "Common and slam, like I did to your waifu")

    @commands.command()
    async def poke(self, ctx, user:discord.Member):
        """Pokes a user"""
        await self.sendAvatarMeme(ctx, user, "poke", "Go poke yourself")

    @commands.command()
    async def avatar(self, ctx, *, user: discord.Member=None):
        """Sends user's avatar"""
        user = user or ctx.author
        if user.avatar:
            await ctx.send(user.avatar.url)

async def setup(bot):
    await bot.add_cog(AvatarImages(bot))
