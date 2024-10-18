import discord
from discord.ext import commands
import asyncio
import os
import platform
from dotenv import load_dotenv # 토큰 가져옴
from pytube import YouTube
import yt_dlp
import re

class MusicBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.music_queue = []
        self.current_song = None
        self.leave_timer = None
        # ffmpeg 실행 파일이 PYTHONPATH에 있어야 함. 아래 코드 참고
        # import sys
        # print(sys.path)
        self.ffmpeg_executable = "ffmpeg.exe" if platform.system() == "Windows" else "ffmpeg"

    # 매뉴얼 출력
    @commands.command(name = "manual")
    async def print_manual(self, ctx, command_name: str = None):
        command_manual = {
            "play": "!play (유튜브 링크): 음성 채널에 봇이 접속하여 해당 유튜브 링크의 음성을 재생",
            "stop": "!stop: 재생 중인 음악의 재생을 취소하고 봇을 음설 채널에서 내보냄",
            "skip": "!skip: 재생 중인 음악의 재생을 취소 후 큐에 있는 다음 음악을 재생",
            "queue": "!queue: 재생 중인 음악과 큐에 있는 음악들의 순서, 제목을 출력",
            "queue skip": "queue skip (번호): 큐에 있는 번호의 음악을 큐에서 제거함. \n    0: 재생 중인 음악 스킵, 1: 1번 음악 스킵 등",
            "pause": "!pause: 현재 재생 중인 음악을 일시정지",
            "resume": "!resume: 일시정지 중인 음악을 다시 재생"
        }
        
        if command_name is None:
            help_message = "사용 가능 명령어 목록:\n"
            for command, description in command_manual.items():
                help_message += f"    {command}: {description}\n\n"
            await ctx.send(help_message)
        else:
            if command_name in command_manual:
                await ctx.send(f"{command_name}: {command_manual[command_name]}")
            else:
                await ctx.send(f"{command_name} 명령어는 없습니다.")
                
    
    # 링크를 받아 유튜브에서 동영상 제목을 추출
    async def extract_video_title(self, url):
        try:
            video_title = YouTube(url).title
            return video_title
        except Exception:
            return None
    
    
    # 링크를 받아 기존에 오디오 파일이 있으면 파일 경로를 반환. 없다면 다운로드하여 경로를 반환
    async def download_audio_file(self, url):
        video_id = await self.get_video_id(url)
        if video_id is None:
            return None
        
        audio_filename = f"{video_id}.mp3"
        audio_filepath = os.path.join(audio_directory, audio_filename)
        
        if os.path.exists(audio_filepath):
            return audio_filepath
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': audio_filepath,  # 다운로드할 파일 경로 지정
            'noplaylist': True,
            'extractor_args': {
                'youtube': {
                    'api_key': youtube_api_key
                }
            }
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])  # 파일 다운로드
        
        return audio_filepath
    

    async def get_video_id(self, url):
        # StackOverflow의 고수 개발자님들 충성
        # youtube.com과 youtu.be에 맞는 패턴. http, https, 또는 아무것도 없는 경우를 처리
        regex_patterns = [
                # youtu.be/ID 형식
                r'(?:https?://)?(?:www\.)?youtu\.be/([a-zA-Z0-9_-]{11})',                 
                # youtube.com/watch?v=ID 형식
                r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',                 
                # music.youtube.com/watch?v=ID 형식
                r'(?:https?://)?(?:music\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',                 
                # youtube.com/shorts/ID 형식
                r'(?:https?://)?(?:www\.)?youtube\.com/shorts/([a-zA-Z0-9_-]{11})',  
                # 특정 시간에서 시작하는 동영상
                r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})&t=\d+s', 
                # 플레이리스트 내의 동영상
                r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})&list=([a-zA-Z0-9_-]+)',
                # Start Radio 파라미터가 포함된 동영상
                r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})&list=([a-zA-Z0-9_-]+)&start_radio=1'
        ]

        for pattern in regex_patterns:
            match = re.match(pattern, url)
            if match:
                return match.group(1)  # 비디오 ID 반환
        
        return None

    
    # 음악 재생 커맨드
    @commands.command(name = "play")
    async def play(self, ctx, url: str):

        if ctx.author.voice is None: # 메시지 작성자가 음성 채널에 접속해 있어야 함
            await ctx.send("먼저 음성 채널에 들어가세요")
            return

        voice_channel = ctx.author.voice.channel # 작성자의 채널에 음악이 재생됨
        
        if ctx.voice_client is None: # 봇을 음성 채널에 연결
            vc = await voice_channel.connect()
        else:
            vc = ctx.voice_client

        video_title = await self.extract_video_title(url)
        
        if video_title is None:
            await ctx.send("잘못된 링크입니다.")
            return
        
        self.music_queue.append(url)
        
        if vc.is_playing():
            await ctx.send(f"'{video_title}' 이 큐에 추가되었습니다.")
        else:
            await self.play_next(ctx)
        
        if self.leave_timer is not None:
            self.leave_timer.cancel()
            self.leave_timer = None
            
            
    # 큐에서 다음 음악 재생
    async def play_next(self, ctx):
        vc = ctx.voice_client

        if len(self.music_queue) > 0:
            next_url = self.music_queue.pop(0)
            await self.play_audio(ctx, next_url)
        else:
            if vc is not None:
                self.leave_timer = asyncio.create_task(self.leave_after_timeout(ctx))

    
    # 음악 재생 코드
    async def play_audio(self, ctx, video_url):
        vc = ctx.voice_client

        self.current_song = video_url
        audio_source = await self.download_audio_file(video_url)
        
        if audio_source is None:
            await ctx.send("잘못된 링크입니다.")
            return
        
        vc.play(discord.FFmpegOpusAudio(executable = self.ffmpeg_executable,
                                    source = audio_source,                                  
                                    options = "-vn -filter:a 'volume=0.5'"), # 기본 볼륨 50%
                                    after = lambda e: asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop)) # 재생 중인 음악이 끝나면 play_next 실행
 
        
        video_title = await self.extract_video_title(video_url)
        await ctx.send(f"현재 재생 중: {video_title}")


    # 스킵 커맨드
    @commands.command(name = "skip")
    async def skip(self, ctx):
        if not ctx.voice_client.is_playing():
            await ctx.send("재생 중인 음악이 없습니다.")
            return
        
        if ctx.voice_client is not None:
            ctx.voice_client.stop()
    
    
    # 음악 재생 중지 및 큐 초기화 커맨드
    @commands.command(name = "stop")
    async def stop(self, ctx):
        if ctx.voice_client is not None:
            ctx.voice_client.stop()
            await ctx.voice_client.disconnect()
            await ctx.send("음악 재생이 중지되었습니다.")
        
        self.music_queue.clear()
        
        await ctx.send("큐가 초기화되었습니다.")
        

    # 현재 큐를 확인하는 커맨드
    @commands.group(name = "queue", invoke_without_command = True)
    async def print_queue(self, ctx):
        if len(self.music_queue) == 0 and self.current_song is None:
            await ctx.send("큐가 비어있습니다.")
            return
        
        current_title = await self.extract_video_title(self.current_song)
        await ctx.send(f"현재 재생 중: {current_title}\n")
        
        # 큐의 음악 출력
        if len(self.music_queue) > 0:
            queue_message = "큐에 대기 중인 음악\n"
            for i, video_url in enumerate(self.music_queue, start = 1):
                video_title = await self.extract_video_title(video_url)
                queue_message += f"{i}. {video_title}\n"
            await ctx.send(queue_message)
        
        
    # 큐에서 선택한 음악을 제거하는 커맨드
    @print_queue.command(name = "skip")
    async def queue_skip(self, ctx, number: int):
        # 입력 번호가 0일 경우 현재 재생 중인 음악을 제거함
        if number == 0:
            await self.skip(ctx)
        
        elif number > 0:
            if number <= len(self.music_queue):
                removed_song = self.music_queue.pop(number - 1)
                video_title = await self.extract_video_title(removed_song)
                await ctx.send(f"큐에서 음악을 제거했습니다: {number}. {video_title}")
            else:
                await ctx.send("잘못된 번호입니다.")
    

    # 현재 재생 중인 음악을 일시정지하는 커맨드
    @commands.command(name = "pause")
    async def pause(self, ctx):
        vc = ctx.voice_client

        if not vc or not vc.is_playing():
            await ctx.send("봇이 음악을 재생 중이지 않습니다.")
        elif vc.is_paused():
            await ctx.send("이미 음악이 일시정지되었습니다")
        
        vc.pause()
        await ctx.send("음악을 일시정지했습니다.")

    
    # 일시정지한 음악을 재생하는 커맨드
    @commands.command(name = "resume")
    async def resume(self, ctx):
        vc = ctx.voice_client

        if not vc:
            await ctx.send("봇이 연결되지 않았습니다.")
        elif vc.is_playing():
            await ctx.send("이미 음악이 재생 중입니다.")

        vc.resume()
        await ctx.send("음악을 다시 재생했습니다.")

    
    # 음악을 검색하는 커맨드
    # @commands.command(name = "search")
    
    async def leave_after_timeout(self, ctx):
        await asyncio.sleep(180) # 대기 시간 3분
        if not ctx.voice_client.is_playing() and len(self.music_queue) == 0:
            await ctx.voice_client.disconnect()
            await ctx.send("활동이 없어 봇을 음성 채널에서 내보냈습니다.")
        
# 초기 설정. 명령어의 prefix는 !로 정함
private_intents = discord.Intents.all()
bot = commands.Bot(command_prefix = "!", intents = private_intents)

load_dotenv()
discord_bot_token = os.getenv("DISCORD_BOT_TOKEN")
youtube_api_key = os.getenv("YOUTUBE_API_KEY")
audio_directory = os.getenv("LOCAL_AUDIO_STORAGE")

# 봇이 정상적으로 가동되면 터미널에 "Terminal message"가 출력될 것임. 이때부터 봇 사용
@bot.event
async def on_ready():
    # 봇 인스턴스 생성
    await bot.add_cog(MusicBot(bot)) # 봇 명령어 등록
    await bot.change_presence(status=discord.Status.online, activity=discord.Game("!manual: 매뉴얼 출력")) # 봇의 상태 메시지
    print("Terminal message")

# discord.py에서 제공하는 event callback 함수
@bot.event
async def on_voice_state_update(member, before, after):
    target_user_tag = "personwhoisnotfullyconsciou" # 스윈들러 등장
    # 사용자의 discord tag가 target_user_tag와 같을 때만 동작 
    if before.channel is None and after.channel is not None and (str(member) == target_user_tag):
        voice_channel = after.channel

        if not member.guild.voice_client:
            vc = await voice_channel.connect()
            await play_audio_for_user(vc, "Swindler.mp3", disconnect_after = True)
        else:
            vc = member.guild.voice_client

            if vc.is_playing():
                vc.pause()
                await play_audio_for_user(vc, "Swindler.mp3", disconnect_after = False)
                vc.resume()
            else:
                await play_audio_for_user(vc, "Swindler.mp3", disconnect_after = True)

async def play_audio_for_user(vc, audio_file, disconnect_after = False):
    audio_path = os.path.join(audio_directory, audio_file)
    
    await asyncio.sleep(1)
    
    def after_play(error):
        if error:
            print(f"error name: {error}")
        if disconnect_after:
            after_play = asyncio.run_coroutine_threadsafe(vc.disconnect(), vc.loop)

    vc.play(discord.FFmpegOpusAudio(
        executable = "ffmpeg.exe" if platform.system() == "Windows" else "ffmpeg",
        source = audio_path,
        options = "-vn -filter:a 'volume=0.8'"),
        after = after_play) # expects a callable for the "after" parameter

    if vc.is_playing():
        await asyncio.sleep(4)

# 봇 실행
bot.run(discord_bot_token)
