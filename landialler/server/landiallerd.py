#!/usr/bin/env python
#
# landiallerd.py - the LAN dialler daemon

"""Landialler Enables several computers on a home LAN to remotely
control a dial up device (e.g. modem) that is connected to a single
Unix workstation.

There are two programs that make up landialler; the client and the
server. This is the server that runs on the Unix workstation.

It runs in the background (as a daemon) waiting for landialler clients
to connect to it and request an Internet connection (through the
landialler XML-RPC API). By default it listens for connections on port
6543.

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
they exit immediately; the connect command MUST NOT hang around
indefinitely waiting to see if the connection has been made, but
should only check that the commands that it has run have started
correctly. If you know how to integrate landialler cleanly with your
own operating system's dial up systems then please send them in and
they will be made available on the web site (the author only uses
Debian).

More information on landialler is available at the project home page:

  http://landialler.sourceforge.net/

Author: Graham Ashton <ashtong@users.sourceforge.net>

"""

# $Id$
#
# Copyright Graham Ashton <ashtong@users.sourceforge.net>, 2001.

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

        config = gmalib.SingleConfigParser()
        cmd = config.get("commands", "connect")
        rval = os.system("%s > /dev/null 2>&1" % cmd)

        if rval == 0:
            return xmlrpclib.True
        else:
            return xmlrpclib.False

    def api_disconnect(self, params):
        """Disconnect from the Internet.

        Drops the Internet connection by running an external dial up
        termination script.

        As with api_connect(), the return value of the external script
        is not checked and the XML-RPC True value is always returned,
        irrespective of success.

        """

        config = gmalib.SingleConfigParser()
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

        config = gmalib.SingleConfigParser()
        cmd = config.get("commands", "is_connected")
        
        rval = os.system("%s > /dev/null 2>&1" % cmd)

        if rval == 0:
            return xmlrpclib.True
        else:
            return xmlrpclib.False


class App(gmalib.Daemon):
    """A simple wrapper class that initialises and runs the server."""
    
    def __init__(self):
        gmalib.Daemon.__init__(self)

    def main(self):
        """Read configuration, start the XML-RPC server."""

        syslog.openlog(posixpath.basename(sys.argv[0]),
                       syslog.LOG_PID | syslog.LOG_CONS)
        self.log_info("starting server")

        # load configuration files
        try:
            self.config = gmalib.SingleConfigParser()
            self.config.read(["/usr/local/etc/landiallerd.conf",
                              "/etc/landiallerd.conf", "landiallerd.conf"])
        except Exception, e:
            self.log_err("Terminating - error reading config file: %s" % e)
            sys.exit()

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
    app.be_daemon = 0  # uncomment to run in foreground (easier debugging)
    app.debug = 1
    app.main()
