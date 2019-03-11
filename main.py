import requests
import matplotlib.pyplot as plt
import re
from time import time

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


MONTH_LIST = ['January', 'February', 'March', 'April', 'May', 'June',
              'July', 'August', 'September', 'October', 'November', 'December']

streamer_name = 'loltyler1'
year, month, day = 2019, 3, 7
url = 'https://overrustlelogs.net/{0}%20chatlog/{1}%20{2}/{2}-{3}-{4}.txt'.format(streamer_name, MONTH_LIST[month-1],
                                                                                  year, str(month).zfill(2),
                                                                                  str(day).zfill(2))
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

plt.plot(range(24*60*60), all_timestamps)
plt.show()
