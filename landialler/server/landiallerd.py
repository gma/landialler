#!/usr/bin/env python
#
# landiallerd.py - the LAN dialler daemon
#
# Provides several computers on a home LAN with the functionality
# required to be able to dial up the Internet (e.g. via modem) in
# situations where only one computer provides connectivity (e.g. via
# NAT) to a group of workstations.
#
# In other words, if you only have one modem and can set your network
# up so that one computer routes packets between your other computers
# and the Internet, this software can help you start/stop the
# connection from the other computers.
#
# This daemon runs on the computer that connects directly to the
# Internet and provides the clients with limited access to the modem,
# via an XML-RPC API.
#
# Copyright Graham Ashton <ashtong@users.sourceforge.net>, 2001.
#
# $Id$

import ConfigParser
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

        Calls one of the other methods in this class (which in
        themselves define the server's API) and returns the other
        method's return value. If the procedure doesn't exist then an
        AttributeError is raised, returning a XML-RPC fault to the
        client.

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

        cmd = "pon"
        os.system(cmd)

        return xmlrpclib.True

    def api_disconnect(self, params):
        """Disconnects from the Internet.

        Drops the Internet connection by running an external dial up
        termination script.

        As with api_connect(), the return value of the external script
        is not checked and the XML-RPC True value is always returned,
        irrespective of success.

        """

        cmd = "poff"
        os.system(cmd)

        return xmlrpclib.True

    def api_is_connected(self, params):
        """Check if we are connected to the Internet.

        Runs an external command to determine whether or not the
        server is currently dialled up. Currently, the external
        command prints a 1 to it's stdout if the server is connected,
        0 otherwise. This behaviour may be changed in a future
        release, and the command itself will be moved into the
        configuration file.

        """

        cmd = "/sbin/ifconfig | perl -e 'undef($/); $_ = <STDIN>; " + \
              "printf \"%s\", /ppp0/? 1 : 0'"
        fd = os.popen(cmd)
        is_conn = int(fd.read(1))
        fd.close()

        if is_conn == 1:
            return xmlrpclib.True
        else:
            return xmlrpclib.False


class App(gmalib.Daemon):
    """A simple wrapper class that initialises and runs the server."""
    
    def __init__(self):
        """Calls the base class's initialisor."""
        gmalib.Daemon.__init__(self)

    def run(self):
        """Start the landiallerd server."""

        syslog.openlog(posixpath.basename(sys.argv[0]),
                       syslog.LOG_PID | syslog.LOG_CONS)
        self.log_info("starting server")

        # load configuration files
        try:
            self.config = ConfigParser.ConfigParser()
            self.config.read(["/usr/local/etc/landiallerd.conf",
                              "/etc/landiallerd.conf", "landiallerd.conf"])
            server_ip = self.config.get("server", "ip")
            server_port = self.config.get("server", "port")

        except ConfigParser.ParsingError, e:
            self.log_err("Error reading config file: %s" % e)
            sys.exit()

        except ConfigParser.NoSectionError, e:
            self.log_err("Error reading config file: %s" % e)
            sys.exit()

        except ConfigParser.NoOptionError, e:
            self.log_err("Error reading config file: %s" % e)
            sys.exit()

        # start the server and start taking requests
        self.server = MyTCPServer((server_ip, server_port), MyHandler)
        self.server.serve_forever()

        syslog.closelog()


if __name__ == '__main__':
    if os.name != "posix":
        print "Sorry, only Unix (and similar) operating systems are supported."
        sys.exit()

    app = App()
    # app.be_daemon = 0  # uncomment to run in foreground (easier debugging)
    app.debug = 1
    app.run()
