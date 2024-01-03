import asyncio
import datetime
import functools
import itertools
import os
import pathlib
import random
import re
import sys
import time

import requests
import httpx
import humanize

import discord
from discord.ext import commands, tasks
from discord.ui import Select, View

import art
import data
import helper

intents = discord.Intents.all()
intents.presences = True
intents.members = True
bot = commands.Bot(command_prefix='ms!', activity=discord.Game(name="ms!help"), intents=intents)

RIOT_API_KEY = sys.argv[2]

@bot.event
async def on_ready():
    await bot.fetch_channel(data.id_dict['general'])
    await bot.fetch_channel(data.id_dict['medieval'])
    await bot.fetch_guild(data.id_dict['server'])
    await bot.fetch_user(240650380227248128)
    # ping free champ rotation to check if api key is working, invalid key would return 403
    if riot_key_is_valid := helper.is_riot_key_valid(RIOT_API_KEY):
        async def get_encrypted_riot_ids(user: dict):
            async with httpx.AsyncClient() as client:
                res = await client.get(f"https://oc1.api.riotgames.com/lol/summoner/v4/summoners/by-name/{user['lol_name']}?api_key={RIOT_API_KEY}")
                if res.status_code != 200:
                    return
                user['encrypted_id'] = dict(res.json())['id']

        while no_ids := [u for u in data.discord_id_list if not u['encrypted_id']]:
            try:
                await asyncio.gather(*map(get_encrypted_riot_ids, no_ids))
            except:
                pass
    if not check_who_is_online_minecraft.is_running():
        check_who_is_online_minecraft.start()
    # if not daily_notification.is_running():
    #     daily_notification.start()
    if not validate_riot_key_task.is_running() and riot_key_is_valid:
        validate_riot_key_task.start()
    if not jordan_aram.is_running() and riot_key_is_valid:
        jordan_aram.start()
    if not check_intlist.is_running() and riot_key_is_valid:
        check_intlist.start()
    if not jordan_water.is_running():
        jordan_water.start()
    print(f'======================\n{bot.user} is online!\n======================')

PREV_ONLINE_PLAYERS = set()
@tasks.loop(seconds=15)
async def check_who_is_online_minecraft():
    if (online_players := helper.get_players_on_server('51.161.198.152', 2082)) == PREV_ONLINE_PLAYERS:
        return
    
    if just_joined := [p for p in online_players if p not in PREV_ONLINE_PLAYERS]:
        medieval = bot.get_channel(data.id_dict['medieval'])
        if len(just_joined) == 1:
            await medieval.send(f"{just_joined[0]} just joined the server!")
        else:
            await medieval.send(f"These players just joined the server: {', '.join(sorted(just_joined))}")

@tasks.loop(seconds=30)
async def validate_riot_key_task():
    if not helper.is_riot_key_valid(RIOT_API_KEY):
        validate_riot_key_task.stop()
        jordan_aram.stop()
        check_intlist.stop()

JORDAN_CURR_GAME_ID = None
@tasks.loop(seconds=60)
async def jordan_aram():
    global JORDAN_CURR_GAME_ID
    jordan_id: int = [user['encrypted_id'] for user in data.discord_id_list if user['lol_name'] == 'iamrandom'][0]
    res = requests.get(f"https://oc1.api.riotgames.com/lol/spectator/v4/active-games/by-summoner/{jordan_id}?api_key={RIOT_API_KEY}")
    if res.status_code == 404:
        JORDAN_CURR_GAME_ID = None
        return
    elif not res.ok:
        return
    match = dict(res.json())
    if match['gameId'] == JORDAN_CURR_GAME_ID:
        return
    JORDAN_CURR_GAME_ID = match['gameId']
    players: set = {player['summonerName'].replace(' ', '').lower() for player in match['participants']}
    if not players & data.carlo_chimps_league_names:
        role_mention_list = [f"<@&{role}>" for role in data.role_ids.values()]
        general = bot.get_channel(data.id_dict['general'])
        await general.send(f"{' '.join(role_mention_list)} JORDAN IS PLAYING LEAGUE SOLO <https://www.op.gg/summoners/oce/iamrandom/ingame>")

@tasks.loop(seconds=40)
async def check_intlist():
    async def get_async_inters(user: dict, inters: set):
        server = bot.get_guild(data.id_dict['server'])
        async with httpx.AsyncClient() as client:
            if (member := server.get_member(user['d_id'])).status == discord.Status.offline:
                return None
            res = await client.get(f"https://oc1.api.riotgames.com/lol/spectator/v4/active-games/by-summoner/{user['encrypted_id']}?api_key={RIOT_API_KEY}")
            if res.status_code == 404:
                user['currgameid'] = None
                return None
            elif res.status_code >= 400:
                return None
            match = dict(res.json())
            if match['gameId'] == user['curr_game_id']:
                return None
            user['curr_game_id'] = match['gameId']
            players: set = {player['summonerName'].replace(' ', '').lower() for player in match['participants']}
            if inters_in_game := players & inters:
                general = bot.get_channel(data.id_dict['general'])
                await general.send(f"{member.mention} {'THESE INTERS ARE' if len(inters_in_game) > 1 else 'THIS INTER IS'} IN YOUR GAME RIGHT NOW: {', '.join(i for i in inters_in_game)}")

    with open('intlist.txt', 'r', encoding='UTF-8') as intlist_file:
        inters: set = {re.search(r'^- \[(.*)\]\(<https', inter).group(1).replace(' ', '').lower() for inter in intlist_file.readlines()}
    try:
        await asyncio.gather(*map(functools.partial(get_async_inters, inters=inters), data.discord_id_list))
    except:
        pass

@tasks.loop(hours=24)
async def daily_notification():
    general = bot.get_channel(data.id_dict['general'])
    await general.send("Do your daily vote: https://www.webnovel.com/book/civilization_21272045006019305#:~:text=Weekly%20Power%20Status")

@tasks.loop(time=[datetime.time(i,random.randint(0,59)) for i in range (24)])
async def jordan_water():
    if random.randint(61,70) == 69:
        jordan_water.change_interval(time=[datetime.time(i,random.randint(0,59)) for i in range (24)])
    server = bot.get_guild(data.id_dict['server'])
    jordan = server.get_member(data.id_dict['jordan'])
    if jordan.status == discord.Status.online:
        general = bot.get_channel(data.id_dict['general'])
        await general.send(f"{jordan.mention} This is a reminder to drink water and stay hydrated!", silent=True)

bot.remove_command("help")
@bot.command()
async def help(ctx: commands.Context):
    await ctx.send("Available commands: " + data.cmd_list)

@bot.command()
async def aram(ctx: commands.Context, spots: str='', *, game: str=None):
    if spots.lower() == 'help':
        await ctx.send("Usage: ms!aram [spots remaining] [game name]")
        return
 
    role_mention_list = [f"<@&{role}>" for role in data.role_ids.values()]
    spots_str = ''
    if spots and spots.isnumeric():
        spots_str = f"{spots} spot{'s' if spots != '1' else ''} left!"
    await ctx.send(f'{game if game else "ARAM"}? {spots_str} {" ".join(role_mention_list)}')

@bot.command()
async def arthur(ctx: commands.Context):
    await ctx.send(f'"{random.choice(data.arthur_quotes)}" - Arthur Ang')

@bot.command()
async def boom(ctx: commands.Context):
    await ctx.send("https://discord.com/channels/391945575886618626/660285290404904982/979716023613792286")

@bot.command(aliases=['clean'])
async def clear(ctx: commands.Context):
    clearing_msg = await ctx.send("Cleared 0 bot messages...")
    counter = 0
    msgs_to_delete = []
    not_deleted = True
    while not_deleted:
        not_deleted = False
        async for msg in ctx.channel.history(limit=100):
            if msg.id == clearing_msg.id:
                continue
            if (msg.content.lower().startswith(("ms!","db!","-p")) or msg.author.id in list(data.bot_ids.values())):
                not_deleted = True
                counter += 1
                msgs_to_delete.append(msg)
        if not not_deleted:
            msgs_to_delete.append(clearing_msg)
        if not_deleted:
            clearing_msg = await clearing_msg.edit(content=f"Cleared {counter} bot messages...")
        await ctx.channel.delete_messages(msgs_to_delete)
        msgs_to_delete.clear()
    await ctx.send(f"{counter} messages cleared!", delete_after=20)

@bot.command()
async def darius(ctx: commands.Context):
    await ctx.send("He's got more mobility than Darius, a juggernaut centric on healing in his radius.\n\
    \rI don't mind that his Q heals a ton, but gore drinker should not get the amp. He isn't a juggernaut, he is a bruiser.")

@bot.command()
async def dice(ctx: commands.Context, start: int=1, end: int=6):
    if start is int and end is int:
        await ctx.send(random.choice(range(start, end + 1)))

@bot.command()
async def dinner(ctx: commands.Context):
    await ctx.send("https://cdn.discordapp.com/attachments/699292316267184248/979656946489655316/unknown.png")

@bot.command()
async def dopa(ctx: commands.Context):
    await ctx.send("RIP ms!dopa\nhttps://clips.twitch.tv/SleepyAwkwardMonitorKlappa-EHSxkSxW6qP-Ai2V")

@bot.command(aliases=['5stars'])
async def fivestars(ctx: commands.Context):
    await ctx.send("https://www.suzuki.com.au/vehicles/hatch/swift")

@bot.command()
async def github(ctx: commands.Context):
    await ctx.send("https://github.com/Marcus-Sammut/MSBot")

@bot.command()
async def gomu(ctx: commands.Context):
    server = bot.get_guild(data.id_dict['server'])
    kingston = await server.fetch_member(data.id_dict['gomu'])
    if kingston.voice is None:
        msg = await ctx.send(f"Hey {kingston.mention}, how are you doing?")
        await msg.add_reaction("<:chonkstone:811979419571847239>")
    else:
        await kingston.move_to(None)

@bot.command()
async def grind(ctx: commands.Context):
    await ctx.send("<https://www.op.gg/multisearch/oce?summoners=2hrpoo,2kgpoo,2kmpoo,devel,acekingsuited,suzuki,suzukii,hellbreak,pineapplepie,plueblue>")

@bot.command()
async def hydra(ctx: commands.Context):
    await ctx.send(art.hydra_art)

@bot.command(aliases=['addil', 'addIL', 'addIl', 'addiL'])
async def addintlist(ctx: commands.Context, *, name: str=None):
    if not name or name.lower() == 'help':
        await ctx.send("Usage example: ms!addintlist iamrandom")
        return
    
    with open('intlist.txt', 'a', encoding='UTF-8') as int_list:
        inter_str = f'- [{name}](<https://www.op.gg/summoners/oce/{name.replace(" ", "%20")}>)\n'
        int_list.write(inter_str)
    
    to_del = []
    to_del.append(ctx.message)
    to_del.append(await ctx.send(f"{name} has been added to the MSBot int list!"))
    to_del.append(await ctx.send(f"<https://www.op.gg/summoners/oce/{name.replace(' ', '%20')}>"))
    await asyncio.sleep(60)
    try:
        await ctx.channel.delete_messages(to_del)
    except discord.errors.NotFound:
        pass

@bot.command(aliases=['removeil', 'removeIL', 'removeIl', 'removeiL', 'deleteil', 'deleteIL', 'deleteIl', 'deleteiL'])
async def removeintlist(ctx: commands.Context, *, name: str=None):
    if not name or name.lower() == 'help':
        await ctx.send("Usage example: ms!removeintlist iamrandom")
        return
    
    with open('intlist.txt', 'r', encoding='UTF-8') as intlist_file:
        int_list = intlist_file.readlines()

    to_del = []
    if (new_int_list := [inter for inter in int_list if not re.search(rf"^- \[{name}\]\(<https", inter, re.IGNORECASE)]) == int_list:
        to_del.append(await ctx.send(f"{name} is not in the MSBot int list!"))
    else:
        with open('intlist.txt', 'w', encoding='UTF-8') as intlist_file:
            intlist_file.writelines(new_int_list)
        to_del.append(await ctx.send(f"{name} has been removed from the MSBot int list!"))
    
    to_del.append(ctx.message)
    await asyncio.sleep(60)
    try:
        await ctx.channel.delete_messages(to_del)
    except discord.errors.NotFound:
        pass

@bot.command(aliases=['noteil', 'noteIL', 'noteIl', 'noteiL'])
async def noteintlist(ctx: commands.Context):
    with open('intlist.txt', 'r', encoding='UTF-8') as intlist_file:
        lines = intlist_file.readlines()
    inters = {re.search(r'^- \[(.*)\]\(<https', line).group(1): index for index, line in enumerate(lines)}

    select = Select(
        placeholder='Choose an inter!',
        options=[discord.SelectOption(label=inter, emoji=random.choice('🐄🧟🤖💩💀🥶🤬🤢🤡👺🙈🐷🐔🦍🐍🐧')) for inter in inters.keys()]
    )
    
    select_msg = None

    to_del = []
    
    async def inter_select_callback(interaction: discord.Interaction):
        await select_msg.delete()
        
        inter = select.values[0]
        line_index = inters[inter]
                
        response = await interaction.response.send_message(f'Please type the note to add for {inter}, or type \'clear\' to remove the note:', ephemeral=True)
        
        def check(msg):
            return msg.author == ctx.author
        
        reply_msg = await bot.wait_for('message', check=check)
        note = reply_msg.content
        
        if note == 'clear':
            note = None
        
        lines[line_index] = lines[line_index].split(' | ')[0].strip() + f" | {note}" * (not not note) + '\n'
        with open('intlist.txt', 'w', encoding='UTF-8') as intlist_file:
            intlist_file.writelines(lines)
        updated_msg = await ctx.send(f"Int list note updated for {inter}!")
        
        await asyncio.sleep(10)
        to_del.append(response)
        to_del.append(reply_msg)
        to_del.append(updated_msg)
        try:
            await ctx.channel.delete_messages(to_del)
        except:
            pass
    
    select.callback = inter_select_callback
    
    view = View()
    view.add_item(select)
    #TODO only ctx.author can see
    select_msg = await ctx.send("Choose an inter from below:", view=view)
    to_del.append(ctx.message)

@bot.command(aliases=['il', 'IL', 'Il', 'iL'])
async def intlist(ctx: commands.Context):
    msg = await ctx.send("These dickheads are on the MSBot int list:\n" + pathlib.Path('intlist.txt').read_text(encoding='UTF-8').strip())
    await asyncio.sleep(60)
    try:
        await ctx.message.delete()
        await msg.delete()
    except discord.errors.NotFound:
        pass

@bot.command(aliases=[f"J{'O'*i}RDAN" for i in range(2,101)])
async def JORDAN(ctx: commands.Context):
    await ctx.message.add_reaction("🇯🇴")
    msg = await ctx.send("https://medal.tv/games/league-of-legends/clips/jaFyE1FuJs1HX")
    await msg.add_reaction("🇯🇴")

@bot.command()
async def knock(ctx: commands.Context):
    await ctx.send("https://media.discordapp.net/attachments/660285290404904982/980466548911251526/ezgif-2-2e7fb41497.gif")

@bot.command()
async def ladbrokes(ctx: commands.Context):
    await ctx.send(art.dollar)

@bot.command()
async def log(ctx: commands.Context):
    msg = await ctx.send(pathlib.Path('voice_log.txt').read_text(encoding='UTF-8').strip(), silent=True, allowed_mentions=discord.AllowedMentions.none())
    await asyncio.sleep(60)
    try:
        await ctx.channel.delete_messages([msg, ctx.message])
    except discord.errors.NotFound:
        pass

@bot.command()
async def medal(ctx: commands.Context, member: discord.Member=None, days=7):
    if member is None:
        await ctx.send("Tag someone to see their recent clips <:creamonbloke:738031587299426304>")
        return
    if not isinstance(days, int):
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
                embed_str = f"{clip['contentTitle']}"
                if game_name := helper.get_game_name(int(clip['categoryId'])):
                    embed_str += f" {game_name}"
                readable_timestamp = humanize.naturaltime(datetime.datetime.fromtimestamp(clip['createdTimestamp']/1000))
                embed_str += f" - {readable_timestamp}"
                embed.add_field(name=embed_str, value=clip['directClipUrl'], inline=False)
            if not clips:
                await ctx.send(f"{sleeper_emoji} {member.mention} has no recent clips {sleeper_emoji}", silent=True, allowed_mentions=discord.AllowedMentions.none())
            else:
                await ctx.send(embed=embed)
            return
    await ctx.send(f"{sleeper_emoji} {member.mention} has no clips {sleeper_emoji}", silent=True, allowed_mentions=discord.AllowedMentions.none())

@bot.command()
async def multi(ctx: commands.Context):
    msgs = []
    for multi_pic in os.listdir('./multis'):
        msgs.append(await ctx.send(file=discord.File(f'./multis/{multi_pic}')))
    try:
        await ctx.message.delete()
        await asyncio.sleep(90)
        await ctx.channel.delete_messages(msgs)
    except discord.errors.NotFound:
        pass

@bot.command(aliases=['clips'])
async def recent_clips(ctx: commands.Context, days=7):
    if not isinstance(days, int):
        await ctx.send("Please put a number")
        return
    if days < 1:
        await ctx.send("Must be at least 1 day")
        return
    
    embed = discord.Embed(colour=discord.Colour.orange())
    clip_count = 0
    for user in data.medal_user_list:
        if not (recent_user_clips := helper.get_recent_clips(user['m_id'], days)):
            continue
        clips_str = ""
        clip_count += len(recent_user_clips)
        for idx, clip in enumerate(recent_user_clips, start=0):
            clip_str = f"{clip['contentTitle']}"
            if game_name := helper.get_game_name(int(clip['categoryId'])):
                clip_str += f" {game_name}"
            readable_timestamp = humanize.naturaltime(datetime.datetime.fromtimestamp(clip['createdTimestamp']/1000))
            clip_str += f" - {readable_timestamp}"
            if len(clips_str) + len(clip_str) > 1000:
                remaining_clips: int = len(recent_user_clips) - idx
                clips_str += f"and {remaining_clips} more clip{'s' if remaining_clips != 1 else ''}"
            else:
                clips_str += f"{clip_str}\n{clip['directClipUrl']}\n"
        embed.add_field(name=f"{user['name']}'s clips:", value=clips_str, inline=False)
    
    if clip_count == 0:
        sleeper_emoji = "<:ResidentChriser:944865466424393738>"
        await ctx.send(f"{sleeper_emoji} No recent clips in the last {days} days {sleeper_emoji}")
        return
    
    embed.title = f"{clip_count} Clip{'s' if clip_count > 1 else ''} from the last {days} days:"
    await ctx.send(embed=embed)

@bot.command()
async def of(ctx: commands.Context):
    await ctx.send("https://onlyfans.com/iamrandom")

@commands.cooldown(1, 15, commands.BucketType.user)
@bot.command()
async def oi(ctx: commands.Context, member: discord.Member=None, moves=7):
    if not isinstance(member, discord.Member):
        await ctx.send("Tag someone to piss them off <:karlnoodle:392209143190126593>")
        return
    if not isinstance(moves, int):
        moves = 7
    if member.voice is None:
        await ctx.send(f"OI {member.mention}")
        return
    initial_ch = member.voice.channel
    vcs = ctx.message.guild.voice_channels
    vcs.remove(initial_ch)
    vc_list = [vc for vc in vcs if vc.name != 'Mary Juan']
    prev = None
    for _ in range(moves):
        curr = random.choice(vc_list)
        while curr == prev:
            curr = random.choice(vc_list)
        await member.move_to(curr)
        await asyncio.sleep(0.5)
        prev = curr
    await member.move_to(initial_ch)

@oi.error
async def oi_error(ctx: commands.Context, error: commands.CommandError):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.reply(f"ms!oi is on CD for {error.retry_after:.2f}s.", delete_after=int(error.retry_after))

@bot.command()
async def ooo(ctx: commands.Context):
    start_str = "JOOOOO"
    msg = await ctx.send(start_str)
    for _ in range(10):
        await asyncio.sleep(1.3)
        start_str += "OOOOOO"
        await msg.edit(content=start_str)
    await msg.edit(content=start_str+"RDAN")

@bot.command()
async def opgg(ctx: commands.Context, name: str='', region: str="oce"):
    if not name:
        await ctx.send("Usage example: ms!opgg iamrandom [na/euw/kr etc., default oce]")
    else:
        await ctx.send(f"https://oce.op.gg/summoners/{region}/{name}")

@bot.command()
async def patchnotes(ctx: commands.Context):
    await ctx.send(pathlib.Path('patchnotes.txt').read_text(encoding='UTF-8').strip())

@bot.command()
async def razza(ctx: commands.Context):
    await ctx.send("https://clips.twitch.tv/TenuousCarelessAnacondaMingLee")

@bot.command(aliases=['resetnames'])
async def reset_nicknames(ctx: commands.Context):
    msg = await ctx.send("Are you sure you want to reset all nicknames?")
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) == '✅' or str(reaction.emoji) == '❌'

    try:
        reaction, _ = await bot.wait_for('reaction_add', timeout=30.0, check=check)
    except asyncio.TimeoutError:
        try:
            await msg.delete()
        except discord.errors.NotFound:
            pass
    else:
        try:
            await msg.delete()
        except discord.errors.NotFound:
            pass
        if str(reaction.emoji) == '✅':
            for member in ctx.guild.members:
                for role in member.roles:
                    if member.nick and role.name in ('Secretary', 'Vice Principal'):
                        await member.edit(nick=None)
            await ctx.send("All nicknames reset!")

@commands.cooldown(1, 30, commands.BucketType.guild)
@bot.command()
async def shuffle(ctx: commands.Context):
    start = time.time()    
    sec_vp_members = list(
        set(
            itertools.chain.from_iterable([role.members for role in ctx.guild.roles if re.search(r'^Secretary$|^Vice Principal$', role.name)])
        )
    )
    nicks: list[str] = [member.nick for member in sec_vp_members]
    random.shuffle(nicks)
    for member, nick in zip(sec_vp_members, nicks):
        if member.nick != nick:
            await member.edit(nick=nick)

    try: 
        await ctx.message.delete()
    except discord.errors.NotFound:
        pass
    
    await ctx.send(f'Shuffled in {time.time()-start:.2f}s!', delete_after=10)
    

@shuffle.error
async def shuffle_error(ctx: commands.Context, error: commands.CommandError):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"ms!shuffle is on CD for {error.retry_after:.2f}s.", delete_after=int(error.retry_after))

@bot.command()
async def snoopy(ctx: commands.Context):
    await ctx.send(art.snoopy_art)

@bot.command()
async def sro(ctx: commands.Context):
    await ctx.send(file=discord.File('bwu.mp3'))

@bot.command()
async def timer(ctx: commands.Context, duration: str=''):
    if not duration:
        await ctx.send("Usage: ms!timer minutes:seconds OR seconds")
        return
    duration_dict = helper.process_time(duration)
    if duration_dict is None or duration_dict['total'] == 0:
        await ctx.message.reply("Wrong format for timer!", mention_author=False)
        return

    await ctx.send(helper.send_timer_msg(duration_dict))
    await asyncio.sleep(duration_dict['total'])
    jeremy: discord.User = await bot.fetch_user(data.id_dict['jeremy'])
    await ctx.send(f"{ctx.message.author.mention} {jeremy.mention} should be back from his shower now!")

@bot.command()
async def worlds(ctx: commands.Context):
    await ctx.send("https://discord.com/channels/391945575886618626/660285290404904982/1171345479309721650")

@bot.command()
async def yt(ctx: commands.Context):
    await ctx.send("https://www.youtube.com/channel/UCEcv1n1cuUC4jdcrdy71S5Q")

@bot.event
async def on_message(msg: discord.Message):
    if msg.author == bot.user:
        return
    if msg.content.lower().startswith("ms!"):
        cmd_names = []
        for cmd in bot.commands:
            cmd_names.append(cmd.name)
            cmd_names.extend(cmd.aliases)
        if msg.content[3:].split(' ')[0] not in cmd_names:
            await msg.channel.send(f"'{msg.content.split(' ')[0]}' is not a valid command!\nAvailable commands: " + data.cmd_list)
        else:
            await bot.process_commands(msg)
        return
    if msg.author.id == data.id_dict['gomu']:
        await msg.add_reaction("<:chonkstone:811979419571847239>")
    elif msg.author.id in (data.bot_ids['Vibr'], data.bot_ids['DuncteBot'], data.bot_ids['Chip']):
        await asyncio.sleep(600)
        try:
            await msg.delete()
        except discord.errors.NotFound:
            pass
    if re.search(r'\bms\b|\bm[a-z]+ s[a-z]+', msg.content, re.IGNORECASE):
        await msg.add_reaction("🇲")
        await msg.add_reaction("🇸")
        await msg.channel.send("MS")
        
    if val_count := len(re.findall(r'\bval\b', msg.content, re.IGNORECASE)):
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
            if re.search("sick", word, re.IGNORECASE):
                await msg.add_reaction("🤮")
            if re.search("<@423369088681902080>", word, re.IGNORECASE):
                await msg.add_reaction("<:chonkstone:811979419571847239>")

@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    if (before.channel or after.channel).guild.id != data.id_dict['server']:
        return
    general = bot.get_channel(data.id_dict['general'])
    if before.channel is None:
        await general.send(f"Hi {member.mention}", silent=True, allowed_mentions=discord.AllowedMentions.none(), delete_after=30)
        helper.append_voice_log(member.mention, status='joined')
    elif after.channel is None:
        if member.id == data.id_dict['jordan']:
            await general.send(f"DID YOU SAY BYE {member.mention}?", silent=True, allowed_mentions=discord.AllowedMentions.none(), delete_after=30)
        else:
            await general.send(f"{member.mention} Where are you going?", silent=True, allowed_mentions=discord.AllowedMentions.none(), delete_after=30)
        helper.append_voice_log(member.mention, status='left')

@bot.event
async def on_typing(channel: discord.TextChannel, _user: discord.Member, _when: datetime.datetime):
    if channel.guild.id == data.id_dict['server']:
        await channel.send(random.choice(data.typing_pic_links), delete_after=1.5)

@bot.event
async def on_presence_update(before: discord.Member, after: discord.Member):
    if before.status != discord.Status.offline:
        return
    if any(twins := [after.id == data.id_dict['jordan'], after.id == data.id_dict['colden']]):
        start_str = f"{after.mention} {'JOOOOO' if twins[0] else 'COOOOO'}"
        name_end = f"{'RDAN' if twins[0] else 'LDEN'}"
        general = bot.get_channel(data.id_dict['general'])
        msg = await general.send(start_str, silent=True)
        for _ in range(10):
            start_str += "OOOOOO"
            await msg.edit(content=start_str)
            await asyncio.sleep(1.3)
        await msg.edit(content=start_str+name_end)

bot.run(sys.argv[1])
