from supybot import utils, plugins, ircutils, callbacks, irclib, world
import supybot.log as log
from supybot.commands import *
from supybot.i18n import PluginInternationalization
# HTML Generation imports:
from typing import List
from xml.dom.minidom import getDOMImplementation, Document
#JSON Generation:
import json
import datetime

_ = PluginInternationalization('UserList')


class UserList(callbacks.Plugin):
    userlist = {}
    def __init__(self, irc):
        super().__init__(irc)
        self.updatelist(irc, None)
        self.renderlist()

    """List users from channels that the bot is on"""
    def updatelist(self, irc, msg):
        for otherIrc in world.ircs:
            for (channel, channel_state) in otherIrc.state.channels.items():
                channelname = channel + "@" + otherIrc.network
                if channelname in self.registryValue("channels"):
                    self.userlist[channelname] = channel_state.users
                else:
                    log.info(channelname + " not in channel list, which is " + str(self.registryValue("UserListChannels")))
    
    def renderlist(self):
        # Create HTML:
        impl = getDOMImplementation()
        dt = impl.createDocumentType(
            "html",
            "-//W3C//DTD XHTML 1.0 Strict//EN",
            "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd",
        )
        dom = impl.createDocument("http://www.w3.org/1999/xhtml", "html", dt)
        html = dom.documentElement
        stylesheet = self.registryValue("stylesheet")
        if (stylesheet != "none"):
            style = dom.createElement("link")
            style.setAttribute("rel", "stylesheet")
            style.setAttribute("href", stylesheet)
            html.appendChild(style)
        title = dom.createElement("title")
        title.appendChild(dom.createTextNode("User List"))
        html.appendChild(title)
        html.appendChild(dom.createTextNode("User list created at " +
str(datetime.datetime.now())))
        for channel in self.userlist.keys():
            table = dom.createElement("table")
            tr = dom.createElement("tr")
            th = dom.createElement("th")
            th.appendChild(dom.createTextNode(channel))
            tr.appendChild(th)
            table.appendChild(tr)
            for user in self.userlist[channel]:
                tr = dom.createElement("tr")
                td = dom.createElement("td") 
                td.appendChild(dom.createTextNode(str(user)))
                tr.appendChild(td)
                table.appendChild(tr)
            html.appendChild(table)
        # Write to file:
        f = open("userlist.html", "w")
        f.write(dom.toxml())
        f.close()
        # Create JSON:
        json_data = {}
        for channel in self.userlist.keys():
            json_data[channel] = json.dumps(list(self.userlist[channel]))
        with open("userlist.json", "w") as json_file:
            json_file.write(str(json_data))

    def doJoin(self, irc, msg):
        self.updatelist(irc, msg)
        self.renderlist()
    
    def doPart(self, irc, msg):
        self.updatelist(irc, msg)
        self.renderlist()

    def doQuit(self, irc, msg):
        self.updatelist(irc, msg)
        self.renderlist()
        
Class = UserList

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
