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

import application
import os
import posixpath
import SocketServer
import sys
import syslog
import xmlrpclib
import xmlrpcserver


class MyTCPServer(SocketServer.TCPServer):
    """We override TCPServer so that we can set the allow_reuse_socket
    attribute to true (so we can restart immediately).

    """
    
    def __init__(self, server_address, RequestHandlerClass):
        self.allow_reuse_address = 1
        SocketServer.TCPServer.__init__(self, server_address,
                                        RequestHandlerClass)
        #print "reuse set to: %d" % self.allow_reuse_address
        

class App(application.Daemon):
    """Simple wrapper class that runs the server."""
    
    def __init__(self):
        application.Daemon.__init__(self)

    def read_config(self):
        """Map config file settings to instance attributes.

        This really ought to be sorted out so that load_sys_config()
        can do everything for us. Making a mental note to fix the
        library...

        """

        self.sys_config_files = ["/usr/local/etc/landiallerd.conf",
                                 "/etc/landiallerd.conf",
                                 "%s/landiallerd.conf" % os.getcwd()]
        self.load_sys_config()

        try:
            self.server_ip = self.config.get("server", "ip")
            self.server_port = int(self.config.get("server", "port"))

        except ConfigParser.ParsingError, e:
            self.log_err("Error reading config file: %s" % e)
            sys.exit()

        except ConfigParser.NoSectionError, e:
            self.log_err("Error reading config file: %s" % e)
            sys.exit()

        except ConfigParser.NoOptionError, e:
            self.log_err("Error reading config file: %s" % e)
            sys.exit()
        
    def run(self):
        """Start the landiallerd server.

        """

        syslog.openlog(posixpath.basename(sys.argv[0]),
                       syslog.LOG_PID | syslog.LOG_CONS)
        self.log_info("starting server")

        self.read_config()

        print "binding to %s:%d" % (self.server_ip, self.server_port)
        self.server = MyTCPServer((self.server_ip, self.server_port), MyHandler)
        self.server.serve_forever()

        syslog.closelog()



class MyHandler(xmlrpcserver.RequestHandler):
    """Defines methods that correspond to a procedure in the XML-RPC API."""

    def call(self, method, params):
        """Call the server side procedure and return the result.

        If the procedure doesn't exist then an AttributeError is
        raised, returning a fault to the client.

        """

	print "CALL: %s %s" % (method, params)

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
        dial up script.

        """

        print "connecting..."
        cmd = "pon"
        os.system(cmd)

        return xmlrpclib.True

    def api_disconnect(self, params):
        """Disconnects from the Internet.

        Drops the Internet connection by running an external dial up
        termination script.

        """

        print "disconnecting..."
        cmd = "poff"
        os.system(cmd)

        return xmlrpclib.True

    def api_is_connected(self, params):
        """Check if we are connected to the Internet.

        Runs the external command that is defined by the is_connected
        configuration file directive. The command should print a
        single line of output; 1 if we are connected to the Internet,
        0 otherwise.

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


if __name__ == '__main__':
    if os.name != "posix":
        print "Sorry, only Unix (and similar) operating systems are supported."
        sys.exit()

    app = App()
    app.daemonise = 0
    app.debug = 1
    app.run()
