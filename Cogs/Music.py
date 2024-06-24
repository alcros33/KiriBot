import asyncio as aio, io, queue, subprocess, threading, time, sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, Optional, IO
import discord
from discord.ext import commands, tasks
from discord.oggparse import OggStream
import httpx
import yt_dlp

BASE_DIR = Path(__file__).absolute().parent

class NoOp:
    def __call__(self, *args, **kwargs):
        pass
    
    def __getattribute__(self, __name: str):
        return self

def yt_audio(url:str) -> dict:
    OPTS = {
    'logger': NoOp(),
    'noplaylist': True,
    }
    try:
        with yt_dlp.YoutubeDL(OPTS) as ydl:
            info = ydl.extract_info(url, download=False)
    except yt_dlp.DownloadError:
        return None
    data = max(
                filter(lambda f:f["protocol"] == "https" and f["acodec"]=="opus", info["formats"]),
                key=lambda x:x.get("abr", 0))
    data['duration'] = info['duration']
    data['title'] = info['title']
    return data


class HttpFileBuffer:
    def __init__(self, url, http_headers, chunk_size=8*1024):
        self._internal_buffer = []
        self._chunk_iterator = self.iter_stream(url, http_headers)
        self.chunk_size = chunk_size
        pass
    
    def iter_stream(self, url, http_headers):
        with httpx.stream("GET", url, headers=http_headers, timeout=None) as r:
            if r.status_code != 200:
                print(r.status_code)
            for c in r.iter_bytes(self.chunk_size):
                self._internal_buffer += c
                yield None

    def read(self, count:int):
        if count > len(self._internal_buffer):
            self.next_chunk()
        ret_val = self._internal_buffer[:count]
        self._internal_buffer = self._internal_buffer[count:]
        return bytes(ret_val)

    def next_chunk(self):
        try:
            next(self._chunk_iterator)
        except StopIteration:
            pass

class Music(commands.Cog):
    """Music :). Mainly youtube"""
    
    def __init__(self, bot):
        self.bot = bot
        self.disconnecter.start()
        self.songQs = defaultdict(queue.Queue)
        self.isLooping = defaultdict(threading.Event)
        self.dcEvent = defaultdict(threading.Event)
        self.clients : Dict[discord.Guild, discord.VoiceClient] = dict()
    
    def next_track(self, ctx:commands.Context):
        if ctx.guild not in self.clients:
            print("this should not happen...")
            return
        try:
            data = self.songQs[ctx.guild].get() # this is current one
            if data is None:
                # DC was scheduled, do nothing
                return
            if not self.isLooping[ctx.guild].is_set():
                data = self.songQs[ctx.guild].get(timeout=5) # if not lopping, get another one
            self.songQs[ctx.guild].put(data)
        except queue.Empty:
            # Need to call DC
            self.isLooping[ctx.guild].clear()
            self.dcEvent[ctx.guild].set()
            return
        
        yt_file_buffer = HttpFileBuffer(data['url'], data['http_headers'])
        audio = discord.FFmpegOpusAudio(yt_file_buffer,
                    bitrate=int(data['abr']), codec='copy', executable='ffmpeg', pipe=True, stderr=None)
        self.clients[ctx.guild].play(audio, after=lambda e: self.next_track(ctx))

    @commands.command(aliases=["p"])
    @commands.max_concurrency(1, commands.BucketType.guild, wait=True)
    @commands.guild_only()
    async def play(self, ctx:commands.Context, url:str = None):
        """ Plays youtube music"""
        if url is not None: 
            await ctx.send(f"**🎵 Searching 🔎** `{url}`")
            if (data := yt_audio(url)) is None:
                return await ctx.send(f"`{url}` **Does Not seem to be a valid video url**")
            
            self.songQs[ctx.guild].put(data)
            await ctx.send(f"🎶 `{data['title']}` **Added to the queue!**")
        
        if ctx.guild not in self.clients:
            self.dcEvent[ctx.guild].clear()
            self.isLooping[ctx.guild].clear()
            self.clients[ctx.guild] = await ctx.author.voice.channel.connect()
            yt_file_buffer = HttpFileBuffer(data['url'], data['http_headers'])
            audio = discord.FFmpegOpusAudio(yt_file_buffer,
                        bitrate=int(data['abr']), codec='copy', executable='ffmpeg', pipe=True, stderr=sys.stderr)
            self.clients[ctx.guild].play(audio, after=lambda e: self.next_track(ctx))
            await ctx.send(f"**👍 Joined `{ctx.author.voice.channel.name}`**")
        else:
            if not self.songQs[ctx.guild]:
                return await ctx.send("Queue is empty")
            if not self.clients[ctx.guild].is_playing():
                self.clients[ctx.guild].resume()
                await ctx.send("** Resumed 👍**")
    
    @commands.command()
    @commands.max_concurrency(1, commands.BucketType.guild, wait=True)
    @commands.guild_only()
    async def pause(self, ctx):
        """Pauses reproduction"""
        if ctx.guild in self.clients:
            self.clients[ctx.guild].pause()
            await ctx.send("**:pause_button: Paused 👍**")
    
    @commands.command(aliases=["fs"])
    @commands.max_concurrency(1, commands.BucketType.guild, wait=True)
    @commands.guild_only()
    async def skip(self, ctx):
        """Skips to next song"""
        if ctx.guild in self.clients:
            self.clients[ctx.guild].stop()
            await ctx.send("**⏩ Skipped 👍**")
    
    @commands.command()
    @commands.max_concurrency(1, commands.BucketType.guild, wait=True)
    @commands.guild_only()
    async def loop(self, ctx):
        """loops current song"""
        if ctx.guild in self.clients:
            self.isLooping[ctx.guild].set()
            await ctx.send("**:infinity: Looping 👍**")
    
    @commands.command()
    @commands.max_concurrency(1, commands.BucketType.guild, wait=True)
    @commands.guild_only()
    async def noloop(self, ctx):
        """disables looping"""
        if ctx.guild in self.clients:
            self.isLooping[ctx.guild].clear()
            await ctx.send("** Disabled Looping 👍**")
    
    @commands.command(aliases=["fuckoff", "dc"])
    @commands.max_concurrency(1, commands.BucketType.guild)
    @commands.guild_only()
    async def disconnect(self, ctx):
        if ctx.guild not in self.clients:
            return
        self.clients[ctx.guild].pause()
        self.isLooping[ctx.guild].clear()
        with self.songQs[ctx.guild].mutex:
            self.songQs[ctx.guild].queue.clear()
        self.songQs[ctx.guild].put(None)
        self.clients[ctx.guild].stop()
        await self.clients[ctx.guild].disconnect()
        del self.clients[ctx.guild]
        self.dcEvent[ctx.guild].clear()
    
    @tasks.loop(seconds=3)
    async def disconnecter(self):
        for guild, event in self.dcEvent.items():
            if event.is_set():
                event.clear()
                await self.clients[guild].disconnect()
                del self.clients[guild]

async def setup(bot):
    await bot.add_cog(Music(bot))
