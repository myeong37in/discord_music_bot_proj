import discord
from discord.ext import commands
import yt_dlp
import asyncio
import os
from dotenv import load_dotenv # 토큰 가져옴

private_intents = discord.Intents.all()
bot = commands.Bot(command_prefix = "/", intents = private_intents)

load_dotenv()
token = os.getenv("DISCORD_BOT_TOKEN")

@bot.event
async def on_ready():
    print("Terminal message")
    await bot.change_presence(status=discord.Status.online, activity=discord.Game("/play_music (링크)")) # 봇의 상태 메시지
    
@bot.event
async def play_audio(ctx, url):
    if ctx.author.voice is None: # 메시지 작성자가 음성 채널에 접속해 있어야 함
        await ctx.message("먼저 음성 채널에 들어가세요")
        return
    
    voice_channel = ctx.author.voice.channel # 작성자의 채널에 음악이 재생됨
    
    if ctx.voice_client is not None: # 이미 음성 채널에 들어와 있을 경우 봇 재연결
        await ctx.voice_client.disconnect()
    vc = await voice_channel.connect()
    
    ydl_opts = {
        'format' : 'bestaudio',
        'quiet': True,
        'extract_flat': 'in_playlist'
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl: # 몰라 StackOverflow에서 이렇게 하래
        info = ydl.extract_info(url, download = False)
        audio_url = info['url']

    # executable: ㅅㅂ 환경 변수 설정했는데 왜 안 됨? before_options: 이거 없으면 3분 재생하고 ffmpeg 프로세스가 꺼짐 -> 재생 끊김
    vc.play(discord.FFmpegPCMAudio(executable="C:/ffmpeg_full_build/bin/ffmpeg.exe", source=audio_url, before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",options="-vn"), after=lambda e: print('done', e))
    
    await ctx.send(f"{url} 재생 중")

@bot.command(name = "play_music")
async def play(ctx, url: str):
    await play_audio(ctx, url)

bot.run(token)