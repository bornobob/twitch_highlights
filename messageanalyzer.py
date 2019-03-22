from scipy.signal import find_peaks
import matplotlib.pyplot as plt
import numpy as np


twitch_highlight_url = '?t={:02}h{:02}m{:02}s'


class MessageAnalyzer:
    def __init__(self, stream_entry):
        self.stream_entry = stream_entry

    def get_message_frequencies(self, vod_id):
        vod = self.stream_entry.get_vod_by_id(vod_id)
        all_timestamps = np.zeros(vod.get_length_in_seconds())
        total_secs = vod.get_length_in_seconds()
        for m in vod.messages:
            delta_secs = int((m.date - vod.time_started).total_seconds())
            all_timestamps[min(delta_secs, total_secs - 1)] += 1
        return all_timestamps

    @staticmethod
    def get_frequency_peaks(frequencies, distance, prominence):
        peaks, _ = find_peaks(frequencies, height=np.median(frequencies), distance=distance, prominence=prominence)
        median_messages = np.median(frequencies[peaks])
        peaks = np.where(frequencies[peaks] > median_messages, peaks, np.zeros_like(peaks))
        return peaks[peaks.nonzero()]

    @staticmethod
    def show_message_frequencies(frequencies, peaks):
        plt.plot(range(len(frequencies)), frequencies)
        plt.plot(peaks, frequencies[peaks], 'x')
        plt.show()

    @staticmethod
    def seconds_to_time(seconds):
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)
        return hours, minutes, seconds

    @staticmethod
    def build_twitch_highlight_url(vod_url, hours, minutes, seconds):
        return vod_url + '/' + twitch_highlight_url.format(hours, minutes, seconds)

    @staticmethod
    def subtract_time_from_peaks(peaks, seconds):
        return [max(0, t - seconds) for t in peaks]

    def get_twitch_highlight_urls(self, distance=150, prominence=1, subtract_seconds=30):
        result_dict = {}
        for v in self.stream_entry.vods:
            frequencies = self.get_message_frequencies(v.broadcast_id)
            peaks = self.get_frequency_peaks(frequencies, distance, prominence)
            peaks = self.subtract_time_from_peaks(peaks, subtract_seconds)
            peaks.sort(key=lambda x: frequencies[x])
            result_dict[v.broadcast_id] = [self.build_twitch_highlight_url(v.url, *self.seconds_to_time(secs))
                                           for secs in peaks]
        return result_dict
