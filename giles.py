#!/usr/bin/env python2
# Giles: giles.py, the main loop.
# Copyright 2012 Phil Bordelon
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import ConfigParser
import giles.server
import sys

cp = ConfigParser.SafeConfigParser()
cp.read("giles.conf")

if not cp.has_option("server", "source_url"):
    print("You absolutely must provide a giles.conf with a valid source_url.")
    print("See giles.conf.sample for more information.")
    sys.exit(1)

source_url = cp.get("server", "source_url")

if not cp.has_option("server", "name"):
    name = "Giles"
else:
    name = cp.get("server", "name")

# No need to keep the config parser around now that we're done with it.
del cp

server = giles.server.Server(name, source_url)

if len(sys.argv) == 2:
   port = int(sys.argv[1])
else:
   port = 9435
server.instantiate(port)
server.loop()
