###
# 2023, Matias Wilkman
#
#
###

from supybot import utils, plugins, ircutils, callbacks
from supybot.commands import *
from supybot.i18n import PluginInternationalization
from datetime import datetime
import json
import icalendar
import requests

_ = PluginInternationalization('Calendar')

class iCal:
    def nextevent(self):
        for event in self.calendar.walk("VEVENT"):
            date = icalendar.vDDDTypes.from_ical(event.get("DTSTART")) 
            if date > datetime.now().date():
                return event

    def __init__(self, url):
        self.calendar = icalendar.Calendar.from_ical(requests.get(url).text)
        
class Calendar(callbacks.Plugin):
    """Notifies of scheduled events in iCal calendars"""
    threaded = True
    
    @wrap([additional("text")])    
    def nextevent(self, irc, msg, args, name=""):
        """takes name of calendar as argument, or uses first calendar if no name given

        Replies with the next event in the calendar
        """
        try:
            calendars = json.loads(''.join(map(str, self.registryValue("calendars"))))
        except Exception as e:
            irc.error("Could not parse the JSON in the calendars configuration value:" + str(e))
            return
        if name in calendars.keys():
            ical = iCal(calendars[name])
        elif calendars:
            ical = iCal(calendars[list(calendars.keys())[0]])
        else:
            irc.error("No calendars configured.")
            return
        event = ical.nextevent()
        date = icalendar.vDDDTypes.from_ical(event.get("DTSTART")) 
        reply = "The next event in the calendar is {summary}, on {date}".format(
            summary=event.get("SUMMARY"),
            date=date.strftime(self.registryValue("dateformat")))
        irc.reply(reply)

Class = Calendar


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
