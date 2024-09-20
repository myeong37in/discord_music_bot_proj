import discord
from discord.ext import commands
import yt_dlp
import asyncio
import os
from dotenv import load_dotenv # 토큰 가져옴

class MusicBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.music_queue = []
        self.is_playing_now = False
        self.current_song = None
        self.video_cache = {} # 캐시 도입
    
    
    # 매뉴얼 출력
    @commands.command(name = "manual")
    async def print_manual(self, ctx, command_name: str = None):
        command_manual = {  # 딕셔너리는 신이고 난 병신이다
            "play": "!play (유튜브 링크): 음성 채널에 봇이 접속하여 해당 유튜브 링크의 음성을 재생",
            "stop": "!stop: 재생 중인 음악의 재생을 취소하고 봇을 음설 채널에서 내보냄",
            "skip": "!skip: 재생 중인 음악의 재생을 취소 후 큐에 있는 다음 음악을 재생",
            "queue": "!queue: 재생 중인 음악과 큐에 있는 음악들의 순서, 제목을 출력"
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
                
                
    # 링크를 받아 유튜브에서 동영상 제목을 추출
    async def extract_video_title(self, url):
        if url in self.video_cache:
            return self.video_cache[url]
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
        }
        
        # 동기화 함수를 비동기적으로 처리
        def sync_extract():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                video_title = info.get('title')  # 제목 추출
            return video_title
        
        video_title = await asyncio.to_thread(sync_extract)
        
        self.video_cache[url] = video_title
        
        return video_title
    
    
    # 링크를 받아 유튜브에서 오디오 URL을 추출
    async def extract_audio_url(self, url):
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
        }
        
        # 동기화 함수를 비동기적으로 처리
        def sync_extract():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                audio_url = info['url']  # 제목 추출
            return audio_url
        
        audio_url = await asyncio.to_thread(sync_extract)

        return audio_url
    
    
    # 음악 재생 커맨드
    @commands.command(name = "play")
    async def play(self, ctx, url: str):

        self.music_queue.append(url)
        
        if self.is_playing_now:
            await ctx.send(f"'{url}' 이 큐에 추가되었습니다.")
        else:
            await self.play_next(ctx)
            
            
    # 큐에서 다음 음악 재생
    async def play_next(self, ctx):
        if len(self.music_queue) > 0:
            self.is_playing_now = True
            next_url = self.music_queue.pop(0)
            await self.play_audio(ctx, next_url)
        else:
            self.is_playing_now = False
            await ctx.send("큐가 비어있습니다. 음악을 추가하세요.")


    # 음악 재생 코드
    async def play_audio(self, ctx, video_url):
        if ctx.author.voice is None: # 메시지 작성자가 음성 채널에 접속해 있어야 함
            await ctx.send("먼저 음성 채널에 들어가세요")
            return
        
        voice_channel = ctx.author.voice.channel # 작성자의 채널에 음악이 재생됨
        
        if ctx.voice_client is None: # 봇을 음성 채널에 연결
            vc = await voice_channel.connect()
        else:
            vc = ctx.voice_client

        self.current_song = video_url
        audio_url = await self.extract_audio_url(video_url)
        
        vc.play(discord.FFmpegPCMAudio(executable="ffmpeg.exe",
                                    source=audio_url, 
                                    before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5", # before_options: 이거 없으면 3분 재생하고 ffmpeg 프로세스가 꺼짐 -> 재생 끊김
                                    options="-vn -filter:a 'volume=0.7'"), # 기본 볼륨 70%
                                    after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop)) # 재생 중인 음악이 끝나면 play_next 실행
        

    # 스킵 커맨드
    @commands.command(name = "skip")
    async def skip(self, ctx):
        if not self.is_playing_now:
            await ctx.send("재생 중임 음악이 없습니다.")
            return
        
        if ctx.voice_client is not None:
            ctx.voice_client.stop()
        
        
    # 음악 재생 중지 및 큐 초기화 커맨드
    @commands.command(name = "stop")
    async def stop(self, ctx):
        if ctx.voice_client is None:
            return
        
        ctx.voice_client.stop()
        await ctx.voice_client.disconnect()
        
        self.music_queue.clear()
        self.is_playing_now = False
        
        await ctx.send("음악 재생이 중지되었습니다. 큐가 초기화되었습니다.")
        

    # 현재 큐를 확인하는 커맨드
    @commands.command(name = "queue")
    async def print_queue(self, ctx):
        if len(self.music_queue) == 0 and self.current_song is None:
            await ctx.send("큐가 비어있습니다.")
            return
        
        current_title = await self.extract_video_title(self.current_song)
        await ctx.send(f"현재 플레이 중: {current_title}")
        
        # 큐의 음악 출력
        if len(self.music_queue) > 0:
            queue_message = "큐에 대기 중인 음악\n"
            for i, video_url in enumerate(self.music_queue, start = 1):
                video_title = await self.extract_video_title(video_url)
                queue_message += f"{i}. {video_title}\n"
            await ctx.send(queue_message)
            
# 초기 설정. 명령어의 prefix는 !로 정함
private_intents = discord.Intents.all()
bot = commands.Bot(command_prefix = "!", intents = private_intents)

load_dotenv()
token = os.getenv("DISCORD_BOT_TOKEN")

# 봇이 정상적으로 가동되면 터미널에 "Terminal message"가 출력될 것임. 이때부터 봇 사용
@bot.event
async def on_ready():
    # 봇 인스턴스 생성
    await bot.add_cog(MusicBot(bot)) # 봇 명령어 등록
    await bot.change_presence(status=discord.Status.online, activity=discord.Game("!manual: 매뉴얼 출력")) # 봇의 상태 메시지
    print("Terminal message")

# 봇 실행
bot.run(token)