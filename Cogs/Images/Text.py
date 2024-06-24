import io
import os
import asyncio
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageFont, ImageDraw
from textwrap import wrap
import discord
from discord.ext import commands

BASE_DIR = Path(os.path.abspath(__file__)).parent
IMG_DIR = BASE_DIR / "Data/"


def radial_blur(img, blur=0.01, iters=5):
    w, h = img.shape[:2]
    center_x = h / 2
    center_y = w / 2
    hrange = np.arange(h)
    wrange = np.arange(w)

    growMapx = np.tile(hrange + ((hrange - center_x) * blur),
                       (w, 1)).astype(np.float32)
    shrinkMapx = np.tile(hrange - ((hrange - center_x) * blur), (w, 1)).astype(
        np.float32
    )
    growMapy = (
        np.tile(wrange + ((wrange - center_y) * blur), (h, 1))
        .transpose()
        .astype(np.float32)
    )
    shrinkMapy = (
        np.tile(wrange - ((wrange - center_y) * blur), (h, 1))
        .transpose()
        .astype(np.float32)
    )

    for _ in range(iters):
        tmp1 = cv2.remap(img, growMapx, growMapy, cv2.INTER_LINEAR)
        tmp2 = cv2.remap(img, shrinkMapx, shrinkMapy, cv2.INTER_LINEAR)
        img = cv2.addWeighted(tmp1, 0.5, tmp2, 0.5, 0)
    return img


def gen_text_img(text, size, color=(0, 0, 0), fontname="Anavio.ttf", fontsize=40, mode="RGBA"):
    font = ImageFont.truetype(font=str(IMG_DIR / fontname), size=fontsize)
    img = Image.new(mode, size)
    draw = ImageDraw.Draw(img)
    draw.text((size[0]//2, 10), text, color,
              font=font, align="center", anchor="ma")
    return img


class TextImages(commands.Cog, name="Images"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def achieved(self, ctx, *text):
        """Dark Souls style Achieved meme"""
        await ctx.typing()
        txt = wrap(" ".join(list(text)+["ACHIEVED"]), 20, break_long_words=False)
        ti = gen_text_img("\n".join(txt).upper(), (800, 100 * (len(txt))),
                          (225, 215, 75), fontsize=70, mode="RGB")
        img = radial_blur(np.array(ti)[:, :, ::-1])
        with io.BytesIO(cv2.imencode(".jpg", img)[1]) as buffer:
            await ctx.send(file=discord.File(fp=buffer, filename="meme.jpg"))

    @commands.command()
    async def restored(self, ctx, *text):
        """Dark Souls style Restored meme"""
        await ctx.typing()
        txt = wrap(" ".join(list(text)+["RESTORED"]), 20, break_long_words=False)
        ti = gen_text_img("\n".join(txt).upper(), (800, 100 * (len(txt))),
                          (80, 140, 110), fontsize=70, mode="RGB")
        img = radial_blur(np.array(ti)[:, :, ::-1])
        with io.BytesIO(cv2.imencode(".jpg", img)[1]) as buffer:
            await ctx.send(file=discord.File(fp=buffer, filename="meme.jpg"))

    @commands.command()
    async def klee(self, ctx, *text):
        """Let Klee say something"""
        await ctx.typing()
        txt = wrap(" ".join(text), 38, break_long_words=False)
        text_img = gen_text_img("\n".join(txt), (500, 500),
                                fontname="Arbery.ttf")
        text_img = text_img.rotate(16, resample=Image.BILINEAR, expand=True)
        img = Image.open(IMG_DIR / "klee.jpg")
        img.paste(text_img, (230, 400), text_img)
        with io.BytesIO() as buffer:
            img.save(buffer, format="PNG")
            buffer.seek(0)
            await ctx.send(file=discord.File(fp=buffer, filename="meme.png"))


async def setup(bot):
    await bot.add_cog(TextImages(bot))
