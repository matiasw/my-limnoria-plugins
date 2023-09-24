from supybot import utils, plugins, ircutils, callbacks, irclib, world, httpserver
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

userlist = {}

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
            #stylesheet = UserList.registryValue("stylesheet")
            #if (stylesheet != "none"):
            #    style = dom.createElement("link")
            #    style.setAttribute("rel", "stylesheet")
            #    style.setAttribute("href", stylesheet)
            #    html.appendChild(style)
            title = dom.createElement("title")
            title.appendChild(dom.createTextNode("User List"))
            html.appendChild(title)
            html.appendChild(dom.createTextNode("User list created at " +
                                                str(datetime.datetime.now()
                                                    .strftime("%d.%m.%Y, %I:%M:%S"))))
            for channel in userlist.keys():
                table = dom.createElement("table")
                tr = dom.createElement("tr")
                th = dom.createElement("th")
                th.appendChild(dom.createTextNode(channel))
                tr.appendChild(th)
                table.appendChild(tr)
                for user in userlist[channel]:
                    tr = dom.createElement("tr")
                    td = dom.createElement("td") 
                    td.appendChild(dom.createTextNode(str(user)))
                    tr.appendChild(td)
                    table.appendChild(tr)
                html.appendChild(table)
            response = dom.toxml()
        elif path.endswith('userlist.json'):
            # Create JSON:
            json_data = {}
            for channel in userlist.keys():
                json_data[channel] = json.dumps(list(self.userlist[channel]))
                response = str(json_data)
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
                The document could not be found. Try one of this links:
                <a href="./userlist.html">User List</a>
                <a href="./userlist.json">User List, JSON format</a>
               </p>
              </body>
             </html>""")
             return
        handler.send_response(200)
        handler.send_header('Content-type', 'text/html') # This is the MIME for HTML
        handler.end_headers() # We won't send more headers
        handler.wfile.write(response.encode())

class UserList(callbacks.Plugin):
    def __init__(self, irc):
        super().__init__(irc)
        self.updatelist(irc, None)
        #register http server callback:
        callback = UserListServerCallback()
        httpserver.hook('userlist', callback)

    def die(self):
        #unregister callback:
        httpserver.unhook('userlist')
        super().die()

    """List users from channels that the bot is on"""
    def updatelist(self, irc, msg):
        for otherIrc in world.ircs:
            for (channel, channel_state) in otherIrc.state.channels.items():
                channelname = channel + "@" + otherIrc.network
                if channelname in self.registryValue("channels"):
                    userlist[channelname] = channel_state.users
                else:
                    log.info(channelname + " not in channel list, which is " +
str(self.registryValue("channels")))
    
    def doJoin(self, irc, msg):
        self.updatelist(irc, msg)
    
    def doPart(self, irc, msg):
        self.updatelist(irc, msg)

    def doQuit(self, irc, msg):
        self.updatelist(irc, msg)
        
Class = UserList

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
