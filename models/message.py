from datetime import datetime
import re

msg_re = re.compile(r'\[[\d]+-[\d]+-[\d]+ (?P<hrs>[\d]+):(?P<mins>[\d]+):(?P<secs>[\d]+) '
                    r'(?P<timezone>[a-zA-Z]+)\] (?P<author>[^:]+): (?P<msg>.*)')


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

    def __str__(self):
        return '{}: {}'.format(self.date.strftime('(%b %d) %H:%M'), self.message)
