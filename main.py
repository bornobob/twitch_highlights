import requests
import matplotlib.pyplot as plt
import re
from time import time
import statistics

msg_re = re.compile(r'\[[\d]+-[\d]+-[\d]+ (?P<hrs>[\d]+):(?P<mins>[\d]+):(?P<secs>[\d]+) '
                    r'(?P<timezone>[a-zA-Z]+)\] (?P<author>[^:]+): (?P<msg>.*)')


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


def secs_to_time(seconds):
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return hours, minutes, seconds


MONTH_LIST = ['January', 'February', 'March', 'April', 'May', 'June',
              'July', 'August', 'September', 'October', 'November', 'December']

streamer_name = 'loltyler1'
year, month, day = 2019, 3, 11
url = 'https://overrustlelogs.net/{0}%20chatlog/{1}%20{2}/{2}-{3}-{4}.txt'.format(streamer_name, MONTH_LIST[month-1],
                                                                                  year, str(month).zfill(2),
                                                                                  str(day).zfill(2))
request_headers = {'Accept': 'application/vnd.twitchtv.v5+json', 'Client-ID': client_id}

twitch_user_url = 'https://api.twitch.tv/kraken/users?login={}'.format(streamer_name)
r = requests.get(twitch_user_url, headers=request_headers)
streamer_id = r.json()['users'][0]['_id']

twitch_vod_url = 'https://api.twitch.tv/kraken/channels/{}/videos?broadcasts=true'.format(streamer_id)
r = requests.get(twitch_vod_url, headers=request_headers)
print(r.json())

response = requests.get(url)
all_chats = response.text

time_before = time()
separated_msgs = []
for chat in all_chats.split('\n')[:-1]:
    separated_msgs.append(ChatEntry(chat))
print('Loaded', len(separated_msgs), 'messages in', time()-time_before, 'ms')

all_timestamps = [0]*(24*60*60)
for chat in separated_msgs:
    all_timestamps[chat.hours*3600 + chat.minutes*60 + chat.seconds] += 1

print('Average number of messages in 24 hours:', sum(all_timestamps)/len(all_timestamps))

streamed_timestamps = list(filter(lambda x: all_timestamps[x] >= 3, range(len(all_timestamps))))
print('Time spent streaming: {}:{}:{}'.format(*secs_to_time(len(streamed_timestamps))))

streamed_messages = list(map(lambda x: all_timestamps[x], streamed_timestamps))
average_streaming_messages = sum(streamed_messages)/len(streamed_messages)
print('Average number of messages in streaming time:', average_streaming_messages)
print('Standard deviation of msgs in streaming time:', statistics.stdev(streamed_messages))

plt.plot(range(24*60*60), all_timestamps)
plt.plot(streamed_timestamps, [0]*len(streamed_timestamps), 'ro')
plt.show()
