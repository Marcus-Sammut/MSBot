import datetime
import time
import random
import re
import json
import requests
import socket
import struct
import data

from typing import Literal

def append_voice_log(name: str, status: Literal["joined", "left"]):

    curr_time = time.strftime("%A %-d/%-m at %-I:%M%p", time.localtime()).lower().capitalize()
    with open('voice_log.txt', 'r+', encoding='UTF-8') as log_file:
        logs = log_file.readlines()
        if len(logs) > 20:
            logs.pop(0)
        logs.append(f"{name} {status} on {curr_time}\n")
        log_file.seek(0)
        log_file.truncate()
        log_file.writelines(logs)

def get_game_name(category_id: str) -> str:
    """get id from category dict"""
    with open('new_medal_categories.json', 'r', encoding='utf8') as categories:
        category_dict = json.loads(categories.read())
    for category in category_dict:
        if category['id'] == category_id:
            return f"({category['name']})"
    return ''

def get_players_on_server(ip: str, port: int) -> set[str|None]:
    # https://gist.github.com/Lonami/b09fc1abb471fd0b8b5483d54f737ea0
    def read_var_int():
        i = 0
        j = 0
        while True:
            k = sock.recv(1)
            if not k:
                return 0
            k = k[0]
            
            i |= (k & 0x7f) << (j * 7)
            j += 1
            if j > 5:
                raise ValueError('var_int too big')
            if not (k & 0x80):
                return i

    sock = socket.socket()
    sock.connect((ip, port))
    try:
        host: bytes = ip.encode('utf-8')
        data = b'\x00\x04' + struct.pack('>b', len(host)) + host + struct.pack('>H', port) + b'\x01'
        data = struct.pack('>b', len(data)) + data
        sock.sendall(data + b'\x01\x00')
        length = read_var_int()
        if length < 10:
            if length < 0:
                raise ValueError('negative length read')
            else:
                raise ValueError(f'invalid response {sock.read(length)}')

        sock.recv(1)
        length = read_var_int()
        data = b''
        while len(data) != length:
            chunk = sock.recv(length - len(data))
            if not chunk:
                raise ValueError('connection abborted')
            data += chunk
        if players := json.loads(data)['players'].get('sample'):
            return {player['name'] for player in players}
        return set()

    finally:
        sock.close()

def get_recent_clips(medal_id: int, days: int) -> list|None:
    header = {"Authorization":"pub_RYBZ8RqPTsYhd9NHK8xPSiyVM5sok5JW"}
    response = requests.get(f"https://developers.medal.tv/v1/latest?userId={medal_id}&limit=50", headers=header)
    if not response.ok:
        print(response)
        return None
    json_data = json.loads(response.text)
    recent_clips = []
    for clip in json_data['contentObjects']:
        now = int(datetime.datetime.now().timestamp())
        post_time = now - int(str(clip['createdTimestamp'])[:-3])
        if post_time < (86400 * days):
            recent_clips.append(clip)
    return sorted(recent_clips, key=lambda x: x['createdTimestamp'], reverse=True)

def is_riot_key_valid(key: str):
    if not requests.get(f"https://oc1.api.riotgames.com/lol/platform/v3/champion-rotations?api_key={key}").ok:
        print("api key expired: https://developer.riotgames.com/")
        return False
    return True

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

def update_mythical_log():
    with open('missed_mythicals.txt', 'r+', encoding='UTF-8') as f:
        attempts, timestamp, user_mention = f.read().split()
        f.seek(0)
        f.write(f"{int(attempts)+1} {timestamp} {user_mention}")
        f.truncate()

def reset_mythical_log(user_mention):
    with open('missed_mythicals.txt', 'w', encoding='UTF-8') as f:
        f.write(f"0 {int(time.time())} {user_mention}")