#!/usr/bin/env python
#
# Copyright (C) 2001 Graham Ashton
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# $Id$


"""Provides classes used by, and developed solely for, the author's
own applications. Currently only very basic functionality required by
the average application or daemon is included.

"""


import ConfigParser
import os
import posixpath
import stat
import sys
import time


try:  # POSIX only modules
    import fcntl
    import syslog
except ImportError, e:
    pass


__version__ = '0.2.3'


class SharedConfigParser(ConfigParser.ConfigParser):

    """A ConfigParser that is only ever loaded once.

    Useful when several classes need access to the configuration data
    in a configuration file but you only want to read it once. You can
    instantiate several SharedConfigParser objects and the configuration
    file will only be read the first time an instance is created.
    Subsequent instances will share the data of the first instance.

    Use it in exactly the same way as you would use ConfigParser
    itself, but note that only the first call to read() will actually
    do anything.

    """

    __shared_state = {}

    def __init__(self, defaults=None):
        self.__dict__ = SharedConfigParser.__shared_state

        # only call base class's __init__() once 
        if not hasattr(self, "already_read"):
            self.already_read = 0
            ConfigParser.ConfigParser.__init__(self, defaults)

    def read(self, files):
        if self.already_read:  # ignore multiple calls to read()
            pass
        else:
            ConfigParser.ConfigParser.read(self, files)
            self.already_read = 1


def test():
    if "syslog" in dir():
        syslog.openlog(posixpath.basename(sys.argv[0]))
    
    log = Logger(log_file="test.log", use_syslog=1)
    log.log_info("an info log message")
    log.log_err("an error log message")
    log.log_notice("a notice log message")


if __name__ == '__main__':
    test()
