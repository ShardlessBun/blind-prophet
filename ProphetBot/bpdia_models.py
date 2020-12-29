from datetime import datetime
import gspread
import discord


class LogEntry(object):

    def __init__(self, existing_log=None, author=None, time=None, target_user=None, activity=None, outcome=None,
                 gp=None, xp=None, cl=None, asl=None):
        if existing_log:
            try:
                author = author or str(existing_log[0])
                time = time or str(existing_log[1])
                target_user = target_user or int(existing_log[2])
                activity = activity or str(existing_log[3])
                outcome = outcome or str(existing_log[4])
                gp = gp or int(existing_log[5])
                xp = xp or int(existing_log[6])
                cl = cl or int(existing_log[7])
                asl = asl or int(existing_log[8])
            except IndexError:
                print("Could not parse input for log entry")

        self.author = author
        self.time = time or str(datetime.utcnow())
        self.discID = target_user
        self.activity = activity
        self.outcome = outcome
        self.gp = gp
        self.xp = xp
        self.cl = cl
        self.asl = asl

    def format_as_list(self):
        return [str(self.author or ''),
                str(self.time),
                str(self.discID or ''),
                str(self.activity or ''),
                str(self.outcome or ''),
                str(self.gp or ''),
                str(self.xp or ''),
                str(self.cl or ''),
                str(self.asl or '')]
