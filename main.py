import discord
from discord.ext import commands
import yt_dlp
import asyncio
import os
from dotenv import load_dotenv # 토큰 가져옴

# 초기 설정. 명령어의 prefix는 !로 정함
private_intents = discord.Intents.all()
bot = commands.Bot(command_prefix = "!", intents = private_intents)

load_dotenv()
token = os.getenv("DISCORD_BOT_TOKEN")

# 봇이 정상적으로 가동되면 터미널에 "Terminal message"가 출력될 것임. 이때부터 봇 사용
@bot.event
async def on_ready():
    print("Terminal message")
    await bot.change_presence(status=discord.Status.online, activity=discord.Game("!manual: 매뉴얼 출력")) # 봇의 상태 메시지

# 음악 큐, 재생 상태 플래그
music_queue = []
is_playing_now = False

# 매뉴얼 출력
@bot.command(name = "manual")
async def print_manual(ctx, command_name: str = None):
    command_manual = {  # 딕셔너리는 신이고 난 병신이다
        "play": "!play (유튜브 링크): 음성 채널에 봇이 접속하여 해당 유튜브 링크의 음성을 재생",
        "stop": "!stop: 현재 재생 중인 음악의 재생을 취소하고 봇을 음설 채널에서 내보냄",
        "skip": "!skip: 현재 재생 중인 음악의 재생을 취소 후 큐에 있는 다음 음악을 재생"
    }
    
    if command_name is None:
        help_message = "사용 가능 명령어 목록:\n"
        for command, description in command_manual.items():
            help_message += f"    {command}: {description}\n"
        await ctx.send(help_message)
    else:
        if command_name in command_manual:
            await ctx.send(f"{command_name}: {command_manual[command_name]}")
        else:
            await ctx.send(f"{command_name} 명령어는 없습니다.")


# 음악 재생 커맨드
@bot.command(name = "play")
async def play(ctx, url: str):
    global is_playing_now
    music_queue.append(url)
    if is_playing_now:
        await ctx.send("음악이 큐에 추가되었습니다.")
    else:
        await play_next(ctx)


# 큐에서 다음 음악 재생
async def play_next(ctx):
    global is_playing_now
    if len(music_queue) > 0:
        is_playing_now = True
        next_url = music_queue.pop(0)
        await play_audio(ctx, next_url)
    else:
        is_playing_now = False
        await ctx.send("큐가 비어있습니다. 음악을 추가하세요.")


# 음악 재생 코드
@bot.event
async def play_audio(ctx, url):
    if ctx.author.voice is None: # 메시지 작성자가 음성 채널에 접속해 있어야 함
        await ctx.message("먼저 음성 채널에 들어가세요")
        return
    
    voice_channel = ctx.author.voice.channel # 작성자의 채널에 음악이 재생됨
    
    if ctx.voice_client is None: # 봇을 음성 채널에 연결
        vc = await voice_channel.connect()
    else:
        vc = ctx.voice_client
    
    ydl_opts = {
        'format' : 'bestaudio',
        'quiet': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl: # 몰라 StackOverflow에서 이렇게 하래
        info = ydl.extract_info(url, download = False)
        audio_url = info['url']

    vc.play(discord.FFmpegPCMAudio(executable="C:/ffmpeg_full_build/bin/ffmpeg.exe", # executable: ㅅㅂ 환경 변수 설정했는데 왜 안 됨?
                                   source=audio_url, 
                                   before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5", # before_options: 이거 없으면 3분 재생하고 ffmpeg 프로세스가 꺼짐 -> 재생 끊김
                                   options="-vn"),
                                   after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop)) # 재생 중인 음악이 끝나면 play_next 실행
    
    await ctx.send(f"{url} 재생 중")


# 스킵 커맨드
@bot.command(name = "skip")
async def skip(ctx):
    global is_playing_now
    if not is_playing_now:
        await ctx.send("재생 중임 음악이 없습니다.")
        return
    
    ctx.voice_client.stop()
    

# 음악 재생 중지 및 큐 초기화 커맨드
@bot.command(name = "stop")
async def stop(ctx):
    global music_queue, is_playing_now
    
    if ctx.voice_client is None:
        return
    
    ctx.voice_client.stop()
    await ctx.voice_client.disconnect()
    
    music_queue.clear()
    is_playing_now = False
    
    await ctx.send("음악 재생이 중지되었습니다. 큐가 초기화되었습니다.")
    

# 봇 실행
bot.run(token)