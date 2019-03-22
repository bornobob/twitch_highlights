from datetime import datetime, timedelta


class VodEntry:
    def __init__(self, broadcast_id, url, length, broadcast_at):
        self.broadcast_id = broadcast_id
        self.url = url
        self.time_started = datetime.strptime(broadcast_at, '%Y-%m-%dT%H:%M:%SZ')
        self.time_finished = self.time_started + timedelta(seconds=length)
        self.messages = []

    def get_length_in_seconds(self):
        return int(abs((self.time_finished - self.time_started).total_seconds()))

    def __str__(self):
        return 'VOD_ID: {}, URL: {}, length: {}, from: {}, until: {}'.format(
            self.broadcast_id, self.url, str(self.time_finished - self.time_started),
            self.time_started.strftime('(%b %d) %H:%M'), self.time_finished.strftime('(%b %d) %H:%M'))
