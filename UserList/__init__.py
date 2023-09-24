"""
UserList: List users from a set of channels that the bot is on
"""

import sys
import supybot
from supybot import world

# Use this for the version of this plugin.
__version__ = "0.6"

__author__ = supybot.Author('Matias Wilkman', 'appas',
'matias.wilkman@gmail.com')

# This is a dictionary mapping supybot.Author instances to lists of
# contributions.
__contributors__ = {}

# This is a url where the most recent plugin package can be downloaded.
__url__ = 'https://github.com/matiasw/my-limnoria-plugins/UserList'

from . import config
from . import plugin
from importlib import reload
# In case we're being reloaded.
reload(config)
reload(plugin)
# Add more reloads here if you add third-party modules and want them to be
# reloaded when this plugin is reloaded.  Don't forget to import them as well!

if world.testing:
    from . import test

Class = plugin.Class
configure = config.configure


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
