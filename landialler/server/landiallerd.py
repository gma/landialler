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
call; connect(), disconnect() and get_status(). These are individually
documented below. Each procedure runs an external script/program to
perform their task, making the landialler server more portable between
different versions of Unix, or distributions of Linux. Each command
should return immediately and exit with a non zero return code if
there is an error. Commands are specified in the [commands] section of
the landiallerd.conf configuration file.

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

The connect and disconnect scripts referenced in the config file
should both make sure that they exit immediately; the connect command
MUST NOT block before the connection has been made, but should only
check that the commands that it has run have started correctly. If you
know how to integrate landialler cleanly with your own operating
system's dial up systems then please send suggestions in and they will
be made available on the web site, with credits.

Error, informational and debugging messages are written to the syslog.

More information on landialler is available at the project home page:

  http://landialler.sourceforge.net/

The author (Graham Ashton) can be contacted at ashtong@users.sourceforge.net.

"""


__version__ = "0.2pre1"


import getopt
import gmalib
import os
import posixpath
import SocketServer
import sys
import time
import xmlrpclib
import xmlrpcserver


try:
    import syslog
except ImportError, e:
    if os.name == 'posix':
        print "can't import syslog: %s" % e


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


class MyHandler(gmalib.Logger, xmlrpcserver.RequestHandler):

    """Defines methods that correspond to a procedure in the XML-RPC API."""

    def __init__(self, *args, **kwargs):
        self.is_connected = 0   # are we currently online?
        self.current_users = 0  # number of clients using connection

        # FIXME: call base class' __init__ methods safely, so that the
        # super classes can change internally without blowing this up.

        gmalib.Logger.__init__(self)
        SocketServer.BaseRequestHandler.__init__(self, *args, **kwargs)

        self.debug = 1

    def call(self, method, params):
        """Call an API procedure, return it's result.

        Calls one of the methods whose name begins with "api_". For
        example, if method is set to "a_method" then the
        "api_a_method" will be called. If the method doesn't exist
        then an AttributeError is raised, returning a XML-RPC fault to
        the client.

        """
        my_api = ['connect', 'disconnect', 'get_status']
        if not method in my_api:
            raise xmlrpclib.Fault(123, 'Unknown method name')
        else:
            if method == 'get_status':
                (host, port) = self.client_address
                params = (host,)
            elif method == 'disconnect':
                (host, port) = self.client_address
                params = (params[0], host)
            return apply(eval("api_" + method), params)
            


class App(gmalib.Daemon):

    """A simple wrapper class that initialises and runs the server."""
    
    def __init__(self):
        gmalib.Daemon.__init__(self)

    def getopt(self):
        """Parse command line arguments.

        Reads the command line arguments, looking for the following:

        -d  enable debugging for extra output
        -f  run in the foreground (not as a daemon)

        """
        opts, args = getopt.getopt(sys.argv[1:], "dft")

        for o, v in opts:
            if o == "-d":
                self.debug = 1
            elif o == "-f":
                self.log_to_console = 1
                self.be_daemon = 0

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


# The functions that follow define the XML-RPC API. They are not part
# of the MyHandler class for a very good reason (namely that MyHandler
# objects aren't stateful and making them so appears to be needlessly
# complex).
#
# We maintain state via three global variables:
#
#   current_users  -- the number of people sharing the connection
#   user_tracker   -- dict of clients and when they checked the status
#   is_connected   -- whether or not the server is connected


def api_connect():
    """Open the connection.

    If the server is already connected the the XML-RPC True value is
    returned.

    Otherwise an attempt is made to make a connection by running
    an external dial up script. If the external script runs
    successfully (and therefore returns 0) then the XML-RPC True
    value is returned, False otherwise. The script should return
    immediately (i.e. not block whilst the connection is made)
    irrespective of whether or not the actual connection will be
    successfully set up by the script.

    """
    global is_connected
    if is_connected:
        return xmlrpclib.True

    else:
        config = gmalib.SharedConfigParser()
        cmd = config.get("commands", "connect")
        rval = os.system("%s > /dev/null 2>&1" % cmd)

        if rval == 0:
            return xmlrpclib.True
        else:
            return xmlrpclib.False


def api_disconnect(all='no', client=None):
    """Close the connection.

    If there are other users online and the all argument is not set
    then the XML-RPC True value is returned.

    Otherwise the connection is dropped by running an external dial up
    termination script. As with api_connect(), the return value of the
    external script is converted into the XML-RPC True or False value,
    and returned.

    """
    global current_users
    print "all: %s, users: %s" % (all, client)
    if (current_users - 1 > 0) and (all != 'yes'):  # other users still online
        del user_tracker[client]
        return xmlrpclib.True

    else:
        config = gmalib.SharedConfigParser()
        cmd = config.get("commands", "disconnect")
        rval = os.system("%s > /dev/null 2>&1" % cmd)
        if rval == 0:
            user_tracker.clear()
            return xmlrpclib.True
        else:
            return xmlrpclib.False


def api_get_status(client):
    """Return current_users and is_connected."""
    global current_users, user_tracker, is_connected

    # register client's connection, purge old data
    now = time.time()
    user_tracker[client] = now
    timeout = 30  # seconds before a user times out
    for client in user_tracker.keys():
        if (now - user_tracker[client]) > timeout:
            del user_tracker[client]

    # get current_users and is_connected
    config = gmalib.SharedConfigParser()
    cmd = config.get("commands", "is_connected")
    rval = os.system("%s > /dev/null 2>&1" % cmd)
    if rval == 0:
        current_users = len(user_tracker.keys())
        is_connected = 1
    else:
        current_users = 0  # ignore contents of user_tracker, we're not online
        is_connected = 0

    return (current_users, is_connected)


if __name__ == '__main__':
    if os.name != "posix":
        print "Sorry, only POSIX compliant systems are currently supported."
        sys.exit()

    # global variables for maintaining state
    user_tracker = {}  # dict of all users' IP/port numbers
    current_users = 0  # number of users online (determined from user_tracker)
    is_connected = 0   # is the connection currently up?

    app = App()
    app.be_daemon = 0  # uncomment to run in foreground (easier debugging)
    app.debug = 1
    app.main()
