###
# 2023, Matias Wilkman
#
#
###

from supybot import utils, plugins, ircutils, callbacks
from supybot.commands import *
from supybot.i18n import PluginInternationalization
from datetime import datetime
import icalendar
import requests

_ = PluginInternationalization('Calendar')

class Calendar(callbacks.Plugin):
    """Notifies of scheduled events in iCal calendars"""
    threaded = True

    
    @wrap
    def nextevent(self, irc, msg, args):
        """takes no arguments

        Replies with the next event in the calendar
        """
        calendar = icalendar.Calendar.from_ical(requests.get(self.registryValue("calendars")[0]).text)
        for event in calendar.walk("VEVENT"):
            date = icalendar.vDDDTypes.from_ical(event.get("DTSTART")) 
            if date > datetime.now().date():
                reply = "The next event in the calendar is {summary}, on {date}".format(
                    summary=event.get("SUMMARY"),
                    date=date.strftime("%d.%m.%Y"))
                irc.reply(reply)

Class = Calendar


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
