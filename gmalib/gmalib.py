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
import stat
import sys
try:
    import syslog
except ImportError, e:
    if os.name == "posix":
        print "can't import syslog: %s" % e


__version__ = "0.2"


class Logger:
    """Provides generic (and very basic) logging functionality.

    Provides a sub class with a methods which write to the
    syslog. When run on non POSIX operating systems it is assumed that
    syslog is unavailable and output is redirected to STDOUT instead.

    The code that calls Logger methods should set the facility by a
    call to syslog.openlog() from within the calling program or sub
    class.

    Public attributes:

    debug -- Debug messages are logged when true (default is false)

    """

    def __init__(self):
        """Initialises the object.

        Sets debug and log_to_console attributes to false by default.

        """

        if not hasattr(self, 'debug'):
            self.debug = 0

        # log to console if there's no syslog or we're debugging
        if (not os.name == "posix") or self.debug:
            self.log_to_console = 1
        else:
            self.log_to_console = 0

    def log_debug(self, message):
        """Write message to syslog with LOG_DEBUG priority.

        If the object's debug attribute is true then the message is
        written syslog with a priority of LOG_DEBUG.
        
        """

        if os.name == "posix":
            if self.debug:
                syslog.syslog(syslog.LOG_DEBUG, message)

        if self.log_to_console:
            print message

    def log_info(self, message):
        """Write message to syslog with LOG_INFO priority."""

        if os.name == "posix":
            syslog.syslog(syslog.LOG_INFO, message)

        if self.log_to_console:
            print message

    def log_notice(self, message):
        """Write message to syslog with LOG_NOTICE priority."""

        if os.name == "posix":
            syslog.syslog(syslog.LOG_NOTICE, message)

        if self.log_to_console:
            print message

    def log_err(self, message):
        """Write message to syslog with LOG_ERR priority."""

        if os.name == "posix":
            syslog.syslog(syslog.LOG_ERR, message)

        if self.log_to_console:
            print message


class Application(Logger):
    """A framework that provides generic application functionality.

    Currently, it's empty.

    """
    
    def __init__(self):
        """Calls the base class's initialiser."""
        
        Logger.__init__(self)


class Daemon(Application):
    """Provides an Application with simple daemon functionality (UNIX only).

    Any script that needs to run as a daemon (a background process)
    need only be written in an object oriented manner (e.g. wrap it up
    in a run() method, or similar), and specify this class as a base
    class.

    A call to self.daemonise() will convert the calling script into a
    daemon, unless it's be_daemon attribute is false (it defaults to
    true).

    Publically accessible attributes:

    be_daemon -- Run as a daemon when true (the default)

    """
    
    def __init__(self):
        """Initialises the base class and sets self.be_daemon to true."""
        
        Application.__init__(self)
        self.be_daemon = 1			# run as daemon by default

    def daemonise(self):
        """Convert the caller into a daemon (UNIX only).

        Forks a child process, exits the parent, makes the child a
        session leader and sets the umask to 0 (so programs run from
        within can set their own file permissions correctly). stdout
        and stderr are sent to syslog (LOG_INFO and LOG_ERR priority,
        respectively).

        """

        # UNIX only, sorry.

        if os.name != "posix":
            print "unable to run as a daemon (Unix only)"
            return None

        # Optionally run in the foreground (handy for debugging).

        if not self.be_daemon:
            return None

        # See "Python Standard Library", pg. 29, O'Reilly, for more
        # info on the following.
        
        self.log_debug("converting to a daemon")
        pid = os.fork()
        if pid:
            os._exit(0) # kill parent

        os.setpgrp()
        os.umask(0)

        # Redirect stdout and stderr to syslog.

        class _StdOutLogDevice(Logger):
            def __init__(self):
                Logger.__init__(self)
                
            def write(self, msg):
                self.log_info(msg)

        class _StdErrLogDevice(Logger):
            def __init__(self):
                Logger.__init__(self)
                
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


if __name__ == '__main__':
    import posixpath
    if "syslog" in dir():
        syslog.openlog(posixpath.basename(sys.argv[0]))
    d = Daemon()
    d.debug = 1
    print "converting to daemon... ",
    d.daemonise()
    print "done.",  # shouldn't see this!
    if "syslog" in dir():
        syslog.closelog()
