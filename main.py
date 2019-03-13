import requests
import re
import json
from datetime import datetime, timedelta

msg_re = re.compile(r'\[[\d]+-[\d]+-[\d]+ (?P<hrs>[\d]+):(?P<mins>[\d]+):(?P<secs>[\d]+) '
                    r'(?P<timezone>[a-zA-Z]+)\] (?P<author>[^:]+): (?P<msg>.*)')
client_id = json.loads(open('credentials.json', 'r').read())['client_id']
request_headers = {'Accept': 'application/vnd.twitchtv.v5+json', 'Client-ID': client_id}
MONTH_LIST = ['January', 'February', 'March', 'April', 'May', 'June',
              'July', 'August', 'September', 'October', 'November', 'December']


def secs_to_time(seconds):
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return hours, minutes, seconds


def time_to_str(hours, minutes, seconds):
    return '{}:{}:{}'.format(str(hours).zfill(2), str(minutes).zfill(2), str(seconds).zfill(2))


class ChatEntry:
    def __init__(self, message):
        match = msg_re.match(message)
        if not match:
            raise ValueError('The given message is not a valid message.', message)
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
        return 'VOD_ID: {}, URL: {}, length: {}, from: {}, until: {}'.format(
            self.broadcast_id, self.url, time_to_str(*secs_to_time(self.length)),
            self.time_started.strftime('(%b %d) %H:%M'), self.time_finished.strftime('(%b %d) %H:%M'))


class UnknownStreamerError(Exception):
    pass


class TwitchHighligher:
    def __init__(self, streamer_name, year, month, day):
        self.streamer_name = streamer_name
        self.year = year
        self.month = month
        self.day = day
        self.streamer_id = self.get_streamer_id()
        self.separated_messages = self.get_messages_by_log_text()
        self.total_vods, self.raw_vods = self.get_vods_by_streamer_id()
        self.vods = self.convert_raw_vods()

    def get_streamer_id(self):
        try:
            twitch_user_url = 'https://api.twitch.tv/kraken/users?login={}'.format(self.streamer_name)
            r = requests.get(twitch_user_url, headers=request_headers)
            return r.json()['users'][0]['_id']
        except KeyError or IndexError:
            raise UnknownStreamerError('The given streamer was not found on twitch', self.streamer_name)

    def get_vods_by_streamer_id(self, limit=100):
        twitch_vod_url = 'https://api.twitch.tv/kraken/channels/{}/videos?broadcast_type=archive&limit={}'.format(
            self.streamer_id, limit)
        r = requests.get(twitch_vod_url, headers=request_headers)
        jsondata = r.json()
        return jsondata['_total'], jsondata['videos']

    def get_logs_url(self):
        return 'https://overrustlelogs.net/{0}%20chatlog/{1}%20{2}/{2}-{3}-{4}.txt'.format(self.streamer_name,
                                                                                           MONTH_LIST[self.month - 1],
                                                                                           self.year,
                                                                                           str(self.month).zfill(2),
                                                                                           str(self.day).zfill(2))

    def get_log_text_by_url(self):
        r = requests.get(self.get_logs_url())
        return r.text

    def get_messages_by_log_text(self):
        separated_msgs = []
        for c in self.get_log_text_by_url().split('\n')[:-1]:
            separated_msgs.append(ChatEntry(c))
        return separated_msgs

    def convert_raw_vods(self):
        vods = []
        for v in self.raw_vods:
            vods.append(VodEntry(v['broadcast_id'], v['url'], v['length'], v['recorded_at']))
        return vods


th = TwitchHighligher('loltyler1', 2019, 3, 12)
for vod in th.vods[::-1]:
    print(vod)
