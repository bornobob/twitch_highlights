import requests
import re
import json
from datetime import datetime, timedelta, timezone, time, date

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
    def __init__(self, message, year, month, day):
        match = msg_re.match(message)
        if not match:
            raise ValueError('The given message is not a valid message.', message)
        hours = int(match['hrs'])
        minutes = int(match['mins'])
        seconds = int(match['secs'])
        self.date = datetime(year, month, day, hours, minutes, seconds)
        self.message = match['msg']


class VodEntry:
    def __init__(self, broadcast_id, url, length, broadcast_at):
        self.broadcast_id = broadcast_id
        self.url = url
        self.length = length
        self.time_started = datetime.strptime(broadcast_at, '%Y-%m-%dT%H:%M:%SZ')
        self.time_finished = self.time_started + timedelta(seconds=length)
        self.messages = []

    def __str__(self):
        return 'VOD_ID: {}, URL: {}, length: {}, from: {}, until: {}'.format(
            self.broadcast_id, self.url, time_to_str(*secs_to_time(self.length)),
            self.time_started.strftime('(%b %d) %H:%M'), self.time_finished.strftime('(%b %d) %H:%M'))


class StreamEntry:
    def __init__(self, vods):
        self.vods = vods

    def __str__(self):
        return '-' * 20 + '\n' + '\n'.join(' - ' + str(x) for x in self.vods)


class UnknownStreamerError(Exception):
    pass


class LogtextCache:
    def __init__(self, streamer_name):
        self.streamer_name = streamer_name
        self.saved_dates = {}

    def get_log_url(self, year, month, day):
        return 'https://overrustlelogs.net/{0}%20chatlog/{1}%20{2}/{2}-{3}-{4}.txt'.format(self.streamer_name,
                                                                                           MONTH_LIST[month - 1],
                                                                                           year,
                                                                                           str(month).zfill(2),
                                                                                           str(day).zfill(2))

    def get_log_text_by_url(self, year, month, day):
        r = requests.get(self.get_log_url(year, month, day))
        return r.text

    def create_new_entry(self, year, month, day):
        separated_msgs = []
        for c in self.get_log_text_by_url(year, month, day).split('\n')[:-1]:
            separated_msgs.append(ChatEntry(c, year, month, day))
        return separated_msgs

    def get_messages_by_date(self, year, month, day):
        if (year, month, day) in self.saved_dates.keys():
            return self.saved_dates[(year, month, day)]
        else:
            new_entry = self.create_new_entry(year, month, day)
            self.saved_dates[(year, month, day)] = new_entry
            return new_entry

    def get_messages_on_date(self, begin_time, end_time):
        all_messages = self.get_messages_by_date(begin_time.year, begin_time.month, begin_time.day)
        messages = []
        for m in all_messages:
            if m.date >= begin_time:
                if m.date <= end_time:
                    messages.append(m)
                else:
                    break
        return messages

    def get_messages_between_dates(self, begin_date, end_date):
        current_date = begin_date
        messages = []
        delta_days = (end_date.date() - begin_date.date()).days
        print('delta_days', delta_days)
        for _ in range(delta_days + 1):
            if current_date.date() == end_date.date():
                messages += self.get_messages_on_date(current_date, end_date)
            else:
                messages += self.get_messages_on_date(current_date, current_date.combine(current_date, time.max))
            current_date = current_date + timedelta(days=1)
            current_date = current_date.combine(current_date, time.min)
        return messages


class TwitchHighligher:
    def __init__(self, streamer_name, year, month, day, max_inter_stream_time=3600):
        self.streamer_name = streamer_name
        self.year = year
        self.month = month
        self.day = day
        self.max_inter_stream_time = max_inter_stream_time
        self.logtext_cache = LogtextCache(streamer_name)
        self.streamer_id = self.get_streamer_id()

    def get_streamer_id(self):
        try:
            twitch_user_url = 'https://api.twitch.tv/kraken/users?login={}'.format(self.streamer_name)
            r = requests.get(twitch_user_url, headers=request_headers)
            return r.json()['users'][0]['_id']
        except (KeyError, IndexError):
            raise UnknownStreamerError('The given streamer was not found on twitch', self.streamer_name)

    def get_vods_by_streamer_id(self, limit=100):
        twitch_vod_url = 'https://api.twitch.tv/kraken/channels/{}/videos?broadcast_type=archive&limit={}'.format(
            self.streamer_id, limit)
        r = requests.get(twitch_vod_url, headers=request_headers)
        jsondata = r.json()
        return jsondata['_total'], jsondata['videos'][::-1]

    @staticmethod
    def convert_raw_vods(raw_vods):
        vods = []
        for v in raw_vods:
            vods.append(VodEntry(v['broadcast_id'], v['url'], v['length'], v['recorded_at']))
        return vods

    def get_vods_on_date(self, vods):
        given_date = datetime(self.year, self.month, self.day, tzinfo=timezone.utc).date()
        relevant_vods = []
        for v in vods:
            if v.time_started.date() <= given_date <= v.time_finished.date():
                relevant_vods.append(v)
        return relevant_vods

    def get_same_stream_vods_before(self, index, vods):
        added_vods = []
        while index > 0:
            difference = vods[index - 1].time_finished - vods[index].time_started
            if abs(difference.total_seconds()) <= self.max_inter_stream_time:
                added_vods.append(vods[index - 1])
            else:
                break
            index -= 1
        return added_vods[::-1]

    def get_same_stream_vods_after(self, index, vods):
        added_vods = []
        while index < len(vods) - 1:
            difference = vods[index + 1].time_started - vods[index].time_finished
            if abs(difference.total_seconds()) <= self.max_inter_stream_time:
                added_vods.append(vods[index + 1])
            else:
                break
            index += 1
        return added_vods

    def get_relevant_stream_vods(self, vods, relevant_vods):
        if relevant_vods:
            before_same_stream_vods = self.get_same_stream_vods_before(vods.index(relevant_vods[0]), vods)
            after_same_stream_vods = self.get_same_stream_vods_after(vods.index(relevant_vods[-1]), vods)
            relevant_vods = before_same_stream_vods + relevant_vods + after_same_stream_vods
        return relevant_vods

    def get_stream_entries_from_vods(self, vods):
        stream_entries, temp_stream = [], []
        for v in vods:
            if not temp_stream:
                temp_stream.append(v)
            else:
                difference = v.time_started - temp_stream[-1].time_finished
                if abs(difference.total_seconds()) <= self.max_inter_stream_time:
                    temp_stream.append(v)
                else:
                    stream_entries.append(StreamEntry(temp_stream))
                    temp_stream = [v]
        if temp_stream:
            stream_entries.append(StreamEntry(temp_stream))
        return stream_entries

    def get_stream_entries_by_date(self):
        total_vods, raw_vods = self.get_vods_by_streamer_id()
        vods = self.convert_raw_vods(raw_vods)
        relevant_vods = self.get_relevant_stream_vods(vods, self.get_vods_on_date(vods))
        return self.get_stream_entries_from_vods(relevant_vods)

    def bind_messages_to_stream_entries(self, entries):
        for s in entries:
            for v in s.vods:
                v.messages = self.logtext_cache.get_messages_between_dates(v.time_started, v.time_finished)

    def get_highlights(self):
        stream_entries = self.get_stream_entries_by_date()
        self.bind_messages_to_stream_entries(stream_entries)


th = TwitchHighligher('loltyler1', 2019, 3, 12)
th.get_highlights()
