from supybot import utils, plugins, ircutils, callbacks, irclib, world, httpserver, conf
import supybot.log as log
from supybot.commands import *
from supybot.i18n import PluginInternationalization
# HTML Generation imports:
from typing import List
from xml.dom.minidom import getDOMImplementation, Document
#JSON Generation:
import json
import datetime
#timezone:
import tzlocal

_ = PluginInternationalization('UserList')

stylesheet = "none"

class UserList(callbacks.Plugin):
    def __init__(self, irc):
        super().__init__(irc)
        #register http server callback:
        callback = UserListServerCallback(self)
        global stylesheet
        stylesheet = self.registryValue("stylesheet")
        httpserver.hook('userlist', callback)

    def die(self):
        #unregister callback:
        httpserver.unhook('userlist')
        super().die()

class UserListServerCallback(httpserver.SupyHTTPServerCallback):
    name = 'UserList'
    defaultResponse = """
        This plugin handles only GET request, please don't use other requests.
        Content served: userlist.html, userlist.json"""

    def __init__(self, plugin):
        self.plugin = plugin

    def doGet(self, handler, path):

        userlist = self.updatelist()
        stylesheet = self.plugin.registryValue("stylesheet")

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
                try:
                    with open(stylesheet) as f:
                        style = dom.createElement("style")
                        style.setAttribute("type", "text/css")
                        style.appendChild(dom.createTextNode(f.read()))
                        head.appendChild(style)
                except FileNotFoundError:
                    log.error("Stylesheet file not found: %s", stylesheet)
            title = dom.createElement("title")
            title.appendChild(dom.createTextNode("User List"))
            head.appendChild(title)
            html.appendChild(head)
            body = dom.createElement("body")
            # Get the local timezone
            local_timezone = tzlocal.get_localzone()
            # Get the UTC offset
            utc_offset = datetime.datetime.now(local_timezone).strftime('%z')
            paragraph = dom.createElement("p")
            paragraph.appendChild(dom.createTextNode("User list created at " +
                                                str(datetime.datetime.now()
                                                    .strftime("%d.%m.%Y, %I:%M:%S") + f" Time zone: {local_timezone}, UTC Offset: {utc_offset}")))
            body.appendChild(paragraph)
            for channel in userlist.keys():
                table = dom.createElement("table")
                tr = dom.createElement("tr")
                th = dom.createElement("th")
                th.appendChild(dom.createTextNode(channel))
                tr.appendChild(th)
                table.appendChild(tr)
                sorted_users = sorted(userlist.get(channel, []), key=str.lower)
                for user in sorted_users:
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
            handler.send_header('Content-type', 'application/xhtml+xml') 
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

    """List users from channels that the bot is on"""
    def updatelist(self):
        userlist = {}
        for otherIrc in world.ircs:
            for (channel, channel_state) in otherIrc.state.channels.items():
                channelname = channel + "@" + otherIrc.network
                log.info("channel: " + str(channelname))
                if channelname in self.plugin.registryValue("channels"):
                    excluded_users = self.plugin.registryValue("ignorednicks")
                    userlist[channelname] = [user for user in channel_state.users if user not in excluded_users]
                else:
                    log.debug(channelname + " not in channel list, which is " +
str(self.plugin.registryValue("channels")))
        return userlist

Class = UserList

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
