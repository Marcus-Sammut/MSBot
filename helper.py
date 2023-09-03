import datetime
import time
import random
import re
import json
import requests
import data

from typing import Literal

def append_voice_log(name: str, status: Literal["joined", "left"]):
    curr_time = time.strftime("%I:%M%p", time.localtime()).lower()
    if curr_time[0] == '0':
        curr_time = curr_time[1:]
    with open('voice_log.txt', 'r+') as log_file:
        logs = log_file.readlines()
        if len(logs) > 20:
            logs.pop(0)
        logs.append(f"{name} {status} at {curr_time}\n")
        log_file.seek(0)
        log_file.truncate()
        log_file.writelines(logs)

def get_aa_quote() -> str:
    quote = random.choice(data.arthur_quotes)
    return "\"" + quote + "\"" + " - Arthur Ang"

def get_quote() -> str:
    response = requests.get("https://zenquotes.io/api/random")
    json_data = json.loads(response.text)
    return json_data[0]['q'] + " - " + json_data[0]['a']

def get_game_name(category_id: int) -> str:
    """get id from category dict"""
    with open('medal_categories.txt', 'r', encoding='utf8') as cats:
        category_dict = json.loads(cats.read())
    for category in category_dict:
        if category['id'] == category_id:
            return f"({category['name']})"
    return ''

def get_recent_clips(medal_id: int, days: int) -> list:
    header = {"Authorization":"pub_v3592mlcXKL8IBhQqnaMzhAsDF7Vky9f"}
    response = requests.get( \
        f"https://developers.medal.tv/v1/latest?userId={medal_id}&limit=100", headers=header \
    )
    print(response)
    # TEMP: remove when code is 200
    return response.status_code

    json_data = json.loads(response.text)
    recent_clips = []
    for clip in json_data['contentObjects']:
        now = int(datetime.datetime.now().timestamp())
        post_time = now - int(str(clip['createdTimestamp'])[:-3])
        if post_time < (86400 * days):
            recent_clips.append(clip)
    return recent_clips

def process_time(input_duration: str) -> dict | None:
    timer = {
        'm': 0,
        's': 0,
        'total' : 0
    }
    if re.search("^[0-9]+:[0-9]+$", input_duration):
        min_sec = input_duration.split(":")
        timer['m'] = int(min_sec[0])
        timer['s'] = int(min_sec[1])
    elif re.search("^[0-9]+$", input_duration):
        timer['s'] = int(input_duration)
    else:
        return None
    timer['total'] = timer['m'] * 60 + timer['s']
    return timer

def send_timer_msg(timer: dict) -> str:
    mins = timer['m']
    secs = timer['s']
    base_msg = "Jeremy said he will take a shower for"
    final_msg = f"{base_msg} {mins} minutes and {secs} second{'s' if secs > 1 else ''}!"
    if mins > 0 and secs == 0:
        return f"{base_msg} {mins} minute{'s' if mins > 1 else ''}!"
    return f"{base_msg} {secs} second{'s' if secs > 1 else ''}!"
