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

try:
    import syslog
except ImportError, e:
    if os.name == "posix":
        sys.stderr.write("can't import syslog: %s" % e)


__version__ = "0.2"


class Logger:

    """Provides generic (and very basic) logging functionality.

    Designed to be used as a mixin class, Logger provides objects with 
    methods for logging messages either to a file, or to syslog.

    """

    # class vars used for creating log time stamps
    weekdayname = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    monthname = [None,
                 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    def __init__(self, file=None, use_syslog=0):
        """Initialises the object.

        If specified, the file attribute should be the name of a file to
        append log messages to. If the syslog attribute is true then
        messages will be written to syslog, on POSIX systems.

        """
        # default attributes
        self.file = file
        self.use_syslog = use_syslog
        if not hasattr(self, 'debug'):
            self.debug = 0

        if self.use_syslog:
            syslog.openlog(posixpath.basename(sys.argv[0]),
                syslog.LOG_PID | syslog.LOG_CONS)
    
    def __del__(self):
        """Close syslog if it's in use."""
        if self.use_syslog:
            syslog.closelog()

    def log_date_time_string(self):
        """Return the current time formatted for logging."""
        now = time.time()
        year, month, day, hh, mm, ss, x, y, z = time.localtime(now)
        s = "%02d/%3s/%04d %02d:%02d:%02d" % \
            (day, self.monthname[month], year, hh, mm, ss)
        s = "%3s %02d %04d %02d:%02d:%02d" % \
            (self.monthname[month], day, year, hh, mm, ss)
        return s

    def _to_file(self, priority, message):
        f = open(self.file, "a")
        date_time = self.log_date_time_string()
        f.write("%s [%s]: %s\n" % (date_time, priority.upper(), message))
        f.close()

    def log_debug(self, message):
        """Log debug message."""

        if self.debug:
            if self.use_syslog:
                syslog.syslog(syslog.LOG_DEBUG, message)
            if self.file:
                self._to_file("debug", message)

    def log_info(self, message):
        """Log info message."""
        if self.use_syslog:
            syslog.syslog(syslog.LOG_INFO, message)
        if self.file:
            self._to_file("info", message)

    def log_notice(self, message):
        """Log a notice message."""
        if self.use_syslog:
            syslog.syslog(syslog.LOG_NOTICE, message)
        if self.file:
            self._to_file("notice", message)

    def log_err(self, message):
        """Log an error message."""
        if self.use_syslog:
            syslog.syslog(syslog.LOG_ERR, message)
        if self.file:
            self._to_file("error", message)


class Daemon:

    """Provides an application with basic daemon functionality (UNIX only).

    Any script that needs to run as a daemon (a background process)
    need only be written in an object oriented manner (e.g. wrap it up
    in a run() method, or similar), and specify this class as a base
    class. Treat it as a mixin class.

    A call to self.daemonise() will convert the calling script into a
    daemon. The sys.stdout and sys.stderr file handles are re-directed
    via a Logger object that 

    """
    
    def __init__(self, **log_args):
        """Initialistion.
        
        Keyword arguments passed via the **log_args argument are passed
        straight into the Logger object that sys.stdout and sys.stderr
        are redirected to, so can be used to configure the logging
        options.
        
        """
        self.log_args = log_args

    def daemonise(self):
        """Convert the caller into a daemon (POSIX only).

        Forks a child process, exits the parent, makes the child a
        session leader and sets the umask to 0 (so programs run from
        within can set their own file permissions correctly). stdout
        and stderr are sent to syslog (LOG_INFO and LOG_ERR priority,
        respectively).

        """
        # UNIX only, sorry.
        if os.name != "posix":
            print "unable to run as a daemon (POSIX only)"
            return None

        # See "Python Standard Library", pg. 29, O'Reilly, for more
        # info on the following.
        print "converting to a daemon"
        pid = os.fork()
        if pid:
            os._exit(0) # kill parent

        os.setpgrp()
        os.umask(0)

        # Redirect stdout and stderr to syslog.
        class _StdOutLogDevice(Logger):
            def __init__(self):
                Logger.__init__(self, self.log_args)
                
            def write(self, msg):
                self.log_info(msg)

        class _StdErrLogDevice(Logger):
            def __init__(self):
                Logger.__init__(self, self.log_args)
                
            def write(self, msg):
                self.log_err(msg)

        sys.stdin.close()
        sys.stdout = _StdOutLogDevice()
        sys.stderr = _StdErrLogDevice()


class SharedConfigParser(ConfigParser.ConfigParser):

    """Useful when several classes need access to the configuration
    data in a configuration file but you only want to read it
    once. You can instantiate several SharedConfigParser objects (one
    per class) and the configuration file will only be read the first
    time an instance is created. Subsequent instances will share the
    data of the first instance.

    Use it in exactly the same way as you would use ConfigParser
    itself.

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
    
    log = Logger(file="test.log", use_syslog=1)
    log.log_info("an info log message")
    log.log_err("an error log message")
    log.log_notice("a notice log message")
    #d = Daemon()
    #d.debug = 1
    #print "converting to daemon... ",
    #d.daemonise()
    #print "done.",  # shouldn't see this!
    #if "syslog" in dir():
    #    syslog.closelog()



if __name__ == '__main__':
    test()