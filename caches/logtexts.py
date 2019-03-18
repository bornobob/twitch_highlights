from models import ChatEntry
import requests
from datetime import timedelta, time

MONTH_LIST = ['January', 'February', 'March', 'April', 'May', 'June',
              'July', 'August', 'September', 'October', 'November', 'December']


class LogtextCache:
    def __init__(self, streamer_name):
        self.streamer_name = streamer_name
        self.saved_dates = {}

    def get_log_url(self, year, month, day):
        return 'https://overrustlelogs.net/{0}%20chatlog/{1}%20{2}/{2}-{3:02}-{4:02}.txt'.format(self.streamer_name,
                                                                                                 MONTH_LIST[month - 1],
                                                                                                 year,
                                                                                                 month,
                                                                                                 day)

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
        for _ in range(delta_days + 1):
            if current_date.date() == end_date.date():
                messages += self.get_messages_on_date(current_date, end_date)
            else:
                messages += self.get_messages_on_date(current_date, current_date.combine(current_date, time.max))
            current_date = current_date + timedelta(days=1)
            current_date = current_date.combine(current_date, time.min)
        return messages
