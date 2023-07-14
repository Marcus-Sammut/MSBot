import asyncio
import datetime
import os
import pathlib
import random
import re
import sys
import time

import discord
from discord.ext import commands, tasks

import art
import data
import helper

intents = discord.Intents.all()
intents.presences = True
intents.members = True
bot = commands.Bot(command_prefix='ms!', activity=discord.Game(name="ms!help"), intents=intents)

#TODO ping riot api every minute to check if jordan is in game, BY HIMSELF then ping @everyone

@bot.event
async def on_ready():
    await bot.fetch_channel(data.id_dict['general'])
    await bot.fetch_guild(data.id_dict['server'])
    if not daily_notification.is_running():
        daily_notification.start()
    if not jordan_water.is_running():
        jordan_water.start()
    print(f'======================\n{bot} is online!\n======================')

@tasks.loop(hours=24)
async def daily_notification():
    general = bot.get_channel(data.id_dict['general'])
    # await general.send("Do your daily vote: https://www.webnovel.com/book/civilization_21272045006019305#:~:text=Weekly%20Power%20Status")
    res_code = helper.get_recent_clips(1,1)
    server = bot.get_guild(data.id_dict['server'])
    ms = await server.fetch_member(data.id_dict['MS'])
    await general.send(f"{ms.mention} medal.tv api response code: {res_code}")

@tasks.loop(time=[datetime.time(i,random.randint(0,59)) for i in range (24)])
async def jordan_water():
    server = bot.get_guild(data.id_dict['server'])
    jordan = server.get_member(data.id_dict['jordan'])
    if jordan.status == discord.Status.online:
        general = bot.get_channel(data.id_dict['general'])
        await general.send(f"{jordan.mention} This is a reminder to drink water and stay hydrated!")

bot.remove_command("help")
@bot.command(aliases=['help'])
async def show_commands(ctx):
    await ctx.send("Available commands: "+data.cmd_list)

@bot.command()
async def aram(ctx):
    #TODO
    await ctx.send(helper.get_aa_quote())

@bot.command()
async def arthur(ctx):
    await ctx.send(helper.get_aa_quote())

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
        async for msg in ctx.channel.history(limit=100):
            if (msg.content.lower().startswith(("ms!","db!","-p")) or msg.author.id in list(data.bot_ids.values())):
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
    await ctx.send("He's got more mobility than Darius, a juggernaut centric on healing in his radius.\n\
    \rI don't mind that his Q heals a ton, but gore drinker should not get the amp. He isn't a juggernaut, he is a bruiser.")

@bot.command()
async def dice(ctx, start=1, end=6):
    if start is int and end is int:
        await ctx.send(random.choice(range(start, end + 1)))

@bot.command()
async def dinner(ctx):
    await ctx.send("https://cdn.discordapp.com/attachments/699292316267184248/979656946489655316/unknown.png")

@bot.command()
async def doItAgain(ctx):
    #TODO
    pass

@bot.command()
async def dopa(ctx):
    await ctx.send("https://clips.twitch.tv/SleepyAwkwardMonitorKlappa-EHSxkSxW6qP-Ai2V")

@bot.command(aliases=['5stars'])
async def fivestars(ctx):
    await ctx.send("https://www.suzuki.com.au/vehicles/hatch/swift")

@bot.command()
async def github(ctx):
    await ctx.send("https://github.com/Marcus-Sammut/MSBot")

@bot.command()
async def gomu(ctx):
    server = bot.get_guild(data.id_dict['server'])
    kingston = await server.fetch_member(data.id_dict['gomu'])
    if kingston.voice is None:
        msg = await ctx.send(f"Hey {kingston.mention}, how are you doing?")
        await msg.add_reaction("<:chonkstone:811979419571847239>")
    else:
        await kingston.move_to(None)

@bot.command()
async def hydra(ctx):
    await ctx.send(art.hydra_art)

@bot.command()
async def inspire(ctx):
    await ctx.send(helper.get_quote())

@bot.command(aliases=helper.jordan_list())
async def JORDAN(ctx):
    await ctx.message.add_reaction("🇯🇴")
    msg = await ctx.send("https://medal.tv/games/league-of-legends/clips/jaFyE1FuJs1HX")
    await msg.add_reaction("🇯🇴")

@bot.command()
async def knock(ctx):
    await ctx.send("https://media.discordapp.net/attachments/660285290404904982/980466548911251526/ezgif-2-2e7fb41497.gif")

@bot.command()
async def ladbrokes(ctx):
    await ctx.send(art.dollar)

@bot.command()
async def log(ctx):
    await ctx.send(pathlib.Path('voice_log.txt').read_text().strip())

@bot.command()
async def medal(ctx, member: discord.Member=None, days=7):
    # TEMP: remove when code is 200
    await ctx.send("ms medal is dead")
    return
    # end block
    if member is None:
        await ctx.send("Tag someone to see their recent clips <:creamonbloke:738031587299426304>")
        return
    if isinstance(days) != int:
        await ctx.send("Please put a number")
        return
    if days < 1:
        await ctx.send("Must be at least 1 day")
        return
    sleeper_emoji = "<:ResidentChriser:944865466424393738>"
    for user in data.medal_user_list:
        if user['d_id'] == member.id:
            clips = helper.get_recent_clips(user['m_id'], days)
            embed = discord.Embed(
                title = f"{len(clips)} Clips from {member.display_name} in the last {days} days:",
                colour = discord.Colour.orange()
            )
            for clip in clips:
                game_name = helper.get_game_name(int(clip['categoryId']))
                embed.add_field(name=f"{clip['contentTitle']} {game_name}", value=clip['directClipUrl'], inline=False)
            if not clips:
                await ctx.send(f"{sleeper_emoji} {member.mention} has no recent clips {sleeper_emoji}")
            else:
                await ctx.send(embed=embed)
            return
    await ctx.send(f"{sleeper_emoji} {member.mention} has no clips {sleeper_emoji}")

@bot.command()
async def millionaire(ctx):
    await ctx.send("soon:tm:")

@bot.command()
async def multi(ctx):
    msgs = []
    for multi_pic in os.listdir('./multis'):
        msg = await ctx.send(multi,file=discord.File(f'./multis/{multi_pic}'))
        msgs.append(msg)
    await ctx.message.delete()
    await asyncio.sleep(120)
    await ctx.channel.delete_messages(msgs)

@bot.command(aliases=['clips'])
async def recent_clips(ctx, days=7):
    if isinstance(days) != int:
        await ctx.send("Please put a number")
        return
    if days < 1:
        await ctx.send("Must be at least 1 day")
        return
    embed = discord.Embed(colour=discord.Colour.orange())
    clip_count = 0
    for user in data.medal_user_list:
        clips_str = ""
        for clip in helper.get_recent_clips(user['m_id'], days):
            clip_count += 1
            game_name = helper.get_game_name(int(clip['categoryId']))
            clips_str += f"{clip['contentTitle']} {game_name}\n{clip['directClipUrl']}\n"
        if clips_str != "":
            embed.add_field(name=f"{user['name']}'s clips:", value=clips_str, inline=False)
    if clip_count == 0:
        sleeper_emoji = "<:ResidentChriser:944865466424393738>"
        await ctx.send(f"{sleeper_emoji} No recent clips in the last {days} days {sleeper_emoji}")
        return
    embed.title = f"{clip_count} Clip{'s' if clip_count > 1 else ''} from the last {days} days:"
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
    _vcs = ctx.message.guild.voice_channels
    _vcs.remove(initial_ch)
    vc_list = [vc for vc in _vcs if vc.name != 'Mary Juan']
    prev = None
    for _ in range(7):
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
async def ooo(ctx):
    start_str = "JOOOOO"
    general = bot.get_channel(data.id_dict['general'])
    msg = await general.send(start_str)
    for _ in range(10):
        start_str += "OOOOOO"
        await msg.edit(content=start_str)
        await asyncio.sleep(1.5)
    await msg.edit(content=start_str+"RDAN")

@bot.command()
async def opgg(ctx, name: None):
    if name is None:
        await ctx.send("put someones league name")
    else:
        await ctx.send(f"https://oce.op.gg/summoners/oce/{name}")

@bot.command()
async def patchnotes(ctx):
    with open('patchnotes.txt', 'r') as notes:
        await ctx.send(notes.read())

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
            await msg.delete()
            for member in ctx.guild.members:
                for role in member.roles:
                    if role.name in ('Secretary', 'Vice Principal'):
                        await member.edit(nick=None)
    await ctx.send("All nicknames reset!")

@commands.cooldown(1, 30, commands.BucketType.guild)
@bot.command()
async def shuffle(ctx):
    start = time.time()
    server = ctx.guild
    the_real_ones = []
    nicks = []
    for member in server.members:
        for role in member.roles:
            if role.name in ('Secretary', 'Vice Principal'):
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
    await ctx.send(art.snoopy_art)

@bot.command()
async def sro(ctx):
    await ctx.send(file=discord.File('bwu.mp3'))
    #TODO
    # tts cmd where msbot joins the discord and says the tts and leaves+----+-+++

@bot.command()
async def timer(ctx, duration: None):
    if duration is None:
        await ctx.send("How long? minutes:seconds or seconds")
        return
    # TODO: try catch block, and throw exeptions in process time
    try:
        duration_dict = helper.process_time(duration)
    except:
        pass
    # if timer := helper.process_time(time):
    #     await ctx.send(helper.send_timer_msg(timer))
    #     await helper.do_timer(ctx, timer['total'], bot)

@bot.command()
async def yt(ctx):
    await ctx.send("https://www.youtube.com/channel/UCEcv1n1cuUC4jdcrdy71S5Q")

@bot.event
async def on_message(msg):
    if msg.author == bot.user:
        return
    if msg.author.id == data.id_dict['gomu']:
        await msg.add_reaction("<:chonkstone:811979419571847239>")
    elif msg.author.id == 882491278581977179: #vibr music bot
        await asyncio.sleep(600)
        await msg.delete()
    if helper.check_MS(msg.content):
        await msg.add_reaction("🇲")
        await msg.add_reaction("🇸")
        await msg.channel.send("MS")
    if val_count := len(re.findall(r'\bval\b',msg.content, re.IGNORECASE)):
        await msg.reply("💀💀💀💀💀💀💀\n"*val_count, mention_author=False)
    if re.search("^HUGH$",msg.content):
        await msg.channel.send("JAYNISS")
    else:
        msg_split = msg.content.split()
        for word in msg_split:
            if re.search("beast", word, re.IGNORECASE):
                await msg.add_reaction("🦍")
            if re.search("boom", word, re.IGNORECASE):
                await msg.add_reaction("💥")
            if re.search("holy", word, re.IGNORECASE):
                await msg.add_reaction("⛪")
            if re.search("<@423369088681902080>", word, re.IGNORECASE):
                await msg.add_reaction("<:chonkstone:811979419571847239>")

    await bot.process_commands(msg)

@bot.event
async def on_voice_state_update(member, before, after):
    name = member.nick if member.nick is not None else member.name
    msg = None
    general = bot.get_channel(data.id_dict['general'])
    if before.channel is None:
        msg = await general.send(f"Hi {name}")
        helper.append_voice_log(name, 'joined')
    elif after.channel is None:
        if member.id == data.id_dict['jordan']:
            msg = await general.send(f"DID YOU SAY BYE {member.mention}?")
        else:
            msg = await general.send(f"{name} Where are you going?")
        #TODO ms!lastseen, shows when they were last in voice chat
        helper.append_voice_log(name, 'left')
    if msg is not None:
        await asyncio.sleep(30)
        await msg.delete()

@bot.event
async def on_typing(channel, user, when):
    if channel.guild.id == data.id_dict['server']:
        msg = await channel.send(random.choice(data.typing_pic_links))
        await asyncio.sleep(1.5)
        await msg.delete()

@bot.event
async def on_presence_update(before, after):
    if before.status != discord.Status.offline:
        return
    if any(twins := [after.id == data.id_dict['jordan'], after.id == data.id_dict['colden']]):
        start_str = f"{after.mention} {'JOOOOO' if twins[0] else 'COOOOO'}"
        name_end = f"{'RDAN' if twins[0] else 'LDEN'}"
        general = bot.get_channel(data.id_dict['general'])
        msg = await general.send(start_str)
        for _ in range(10):
            start_str += "OOOOOO"
            await msg.edit(content=start_str)
            await asyncio.sleep(1.3)
        await msg.edit(content=start_str+name_end)

bot.run(sys.argv[1])
