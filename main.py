import requests
import json
from datetime import datetime, timezone
from models import StreamEntry, VodEntry
from exceptions import UnknownStreamerError
from caches import LogtextCache
from messageanalyzer import MessageAnalyzer


client_id = json.loads(open('credentials.json', 'r').read())['client_id']
request_headers = {'Accept': 'application/vnd.twitchtv.v5+json', 'Client-ID': client_id}


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
        for s in stream_entries:
            ma = MessageAnalyzer(s)
            urls = ma.get_twitch_highlight_urls()
            print(s)
            for v in urls.keys():
                print(s.get_vod_by_id(v), '\n -', '\n - '.join(urls[v]))


th = TwitchHighligher('loltyler1', 2019, 3, 12)
th.get_highlights()
