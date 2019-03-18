class StreamEntry:
    def __init__(self, vods):
        self.vods = vods

    def __str__(self):
        return '-' * 20 + '\n' + '\n'.join(' - ' + str(x) for x in self.vods)
