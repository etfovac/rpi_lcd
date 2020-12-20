import datetime
import psutil

ts_form = "%b %d  %H:%M:%S"
# LCD:
        # Sep 04  12:32:53
        # Sep 04  15:02:38

class TimeTrack():
    def __init__(self):
        self.bt = datetime.datetime.fromtimestamp(psutil.boot_time())
        self.bts = self.bt.strftime(ts_form)
        self.ct = self.bt
        self.cts = self.bts
        self.diff = 0
        self.tot_diff = 0
        self.upt = self.ct - self.bt # up time

    def timestamps(self):
        curr = datetime.datetime.now()
        self.diff = curr - self.ct
        self.ct = curr
        self.cts = self.ct.strftime(ts_form)
        self.upt = self.ct - self.bt # up time
        return self.bts, self.cts

    def timedeltas(self, threshold=1):
        passed = self.tot_diff > threshold
        if passed:
            self.tot_diff = self.diff.total_seconds()
        else:
            self.tot_diff = self.tot_diff + self.diff.total_seconds()
        return self.upt, self.tot_diff, passed