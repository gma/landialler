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


class Logger:

    """Provides generic (and very basic) logging functionality.

    Designed to be used as a mixin class, Logger provides objects with 
    methods for logging messages either to a file, or to syslog.

    """

    month_names = [None,
                 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    def __init__(self, log_file=None, use_syslog=0):
        """Initialises the object.

        If specified, the log_file attribute should be the name of a file to
        append log messages to. If the syslog attribute is true then
        messages will be written to syslog, on POSIX systems.

        """
        # default attributes
        self.log_file = log_file
        if os.name == "posix" and use_syslog:
            self.use_syslog = 1
        else:
            self.use_syslog = 0
        if not hasattr(self, 'debug'):
            self.debug = 0

        if self.use_syslog:
            syslog.openlog(posixpath.basename(sys.argv[0]),
                syslog.LOG_PID | syslog.LOG_CONS)
    
    def __del__(self):
        """Close syslog if it's in use."""
        if self.use_syslog:
            syslog.closelog()

    def _log_date_time_string(self):
        """Return the current time formatted for logging.

        The output format used is based on that used by the
        BaseHTTPServer class.

        """
        now = time.time()
        year, month, day, hh, mm, ss, x, y, z = time.localtime(now)
        s = "%3s %02d %04d %02d:%02d:%02d" % \
            (self.month_names[month], day, year, hh, mm, ss)
        return s

    def _to_file(self, priority, message):
        """Append a line to the log file, including priority and message.
        
        On POSIX systems the file is locked exclusively with flock() prior
        to writing.
        
        """
        date_time = self._log_date_time_string()
        fmt = "%s %s[%d] %5s: %s"
        if message[-1:] != "\n":
            fmt += "\n"
        file_obj = file(self.log_file, "a")
        if os.name == "posix":
            fcntl.flock(file_obj.fileno(), fcntl.LOCK_EX)
        file_obj.write(fmt % (date_time, posixpath.basename(sys.argv[0]),
                       os.getpid(), priority.upper(), message))
        file_obj.close()

    def log_debug(self, message):
        """Log a debug message."""
        if self.debug:
            if self.use_syslog:
                syslog.syslog(syslog.LOG_DEBUG, message)
            if self.log_file:
                self._to_file("debug", message)

    def log_info(self, message):
        """Log info message."""
        if self.use_syslog:
            syslog.syslog(syslog.LOG_INFO, message)
        if self.log_file:
            self._to_file("info", message)

    def log_notice(self, message):
        """Log a notice message."""
        if self.use_syslog:
            syslog.syslog(syslog.LOG_NOTICE, message)
        if self.log_file:
            self._to_file("notice", message)

    def log_err(self, message):
        """Log an error message."""
        if self.use_syslog:
            syslog.syslog(syslog.LOG_ERR, message)
        if self.log_file:
            self._to_file("error", message)


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
