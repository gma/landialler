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

import BaseHTTPServer
import posixpath
import SocketServer
import sys
import syslog
import xmlrpclib
import xmlrpcserver

from harpoon.Log import Log
from harpoon.application import Daemon

class App(Daemon):
    """Simple wrapper class that runs the server."""
    
    def __init__(self):
        Daemon.__init__(self)
        print "running App.__init__()"
        self.debug = 1 # prevents daemonising when true

    def run(self):
        syslog.openlog(posixpath.basename(sys.argv[0]),
                       syslog.LOG_PID | syslog.LOG_CONS)
        self.log_info("starting server")
        self.load_sys_config("/usr/local/etc/landiallerd.conf")
        self.server = SocketServer.TCPServer(('', 8090), LandiallerHandler)
        self.server.serve_forever()


class LandiallerHandler(xmlrpcserver.RequestHandler):
    """Defines methods that correspond to a procedure in the XML-RPC API.

    Other methods are already defined in the super classes though, so
    read the docs with care...

    """

    def call(self, method, params):
        """Call the server side procedure and return the result.

        If the procedure doesn't exist then an AttributeError is
        raised, returning a fault to the client.

        """

	print "CALL: %s(%s)" % (method, params)
        try:
            server_method = getattr(self, method)
        except:
            raise AttributeError, \
                  "Server does not have XML-RPC procedure %s" % method

        return server_method(method, params)

    def is_connected(self, params):
        """Check if we are connected to the Internet.

        Returns true if the server is connected to the Internet, false
        otherwise.

        """

        # Currently, this stuff is only designed to work with ppp
        # interfaces on UNIX like operating systems. If you'd like to
        # get this working from your Windows box and mail me a patch,
        # that'd be spiffing. If you'd do the same for some other
        # operating system, that'd be even better.

        try:
            if os.name == "posix":
                return linux_is_connected(self, params)
            else:
                raise NotImplementedError

        except NotImplementedError:
            print "Sorry, non POSIX compliant servers are not supported."
            sys.exit()
        
        
    def linux_is_connected(self, params):
        """Checks to see if we're connected on a POSIX operating system.

        Parses the output of the /sbin/ifconfig command to see if
        there is a ppp interface up.

        """

        return xmlrpclib.True


if __name__ == '__main__':
    app = App()
    app.run()
