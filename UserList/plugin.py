from supybot import utils, plugins, ircutils, callbacks, irclib, world, httpserver, conf
import supybot.log as log
from supybot.commands import *
from supybot.i18n import PluginInternationalization
# HTML Generation imports:
from typing import List
from xml.dom.minidom import getDOMImplementation, Document
#JSON Generation:
import json
from datetime import datetime
#timezone:
import tzlocal

_ = PluginInternationalization('UserList')

userlist = {}
stylesheet = "none"

class UserList(callbacks.Plugin):
    def __init__(self, irc):
        super().__init__(irc)
        self.updatelist(irc, None)
        conf.supybot.plugins.UserList.channels.addCallback(self.updatelist)
        conf.supybot.plugins.UserList.ignorednicks.addCallback(self.updatelist)
        #register http server callback:
        callback = UserListServerCallback()
        global stylesheet
        stylesheet = self.registryValue("stylesheet")
        httpserver.hook('userlist', callback)

    def die(self):
        conf.supybot.plugins.UserList.channels.removeCallback(self.updatelist)
        conf.supybot.plugins.UserList.ignorednicks.removeCallback(self.updatelist)
        #unregister callback:
        httpserver.unhook('userlist')
        super().die()

    """List users from channels that the bot is on"""
    def updatelist(self, irc = None, msg = None):
        for otherIrc in world.ircs:
            for (channel, channel_state) in otherIrc.state.channels.items():
                channelname = channel + "@" + otherIrc.network
                if channelname in self.registryValue("channels"):
                    excluded_users = self.registryValue("ignorednicks")
                    userlist[channelname] = [user for user in channel_state.users if user not in excluded_users]
                else:
                    log.debug(channelname + " not in channel list, which is " +
str(self.registryValue("channels")))
    
    def doJoin(self, irc, msg):
        self.updatelist(irc, msg)
    
    def doPart(self, irc, msg):
        self.updatelist(irc, msg)

    def doQuit(self, irc, msg):
        self.updatelist(irc, msg)

    def doNick(self, irc, msg):
        self.updatelist(irc, msg)
        
class UserListServerCallback(httpserver.SupyHTTPServerCallback):
    name = 'UserList'
    defaultResponse = """
        This plugin handles only GET request, please don't use other requests.
        Content served: userlist.html, userlist.json"""

    def doGet(self, handler, path):
        if path.endswith('userlist.html'):
            # Create HTML:
            impl = getDOMImplementation()
            dt = impl.createDocumentType(
                "html",
                "-//W3C//DTD XHTML 1.0 Strict//EN",
                "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd",
            )
            dom = impl.createDocument("http://www.w3.org/1999/xhtml", "html", dt)
            html = dom.documentElement
            html.setAttribute("xmlns", "http://www.w3.org/1999/xhtml")
            head = dom.createElement("head")
            if (stylesheet != "none"):
                style = dom.createElement("style")
                style.setAttribute("type", "text/css")
                with open(stylesheet) as f:
                    style.appendChild(dom.createTextNode(f.read()))
                head.appendChild(style)
            title = dom.createElement("title")
            title.appendChild(dom.createTextNode("User List"))
            head.appendChild(title)
            html.appendChild(head)
            body = dom.createElement("body")
            # Get the local timezone
            local_timezone = tzlocal.get_localzone()
            # Get the UTC offset
            utc_offset = datetime.now(local_timezone).strftime('%z')
            paragraph = dom.createElement("p")
            paragraph.appendChild(dom.createTextNode("User list created at " +
                                                str(datetime.now()
                                                    .strftime("%d.%m.%Y, %I:%M:%S") + f" Time zone: {local_timezone}, UTC Offset: {utc_offset}")))
            body.appendChild(paragraph)
            for channel in userlist.keys():
                table = dom.createElement("table")
                tr = dom.createElement("tr")
                th = dom.createElement("th")
                th.appendChild(dom.createTextNode(channel))
                tr.appendChild(th)
                table.appendChild(tr)
                for user in sorted(userlist[channel]):
                    tr = dom.createElement("tr")
                    td = dom.createElement("td") 
                    td.appendChild(dom.createTextNode(str(user)))
                    tr.appendChild(td)
                    table.appendChild(tr)
                body.appendChild(table)
            html.appendChild(body)
            page = dom.toxml(encoding="UTF-8").decode()
            page = page.replace('<?xml version="1.0"?>', '<?xml version="1.0" encoding="UTF-8"?>')
            response = page
            handler.send_response(200)
            handler.send_header('Content-type', 'text/html') # This is the MIME for HTML
            handler.end_headers() # We won't send more headers
            handler.wfile.write(response.encode())
        elif path.endswith('userlist.json'):
            # Create JSON:
            json_data = {}
            for channel in userlist.keys():
                json_data[channel] = json.dumps(list(self.userlist[channel]))
                response = str(json_data)
        elif path.endswith(stylesheet):
            with open(stylesheet) as f:
                handler.send_response(200)
                handler.send_header('Content-type', 'text/css') # This is the MIME for CSS data
                handler.end_headers()
                handler.wfile.write(f.read().encode())
        else:
             handler.send_response(404) # Not found
             handler.send_header('Content-type', 'text/html') # This is the MIME for HTML data
             handler.end_headers() # We won't send more headers
             handler.wfile.write(b"""
             <!DOCTYPE html>
             <html>
              <head>
               <meta charset="UTF-8">
               <title>Error</title>
              </head>
              <body>
               <h1>404 Not found</h1>
               <p>
                The document could not be found. Try one of these links:
                <a href="./userlist.html">User List</a>
                <a href="./userlist.json">User List, JSON format</a>
               </p>
              </body>
             </html>""")
             return

Class = UserList

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
