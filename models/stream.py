class StreamEntry:
    def __init__(self, vods):
        self.vods = vods

    def get_vod_by_id(self, vod_id):
        for v in self.vods:
            if v.broadcast_id == vod_id:
                return v
        raise KeyError('No VOD was found with the given ID', vod_id)

    def __str__(self):
        return 'STREAM containing {} VODS, FROM: {}, UNTIL: {}'.format(len(self.vods),
                                                                       self.vods[0].time_started.strftime('(%b %d) '
                                                                                                          '%H:%M'),
                                                                       self.vods[-1].time_finished.strftime('(%b %d) '
                                                                                                            '%H:%M'))
