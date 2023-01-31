import sys

import discord
from discord.ext import commands, tasks

import googleapiclient.discovery
import googleapiclient.errors
import youtube_dl
import html
import asyncio
import isodate

youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=sys.argv[2])

def youtube_search(query):
    request = youtube.search().list(
        type='video',
        q=query,
        part='id,snippet',
        maxResults=1,
        fields='items(id(videoId),snippet(title,thumbnails))'
    )

    response = request.execute()
    return response

def get_youtube_video_duration(id):
    # Get the video data
    video_response = youtube.videos().list(
        part='contentDetails',
        id=id
    ).execute()

    # Get the video length
    duration = str(isodate.parse_duration(video_response['items'][0]['contentDetails']['duration']))
    if duration[0] == '0':
        duration = duration[2:]
    return f'[{duration}]'

def create_embed(video_dict: dict, queued=False):
    embed = discord.Embed(
        colour = discord.Colour.orange()
    )
    embed_str = "Added to queue: " if queued else "Now playing: "
    embed.add_field(name='\u200b', value=f"{embed_str}[{video_dict['title']}]({video_dict['video_url']})", inline=False)
    embed.set_thumbnail(url=video_dict['thumb_url'])
    return embed

class music_player(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.queue = []
        self.curr_vid = None
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("Music cog is online")
    
    async def play_queue(self, vc):
        while True:
            if len(self.queue) > 0:
                # Get the next video URL from the queue
                self.curr_vid = self.queue.pop(0)
                audio_url = self.curr_vid['audio_url']

                # Play the audio
                vc.play(discord.FFmpegPCMAudio(audio_url, before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"))

                # Wait for the audio to finish playing
                while vc.is_playing():
                    await asyncio.sleep(1)
                
                # Reset curr vid in case it's the last video
                self.curr_vid = None
            else:
                # If the queue is empty, wait for a new video to be added
                await asyncio.sleep(1)

    def add_to_queue(self, query, channel_id):
        results = youtube_search(query)
        video_id = results['items'][0]['id']['videoId']
        video_url = f'https://www.youtube.com/watch?v={video_id}' 
        title = html.unescape(results['items'][0]['snippet']['title'])
        thumb_url = results['items'][0]['snippet']['thumbnails']['default']['url'].replace('default', 'hq720')
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            stream = ydl.extract_info(video_url, download=False)
            audio_url = stream['formats'][0]['url']
        
        video_dict = {
            'title': title,
            'thumb_url': thumb_url,
            'video_url': video_url,
            'audio_url': audio_url,
            'duration': get_youtube_video_duration(video_id),
            'sent_channel': channel_id,
        }

        self.queue.append(video_dict)
        return video_dict

    @commands.command(aliases=['p'])
    async def play(self, ctx, *, query):
        # Get the user's voice channel and connect to it
        channel = ctx.message.author.voice.channel
        if channel is None:
            await ctx.send("You are not connected to a voice channel.")
            return
        vc = ctx.voice_client
        if vc is None:
            vc = await channel.connect()
        
        video_dict = self.add_to_queue(query, channel)
        if vc.is_playing():
            await ctx.send(embed=create_embed(video_dict, queued=True))
        else:
            await ctx.send(embed=create_embed(video_dict, queued=False))
            await self.play_queue(vc)

    @commands.command()
    async def pause(self, ctx):
        vc = ctx.voice_client
        if vc.is_paused() is True:
            vc.resume()
            await ctx.send("Audio has been resumed")
        else:
            vc.pause()
            await ctx.send("Audio is now paused")
    
    @commands.command(aliases=['s'])
    async def skip(self, ctx):
        vc = ctx.voice_client
        vc.stop()

    @commands.command(aliases=['q'])
    async def queue(self, ctx):
        embed = discord.Embed(
            title = f"Queue: {len(self.queue)} song{'s'*(len(self.queue) > 1)} remaining",
            colour = discord.Colour.orange()
        )
        for count, video in enumerate(self.queue):
            embed.add_field(name=f"{count+1}. `{video['duration']}` {video['title']}", value='\u200b', inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def clearqueue(self, ctx):
        self.queue = []
        await ctx.send("Queue has been cleared!")

    @commands.command(aliases=['np'])
    async def nowplaying(self, ctx):
        #TODO print embed with seek bar
        pass

    @commands.command()
    async def seek(self, ctx):
        pass

    @commands.command()
    async def stop(self, ctx):
        vc = ctx.voice_client
        vc.stop()
        await vc.disconnect()
        await ctx.send("Queue cleared, bye bye :)")

async def setup(bot):
    await bot.add_cog(music_player(bot))
