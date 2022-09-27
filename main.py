import asyncio
import os
import random
import re
import time

import discord

from discord.ext import commands

from art import *
from data import *
from helper import *

intents = discord.Intents.all()
intents.members = True
bot = commands.Bot(command_prefix='ms!', activity=discord.Game(name="ms!help"), intents=intents)

@bot.event
async def on_ready():
    print('======================\n{0.user} is online!\n======================'.format(bot))

@bot.command()
async def template(ctx):
    pass
    
bot.remove_command("help")
@bot.command()
async def help(ctx):
    await ctx.send("Available commands: "+cmd_list)

@bot.command()
async def arthur(ctx):
    await ctx.send(get_aa_quote())

@bot.command()
async def boom(ctx):
    await ctx.send("https://discord.com/channels/391945575886618626/660285290404904982/979716023613792286")

@bot.command(aliases=['clear'])
async def clean(ctx):
    counter = 0
    to_del = []
    not_deleted = True
    while not_deleted:
        not_deleted = False
        async for msg in ctx.channel.history(limit=50):
            if (msg.content.startswith(("ms!","Ms!","mS!","MS!","db!","Db!","dB!","DB!","-p")) or
                msg.author.id == 897321183794573372 or # Ms bot
                msg.author.id == 980918916211695717 or # valorant shop
                msg.author.id == 614109280508968980 or #chip bot
                msg.author.id == 210363111729790977): #duncte
                    not_deleted = True
                    counter += 1
                    to_del.append(msg)
        await ctx.channel.delete_messages(to_del)
        to_del.clear()
    msg = await ctx.send(f"{counter} messages cleaned up")
    await asyncio.sleep(10)
    await msg.delete()

@bot.command()
async def daddy(ctx):
    await ctx.send("https://cdn.discordapp.com/attachments/660285290404904982/970615387341357056/unknown.png")

@bot.command()
async def darius(ctx):
    await ctx.send("""He's got more mobility than Darius, a juggernaut centric on healing in his radius. 
I don't mind that his Q heals a ton, but gore drinker should not get the amp. He isn't a juggernaut, he is a bruiser.""")

@bot.command()
async def dice(ctx, start=1, end=6):
    if start is int and end is int:
        await ctx.send(random.choice(range(start, end + 1)))

@bot.command()
async def dinner(ctx):
    await ctx.send("https://cdn.discordapp.com/attachments/699292316267184248/979656946489655316/unknown.png")

@bot.command()
async def dopa(ctx):
    await ctx.send("https://clips.twitch.tv/SleepyAwkwardMonitorKlappa-EHSxkSxW6qP-Ai2V")

@bot.command(aliases=['5stars'])
async def fivestars(ctx):
    await ctx.send("https://www.suzuki.com.au/vehicles/hatch/swift")

@bot.command()
async def gomu(ctx):
    server = await bot.fetch_guild(server_id)
    gomu = await server.fetch_member(gomu_id)
    
    if gomu.voice is None:
        msg = await ctx.send(f"How is your connection {gomu.mention}?")
        await msg.add_reaction("<:chonkstone:811979419571847239>")
    else:
        await gomu.move_to(None)

@bot.command()
async def hydra(ctx):
    await ctx.send(hydra_art)

@bot.command()
async def inspire(ctx):
    await ctx.send(get_quote())

@bot.command()
async def knock(ctx):
    await ctx.send("https://media.discordapp.net/attachments/660285290404904982/980466548911251526/ezgif-2-2e7fb41497.gif")

@bot.command()
async def ladbrokes(ctx):
    await ctx.send(dollar)


@bot.command()
async def medal(ctx, member: discord.Member=None, days=7):
    if member is None:
        await ctx.send("Tag someone to see their recent clips <:creamonbloke:738031587299426304>")
        return
    if type(days) != int:
        await ctx.send("Please put a number")
    if days < 1:
        await ctx.send("Must be at least 1 day")
    for dict in medal_list:
        if dict['d_id'] == member.id:
            clips = get_recent_clips(dict['m_id'], days)
            embed = discord.Embed(
                title = f"{len(clips)} Clips from {member.display_name} in the last {days} days:", 
                colour = discord.Colour.orange()
            )
            for clip in clips:
                embed.add_field(name=clip['contentTitle'], value=clip['directClipUrl'], inline=False)
            if not clips:
                await ctx.send(f"<:ResidentChriser:944865466424393738> {member.mention} has no recent clips <:ResidentChriser:944865466424393738>")
            else:
                await ctx.send(embed=embed)
            return
    await ctx.send(f"<:ResidentChriser:944865466424393738> {member.mention} has no clips <:ResidentChriser:944865466424393738>")

@bot.command(aliases=['clips'])
async def recent_clips(ctx, days=7):
    if type(days) != int: await ctx.send("Please put a number"); return
    if days < 1: await ctx.send("Must be at least 1 day"); return
    embed = discord.Embed(colour=discord.Colour.orange())
    clip_count = 0
    for dict in medal_list:
        clips_str = ""
        for clip in get_recent_clips(dict['m_id'], days):
            clip_count += 1
            clips_str += f"{clip['contentTitle']}\n{clip['directClipUrl']}\n"
        if clips_str != "": embed.add_field(name=f"{dict['name']}'s clips:", value=clips_str, inline=False)
    if clip_count == 0: await ctx.send(f"<:ResidentChriser:944865466424393738> No recent clips in the last {days} days <:ResidentChriser:944865466424393738>"); return
    embed.title = f"{clip_count} Clips from the last {days} days:"
    await ctx.send(embed=embed)

@bot.command()
async def of(ctx):
    await ctx.send("https://onlyfans.com/iamrandom")

@commands.cooldown(1, 15, commands.BucketType.guild)
@bot.command()
async def oi(ctx, member: discord.Member=None):
    if member is None:
        await ctx.send("Tag someone to piss them off <:karlnoodle:392209143190126593>")
        return
    if member.voice is None:
        return
    initial_ch = member.voice.channel
    vc_list = ctx.message.guild.voice_channels
    vc_list.remove(initial_ch)
    prev = None
    for i in range(7):
        curr = random.choice(vc_list)
        while curr == prev:
            curr = random.choice(vc_list)
        await member.move_to(curr)
        await asyncio.sleep(0.5)
        prev = curr
    await member.move_to(initial_ch)

@oi.error
async def oi_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        msg = await ctx.send(f"ms!oi is on CD for {error.retry_after:.2f}s.")
        await asyncio.sleep(int(error.retry_after))
        await msg.delete()

@bot.command()
async def opgg(ctx):
    args = ctx.message.content[len(os.getenv('PREFIX')):].lower().split()
    if len(args) == 1:
        await ctx.send("put someones league name")
    else:
        await ctx.send(f"https://oce.op.gg/summoners/oce/{args[1]}")

@bot.command()
async def razza(ctx):
    await ctx.send("https://clips.twitch.tv/TenuousCarelessAnacondaMingLee")

@bot.command(aliases=['resetnames'])
async def reset_nicknames(ctx):
    msg = await ctx.send("Are you sure you want to reset all nicknames?")
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")

    def check(reaction, user):
        return str(reaction.emoji) == '✅' or str(reaction.emoji) == '❌'

    try:
        reaction, user = await bot.wait_for('reaction_add', timeout=30.0, check=check)
    except asyncio.TimeoutError:
        await msg.delete()
    else:
        if str(reaction.emoji) == '✅':
            for member in ctx.guild.members:
                for role in member.roles:
                    if role.name == "Secretary" or role.name == "Vice Principal":
                        await member.edit(nick=None)
    await msg.delete()

@commands.cooldown(1, 30, commands.BucketType.guild)
@bot.command()
async def shuffle(ctx):
    start = time.time()
    server = ctx.guild
    the_real_ones = []
    nicks = []
    for member in server.members:
        for role in member.roles:
            if role.name == "Secretary" or role.name == "Vice Principal":
                nicks.append(member.nick)
                the_real_ones.append(member)
    random.shuffle(nicks)
    for member, nick in zip(the_real_ones, nicks):
        await member.edit(nick=nick)
    end = time.time()
    total = end - start
    msg = await ctx.send(f'Shuffled in {total:.2f}s!')
    await asyncio.sleep(5)
    await ctx.message.delete()
    await msg.delete()

@shuffle.error
async def shuffle_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        msg = await ctx.send(f"ms!shuffle is on CD for {error.retry_after:.2f}s.")
        await asyncio.sleep(int(error.retry_after))
        await msg.delete()

@bot.command()
async def snoopy(ctx):
    await ctx.send(snoopy_art)

@bot.command()
async def timer(ctx):
    args = ctx.message.content[len(os.getenv('PREFIX')):].lower().split()
    if len(args) == 1:
        await ctx.send("How long? m:s or s")
    else:
        timer = process_time(args[1])
        if timer is not None:
            await ctx.send(send_timer_msg(timer))
            await do_timer(timer['total'], ctx, bot)
        else:
            await ctx.send("im not that retarded")

@bot.command()
async def yt(ctx):
    await ctx.send("https://www.youtube.com/channel/UCEcv1n1cuUC4jdcrdy71S5Q")

@bot.event
async def on_message(msg):
    if msg.author == bot.user:
        return
    if check_MS(msg.content):
        await msg.add_reaction("🇲")
        await msg.add_reaction("🇸")
        await msg.channel.send("MS")
    if re.search("^HUGH$",msg.content):
        await msg.channel.send("JAYNISS")
    if re.search("beast", msg.content, re.IGNORECASE):
        await msg.add_reaction("🦍")
    if re.search("boom", msg.content, re.IGNORECASE):
        await msg.add_reaction("💥")
    if re.search("holy", msg.content, re.IGNORECASE):
        await msg.add_reaction("⛪")
    if re.search("<@423369088681902080>", msg.content, re.IGNORECASE):
        await msg.add_reaction("<:chonkstone:811979419571847239>")

    await bot.process_commands(msg)

@bot.event
async def on_voice_state_update(member, before, after):

    if after.channel is None:
        ch = await bot.fetch_channel(660285290404904982)
        msg = await ch.send(f"{member.mention} Where are you going?")
        await asyncio.sleep(5)
        await msg.delete()
       
@bot.event
async def on_typing(channel, user, when):
    if channel.guild.id == server_id:
        msg = await channel.send(random.choice(typing_pic_links))
        await asyncio.sleep(1.5)
        await msg.delete()
        
bot.run('token here')