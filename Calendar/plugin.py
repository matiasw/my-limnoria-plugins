###
# 2023, Matias Wilkman
#
#
###

from supybot import utils, plugins, ircutils, callbacks, registry
from supybot.commands import *
from supybot.i18n import PluginInternationalization
from datetime import datetime
from contextlib import closing
import sqlite3
import json
import icalendar
import requests

_ = PluginInternationalization('Calendar')

class Calendar(callbacks.Plugin):
    """Notifies of scheduled events in iCal calendars"""
    threaded = True
    dbfile = "data/calendar.db"
    calendars = {}

    def __init__(self, irc):
        # call the superclass's constructor
        super().__init__(irc)
        with closing(sqlite3.connect(self.dbfile)) as sqlconnection:
            with closing(sqlconnection.cursor()) as cursor:
                cursor.execute("""CREATE TABLE IF NOT EXISTS icsurls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                    name VARCHAR NOT NULL,
                    url VARCHAR NOT NULL,
                    UNIQUE (name))""")
            sqlconnection.commit()

    @wrap(["text"])    
    def addcalendars(self, irc, msg, args, calendarstoadd):
        """takes name and URL calendar as argument in JSON format

        You must escape double quotes in the JSON.
        """
        try:
            calendarurls = json.loads(str(calendarstoadd.replace('\\', '')))
        except Exception as e:
            irc.error("Could not parse the JSON in the calendars configuration value:" + str(e))
            return
        with closing(sqlite3.connect(self.dbfile)) as sqlconnection:
           with closing(sqlconnection.cursor()) as cursor:
               for name, url in calendarurls.items():
                   cursor.execute("INSERT OR REPLACE INTO icsurls(name, url) VALUES (?, ?)", (name, url))
                   self.calendars[name] = icalendar.Calendar.from_ical(requests.get(url).text)
        
    def _getcalendars(self): 
        with closing(sqlite3.connect(self.dbfile)) as sqlconnection:
            with closing(sqlconnection.cursor()) as cursor:
                for name, url in cursor.execute("SELECT name, url FROM icsurls").fetchall():
                    self.calendars[name] = icalendar.Calendar.from_ical(requests.get(url).text)

    @wrap([additional("text")])    
    def nextevent(self, irc, msg, args, calendarname=""):
        """takes name of calendar as argument, or uses first calendar if no name given

        Replies with the next event in the calendar
        """
        if self.calendars:
            calendarname = next(iter(self.calendars.keys()))
        else:
            self._getcalendars()
        if not self.calendars:
            irc.error("No calendars have been set up.")
        if calendarname:
           if calendarname in self.calendars:
                for event in self.calendars[calendarname].walk("VEVENT"):
                    date = icalendar.vDDDTypes.from_ical(event.get("DTSTART")) 
                    if date > datetime.now().date():
                        reply = "The next event in the calendar is {summary}, on {date}".format(
                            summary=event.get("SUMMARY"),
                            date=date.strftime(self.registryValue("dateformat")))
                        irc.reply(reply)
                        return

Class = Calendar


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
