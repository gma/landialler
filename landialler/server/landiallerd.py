#!/usr/bin/env python
#
# landiallerd.py - the LAN dialler daemon
#
# Copyright (C) 2001 Graham Ashton
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# $Id$

"""serves landialler XML-RPC requests

Landialler enables several computers on a home LAN to remotely
control a dial up device (e.g. modem) that is connected to a single
Unix workstation.

There are two programs that make up landialler; the client and the
server. This is the server that runs on the Unix workstation.

The client and server communicate via XML-RPC. The server runs in the
background (as a daemon) waiting for landialler clients to connect to
it and request an Internet connection (through the landialler XML-RPC
API). By default the server listen for connections on port 6543.

The client/server API defines three procedures that the client can
call; connect(), disconnect() and is_connected(). These are
individually documented in the MyHandler class (see below). Each
procedure runs an external script/program to perform their task,
making the landialler server more portable between different versions
of Unix, or distributions of Linux. Each command should return
immediately and exit with a non zero return code if there is an
error. Commands are specified in the [commands] section of the
landiallerd.conf configuration file.

A sample configuration file should be included with the package, but
the following should serve as a good example:

  [commands]
  connect: /usr/local/bin/dialup
  disconnet: /usr/local/bin/kill-dialup
  is_connected: /sbin/ifconfig ppp0

  [server]
  port: 6543

Note that you can also configure the TCP port number that landiallerd
uses to talk to the clients.

The connect and disconnect scripts above should both make sure that
they exit immediately; the connect command MUST NOT block before the
connection has been made, but should only check that the commands that
it has run have started correctly. If you know how to integrate
landialler cleanly with your own operating system's dial up systems
then please send them in and they will be made available on the web
site (the author only uses Debian).

Error, informational and debugging messages are written to the syslog.

More information on landialler is available at the project home page:

  http://landialler.sourceforge.net/

The author (Graham Ashton) can be contacted at ashtong@users.sourceforge.net.

"""

__version__ = "0.1"

import getopt
import gmalib
import os
import posixpath
import SocketServer
import sys
import syslog
import xmlrpclib
import xmlrpcserver


class MyTCPServer(SocketServer.TCPServer):
    """We override TCPServer so that we can set the allow_reuse_socket
    attribute to true (so we can restart immediately and the TCP
    socket doesn't sit in the CLOSE_WAIT state instead).

    """
    
    def __init__(self, server_address, RequestHandlerClass):
        """Initialise the server instance.

        Sets the allow_reuse_address attribute to true and then calls
        the base class's initialisor.

        """
        
        self.allow_reuse_address = 1
        SocketServer.TCPServer.__init__(self, server_address,
                                        RequestHandlerClass)


class MyHandler(xmlrpcserver.RequestHandler):
    """Defines methods that correspond to a procedure in the XML-RPC API."""

    def call(self, method, params):
        """Call the XML-RPC procedure and return it's result.

        Calls one of the other methods in this class (which define the
        server's API) and returns the other method's return value. If
        the procedure doesn't exist then an AttributeError is raised,
        returning a XML-RPC fault to the client.

        """

        try:
            server_method = getattr(self, "api_%s" % method)
        except:
            raise AttributeError, \
                  "Server does not have XML-RPC procedure %s" % method

        return server_method(params)

    ### remaining methods are part of the XML-RPC API.

    def api_connect(self, params):
        """Connect to the Internet.

        Attempts to connect to the Internet by running an external
        dial up script. This method currently blindly returns the
        XML-RPC True value, as it does not check the return value of
        the external script (the standard interface between
        landiallerd.py and external scripts is yet to be defined).
        This will be fixed in a future release.

        """

        config = gmalib.SharedConfigParser()
        cmd = config.get("commands", "connect")
        rval = os.system("%s > /dev/null 2>&1" % cmd)

        if rval == 0:
            return xmlrpclib.True
        else:
            return xmlrpclib.False

    def api_count_users(self, params):
        """Returns the number of clients currently using landiallerd."""

        from random import random
        return int(random() * 10)

    def api_disconnect(self, params):
        """Disconnect from the Internet.

        Drops the Internet connection by running an external dial up
        termination script.

        As with api_connect(), the return value of the external script
        is not checked and the XML-RPC True value is always returned,
        irrespective of success.

        """

        config = gmalib.SharedConfigParser()
        cmd = config.get("commands", "disconnect")
        rval = os.system("%s > /dev/null 2>&1" % cmd)

        if rval == 0:
            return xmlrpclib.True
        else:
            return xmlrpclib.False

    def api_is_connected(self, params):
        """Check if we are connected to the Internet.

        Runs an external command to determine whether or not the
        server is currently dialled up. If the external command exits
        with a return code of 0 then we return true, otherwise false.

        """

        config = gmalib.SharedConfigParser()
        cmd = config.get("commands", "is_connected")
        
        rval = os.system("%s > /dev/null 2>&1" % cmd)

        if rval == 0:
            return xmlrpclib.True
        else:
            return xmlrpclib.False

    def api_time_online(self, params):
        """Returns number of seconds the connection has been up.

        If the connection is down it returns -1 instead.

        """

        from random import random
        return int(random() * 10)


class App(gmalib.Daemon):
    """A simple wrapper class that initialises and runs the server."""
    
    def __init__(self):
        gmalib.Daemon.__init__(self)

    def getopt(self):
        """Parse command line arguments.

        Reads the command line arguments, looking for the following:

        -d   enable debugging for extra output
        -f   run in the foreground (not as a daemon)

        """

        opts, args = getopt.getopt(sys.argv[1:], "df")

        for o, v in opts:
            if o == "-d":
                self.debug = 1
            elif o == "-f":
                self.log_to_console = 1
                self.be_daemon = 0

        print "be_daemon=%s" % self.be_daemon
        self.log_debug("App.getopt(): opts=%s, args=%s" % (opts, args))

    def main(self):
        """Read configuration, start the XML-RPC server."""

        syslog.openlog(posixpath.basename(sys.argv[0]),
                       syslog.LOG_PID | syslog.LOG_CONS)
        self.log_info("starting server")

        self.getopt()

        # load configuration files
        try:
            self.config = gmalib.SharedConfigParser()
            self.config.read(["/usr/local/etc/landiallerd.conf",
                              "/etc/landiallerd.conf", "landiallerd.conf"])
        except Exception, e:
            self.log_err("Terminating - error reading config file: %s" % e)
            sys.exit()

        self.daemonise()

        # start the server and start taking requests
        server_port = int(self.config.get("server", "port"))
        self.server = MyTCPServer(("", server_port), MyHandler)
        self.server.serve_forever()

        syslog.closelog()


if __name__ == '__main__':
    if os.name != "posix":
        print "Sorry, only Unix (and similar) operating systems are supported."
        sys.exit()
    app = App()
    # app.be_daemon = 0  # uncomment to run in foreground (easier debugging)
    # app.debug = 1
    app.main()
