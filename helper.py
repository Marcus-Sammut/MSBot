import datetime
import time
import random
import re
import requests
import json
import asyncio
import data

def append_voice_log(name, status):
    curr_time = time.strftime("%I:%M%p", time.localtime()).lower()
    if curr_time[0] == '0':
        curr_time = curr_time[1:]
    with open('voice_log.txt', 'r+') as f:
        logs = f.readlines()
        if len(logs) > 20:
            logs.pop(0)
        if status == 'joined':
            logs.append(f"{name} joined at {curr_time}\n")
        elif status == 'left':
            logs.append(f"{name} left at {curr_time}\n")

        # write to file
        f.seek(0)
        f.truncate()
        f.writelines(logs)

def check_MS(msg):
    a = re.search("^[Mm][Ss] ", msg) # 'ms beast'
    b = re.search(" [Mm][Ss]$", msg) # 'boom ms'
    c = re.search(" [Mm][Ss] ", msg) # 'dude ms beast'
    d = re.search("^[Mm][Ss]$", msg) # "^MS/Ms/mS/ms$"
    e = re.search("^[Mm][a-zA-Z]+ [Ss][a-zA-Z]+", msg) # "^mega shark"
    f = re.search(" [Mm][a-zA-Z]+ [Ss][a-zA-Z]+", msg) # "hello mega shark"
    #print(msg,a,b,c,d,e,f)
    if any([a,b,c,d,e,f]):
        return True
    else:
        return False

def fetch_member(id, members):
    for member in members:
        print('huh', member.id,' ', id)
        if member.id == id:
            return member

def get_aa_quote():
    quote = random.choice(data.arthur_quotes)
    return "\"" + quote + "\"" + " - Arthur Ang"

def get_quote():
    response = requests.get("https://zenquotes.io/api/random")
    json_data = json.loads(response.text)
    return json_data[0]['q'] + " - " + json_data[0]['a']

def get_game_name(category_id):
    """get id from category dict"""
    with open('medal_categories.txt', 'r', encoding='utf8') as data:
        category_dict = json.loads(data.read())
    found = False
    for category in category_dict:
        if category['id'] == category_id:
            return f"({category['name']})"
    return ''

def get_recent_clips(id, days):
    header = {"Authorization":"pub_qBFrFBCfU0SErmP9hChALNXeQnyekLik"}
    response = requests.get(f"https://developers.medal.tv/v1/latest?userId={id}&limit=100", headers=header)
    json_data = json.loads(response.text)
    recent_clips = []
    for data in json_data['contentObjects']:
        now = int(datetime.datetime.now().timestamp())
        post_time = now - int(str(data['createdTimestamp'])[:-3])
        if post_time < (86400 * days):
            recent_clips.append(data)
    return recent_clips

def jordan_list():
    jordans = []
    for i in range(2,101):
        jordans.append("J" + "O" * i + "RDAN")
    return jordans

def process_time(time: str):
    timer = {
        'm': 0,
        's': 0,
        'total' : 0
    }
    if re.search("^[0-9]+:[0-9]+$", time):
        min_sec = time.split(":")
        timer['m'] = int(min_sec[0])
        timer['s'] = int(min_sec[1])
    elif re.search("^[0-9]+$", time):
        if int(time) <= 0:
            return None
        timer['s'] = int(time)
    else:
        return None
    timer['total'] = timer['m'] * 60 + timer['s']
    return timer

def send_timer_msg(timer):
    mins = timer['m']
    secs = timer['s']
    base_msg = "Jeremy said he will take a shower for"
    if mins > 0 and secs > 0:
        return f"{base_msg} {mins} minutes and {secs} seconds!"
    elif mins >= 1 and secs == 0:
        return f"{base_msg} {mins} minute{'s' if mins > 1 else ''}!"
    elif mins == 0:
        return f"{base_msg} {secs} seconds!"

async def do_timer(ctx, total, bot):
    await asyncio.sleep(total)
    jeremy = await bot.fetch_user(data.jeremy_id)
    await ctx.send(f"{ctx.message.author.mention} {jeremy.mention} should be back from his shower now!")

def seconds_to_text(secs):
    days = secs // 86400
    hours = (secs - days * 86400) // 3600
    minutes = (secs - days * 86400 - hours * 3600) // 60
    seconds = secs - days * 86400 - hours * 3600 - minutes*60
    result = ("{} days, ".format(days) if days else "") + \
    ("{} hours, ".format(hours) if hours else "") + \
    ("{} mins, ".format(minutes) if minutes else "") + \
    ("{} secs".format(seconds) if seconds else "")
    return result