import requests
import matplotlib.pyplot as plt
import re
import json
from datetime import datetime, timedelta

msg_re = re.compile(r'\[[\d]+-[\d]+-[\d]+ (?P<hrs>[\d]+):(?P<mins>[\d]+):(?P<secs>[\d]+) '
                    r'(?P<timezone>[a-zA-Z]+)\] (?P<author>[^:]+): (?P<msg>.*)')
client_id = json.loads(open('credentials.json', 'r').read())['client_id']
request_headers = {'Accept': 'application/vnd.twitchtv.v5+json', 'Client-ID': client_id}
MONTH_LIST = ['January', 'February', 'March', 'April', 'May', 'June',
              'July', 'August', 'September', 'October', 'November', 'December']


class ChatEntry:
    def __init__(self, message):
        match = msg_re.match(message)
        if not match:
            raise ValueError('The given message was not a valid message.')
        self.hours = int(match['hrs'])
        self.minutes = int(match['mins'])
        self.seconds = int(match['secs'])
        self.timezone = match['timezone']
        self.author = match['author']
        self.message = match['msg']


class VodEntry:
    def __init__(self, broadcast_id, url, length, broadcast_at):
        self.broadcast_id = broadcast_id
        self.url = url
        self.length = length
        self.time_started = datetime.strptime(broadcast_at, '%Y-%m-%dT%H:%M:%SZ')
        self.time_finished = self.time_started + timedelta(seconds=length)

    def __str__(self):
        return 'VOD_ID: {}, URL: {}, length: {}:{}:{}, from: {}, until: {}'.format(
            self.broadcast_id, self.url, *secs_to_time(self.length), self.time_started.strftime('(%b %d) %H:%M'),
            self.time_finished.strftime('(%b %d) %H:%M'))


def secs_to_time(seconds):
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return hours, minutes, seconds


def get_streamer_id(streamer_name):
    twitch_user_url = 'https://api.twitch.tv/kraken/users?login={}'.format(streamer_name)
    r = requests.get(twitch_user_url, headers=request_headers)
    return r.json()['users'][0]['_id']


def get_vods_by_streamer_id(streamer_id, limit=100):
    twitch_vod_url = 'https://api.twitch.tv/kraken/channels/{}/videos?broadcast_type=archive&limit={}'.format(
        streamer_id, limit)
    r = requests.get(twitch_vod_url, headers=request_headers)
    jsondata = r.json()
    return jsondata['_total'], jsondata['videos']


def get_logs_url(streamer_name, year, month, day):
    return 'https://overrustlelogs.net/{0}%20chatlog/{1}%20{2}/{2}-{3}-{4}.txt'.format(streamer_name,
                                                                                       MONTH_LIST[month - 1], year,
                                                                                       str(month).zfill(2),
                                                                                       str(day).zfill(2))


def get_log_text_by_url(logs_url):
    r = requests.get(logs_url)
    return r.text


def get_messages_by_log_text(log_text):
    separated_msgs = []
    for c in log_text.split('\n')[:-1]:
        separated_msgs.append(ChatEntry(c))
    return separated_msgs


def show_info(all_messages):
    all_timestamps = [0] * (24 * 60 * 60)
    for chat in all_messages:
        all_timestamps[chat.hours * 3600 + chat.minutes * 60 + chat.seconds] += 1
    print('Average number of messages in 24 hours:', sum(all_timestamps) / len(all_timestamps))
    plt.plot(range(24 * 60 * 60), all_timestamps)
    plt.show()


def convert_raw_vods(raw_vods):
    vods = []
    for v in raw_vods:
        vods.append(VodEntry(v['broadcast_id'], v['url'], v['length'], v['recorded_at']))
    return vods


streamer_name = 'loltyler1'
year, month, day = 2019, 3, 12

streamer_id = get_streamer_id(streamer_name)
total, raw_vods = get_vods_by_streamer_id(streamer_id)
logs_url = get_logs_url(streamer_name, year, month, day)
log_text = get_log_text_by_url(logs_url)
all_messages = get_messages_by_log_text(log_text)
vods = convert_raw_vods(raw_vods)
for v in vods[::-1]:
    print(v)
