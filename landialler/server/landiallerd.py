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


"""serves landialler clients, manages connecctions

LANdialler enables several computers on a home LAN to remotely control
a dial up device (e.g. modem) that is connected to a single Unix
workstation. This scenario is explained in more detail on the
LANdialler web site.

There are two programs that make up a complete LANdialler system; the
client (landialler) and the server (landiallerd). This is the server
that runs on the Unix workstation.

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
  connect: /usr/local/bin/start-connection
  disconnet: /usr/local/bin/stop-connection
  is_connected: /sbin/ifconfig ppp0 | grep "inet addr" >/dev/null

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

To see a list of the available command line options, use the -h
switch. For example, error, informational and debugging messages can
be written to the syslog if the -s switch is used, or to a separate
log file if -l is used.

More information on landialler is available at the project home page:

  http://landialler.sourceforge.net/

The author can be contacted at ashtong@users.sourceforge.net.

"""


__version__ = "0.2.1"


import getopt
import gmalib
import os
import SocketServer
import sys
import threading
import time
import xmlrpclib
import xmlrpcserver

try:
    import syslog
except ImportError, e:
    if os.name == "posix":
        sys.stderr.write("can't import syslog: %s" % e)


class Connection:

    """Controls a dial up connection.

    Provides methods for controlling/querying the status of a dial up
    connection (e.g. modem connection to the Internet). All instances
    of this class share their state (see the Borg design pattern in
    the ASPN Python Cookbook) so that status information is maintained
    between different client HTTP requests.

    The following methods are part of the LANdialler XML-RPC API, and
    are called directly whenever a client makes an HTTP request to the
    server:

      connect()
      disconnect()
      get_status()

    Their return values are passed directly back to the XML-RPC
    clients.

    Other methods should only be used either from within these
    methods, or from within other parts of the landiallerd application.

    """

    __shared_state = {}

    def __init__(self):
        self.__dict__ = Connection.__shared_state
        if not hasattr(self, "clientTracker"):
            print "initialising Connection() attributes"
            self.clientTracker = {}
            self.config = gmalib.SharedConfigParser()
            self.nowConnecting = 0

    def connect(self):
        """Open the connection.

        If the server is already connected the XML-RPC True value is
        returned. If the server is in the process of connecting then
        an XML-RPC False value is returned.

        Otherwise an attempt is made to make a connection by running
        an external dial up command (see landiallerd.conf). If the
        external command runs successfully (and therefore returns 0)
        then the XML-RPC True value is returned, False otherwise. The
        external command should return immediately (i.e. not block
        whilst the connection is made) irrespective of whether or not
        the actual connection will be successfully set up immediately.

        """
        if self.isConnected():
            return xmlrpclib.True
        elif self.nowConnecting:
            return xmlrpclib.False
        else:
            cmd = self.config.get("commands", "connect")
            rval = os.system("%s > /dev/null 2>&1" % cmd)
            if rval == 0:
                self.nowConnecting = 1
                print "connect command ran successfully"
                return xmlrpclib.True
            else:
                sys.stderr.write("connect command failed (%s)\n" % rval)
            return xmlrpclib.False

    def countClients(self):
        """Return the number of active clients."""
        self.forgetOldClients()
        return len(self.clientTracker.keys())

    def disconnect(self, all="no", client=None):
        """Close the connection.

        If there are other users online and the all argument is not
        set to "yes" then the XML-RPC True value is returned.

        Otherwise the connection is dropped by running an external
        dial up termination script. As with connect(), the return
        value of the external script is converted into the XML-RPC
        True or False value, and returned.

        The client argument should uniquely identify the client, and
        should be usable as a dictionary key.

        """
        if (self.countClients() > 1) and (all != "yes"):
            self.forgetClient(client)
            return xmlrpclib.True
        else:
            cmd = self.config.get("commands", "disconnect")
            rval = os.system("%s > /dev/null 2>&1" % cmd)
            if rval == 0:
                self.nowConnecting = 0
                self.forgetAllClients()
                print "disconnect command run successfully"
                return xmlrpclib.True
            else:
                sys.stderr.write("disconnect command failed (%s)\n" % rval)
                return xmlrpclib.False

    def get_status(self, client):
        """Returns the number of clients and connection status.

        The client parameter should uniquely identify the client, and
        should be usable as a dictionary key. The IP address is
        usually used.

        The two values returned are:

        current_clients -- The number of users sharing the connection
        is_connected    -- 1 if connected, 0 otherwise

        """
        self.rememberClient(client)
        if self.isConnected() and self.nowConnecting:
            self.nowConnecting = 0
            numClients = self.countClients()
        else:
            numClients = 0
        return (numClients, self.isConnected())

    def rememberClient(self, client):
        """Record time of the client's last HTTP connection."""
        self.clientTracker[client] = time.time()

    def forgetClient(self, client):
        """Stop treating this client as active."""
        try:
            del self.clientTracker[client]
        except KeyError:
            pass

    def forgetAllClients(self):
        """Assume that all clients are inactive."""
        self.clientTracker.clear()

    def forgetOldClients(self):
        """Forget about clients that haven't connected recently.

        We keep track of the number of users by counting the number
        that have connected recently. If a client hasn't connected in
        the last 30 seconds it is deemed to have died and isn't
        counted any more.

        """
        timeout = 30
        for client in self.clientTracker.keys():
            if (time.time() - self.clientTracker[client]) > timeout:
                self.forgetClient(client)

    def isConnected(self):
        """Return 1 if the connection is up, 0 otherwise.

        Runs the external command as specified in the configuration
        file to determine if the connection is up.

        """
        cmd = self.config.get("commands", "is_connected")
        rval = os.system("%s > /dev/null 2>&1" % cmd)
        if rval == 0:
            self.nowConnecting = 0
            return 1
        else:
            return 0


class CleanerThread(threading.Thread, gmalib.Logger):

    """Ensures that the connection does not remain live with no clients.

    If a client is not shut down cleanly it may not be able to call
    the API's disconnect procedure, thereby leaving the connection
    open when there are no clients left. This is bad, as it could lead
    to an expensive telephone bill.

    This thread periodically makes sure that the connection is not
    alive when tere are no users. If it is, the Connection.disconnect()
    method is called.

    """

    def __init__(self, interval=10):
        """Setup the thread object.

        The thread is set to be a daemon thread, so that the server
        exits without worrying about closing this thread.

        The object also creates an Event object for itself, to
        facilitate a timer. The timer is used to execute the contents
        of the run() method every "interval" seconds.

        """
        threading.Thread.__init__(self, name=CleanerThread)
        self.setDaemon(1)
        self.interval = interval  # time before re-running clean up
        self.pauser = threading.Event()

        self.debug = debug
        gmalib.Logger.__init__(self, logfile=logfile, use_syslog=use_syslog)

    def run(self):
        # See http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/65222
        # for a full example of the while loop's timer code.

        conn = Connection()
        while 1:
            self.log_debug("CleanerThread: users=%s, connected=%s" %
                           (conn.countClients(), conn.isConnected()))
            if (conn.countClients() < 1) and \
               (conn.nowConnecting or conn.isConnected()):
                self.log_debug("CleanerThread: disconnecting")
                conn.disconnect(all="yes")

            self.pauser.wait(self.interval)


class MyTCPServer(SocketServer.TCPServer):

    """We override TCPServer so that we can set the allow_reuse_socket
    attribute to true (so we can restart immediately and the TCP
    socket doesn't sit in the CLOSE_WAIT state instead).

    """
    
    def __init__(self, server_address, RequestHandlerClass):
        """Initialise the server instance.

        Sets the allow_reuse_address and debug attributes. Calls the base
        class's initialiser.

        """
        self.allow_reuse_address = 1
        SocketServer.TCPServer.__init__(self, server_address,
                                        RequestHandlerClass)
    

class MyHandler(xmlrpcserver.RequestHandler, gmalib.Logger):

    """Handles XML-RPC requests."""

    def __init__(self, *args, **kwargs):
        global debug, logfile, use_syslog
        self.debug = debug
        gmalib.Logger.__init__(self, logfile=logfile, use_syslog=use_syslog)

        # FIXME: iterate through all base class' __init__ methods so that
        #        class hierarchy can change without us worrying about it.
        SocketServer.BaseRequestHandler.__init__(self, *args, **kwargs)

    def call(self, procedure, params):
        """Call an API procedure, return it's result.

        Calls one of the API's methods on an instance of the
        Connection class. If the procedure isn't supported then an
        AttributeError is raised, returning a XML-RPC fault to the
        client.

        """
        if not procedure in ["connect", "disconnect", "get_status"]:
            self.log_err("Unknown procedure name: %s" % procedure)
            raise xmlrpclib.Fault, "Unknown procedure name: %s" % procedure
        else:
            conn = Connection()
            method = getattr(conn, procedure)
            if procedure == "get_status":
                (host, port) = self.client_address
                params = (host,)
            elif procedure == "disconnect":
                (host, port) = self.client_address
                disconnectAllUsers = params[0]
                params = (disconnectAllUsers, host)
            self.log_debug("called %s(%s)" % \
                           (procedure, ", ".join(map(repr, params))))
            return apply(method, params)

    def log_request(self, code="-", size="-"):
        """Requests are logged if running in debug mode."""
        if self.debug:
            self.log_debug('%s - - [%s] "%s" %s %s\n' % \
                           (self.address_string(),
                           self.log_date_time_string(),
                           self.requestline, str(code), str(size)))


class App(gmalib.Daemon):

    """A simple wrapper class that initialises and runs the server."""
    
    def __init__(self):
        gmalib.Daemon.__init__(self)
        self.debug = 0
        self.runAsDaemon = 1

    def checkPlatform(self):
        """Check OS is supported."""
        if os.name != "posix":
            print "Sorry, only POSIX compliant systems are supported."
            sys.exit()

    def daemonise(self):
        """Run parent's daemonise() if runAsDaemon attribute is set."""
        if self.runAsDaemon:
            gmalib.Daemon.daemonise(self)

    def getopt(self):
        """Parse command line arguments.

        Reads the command line arguments, looking for the following:

        -d          enable debugging for extra output
        -f          run in the foreground (not as a daemon)
        -h          print usage message to stderr
        -l file     log events to file
        -s          log events to syslog

        """
        opts, args = getopt.getopt(sys.argv[1:], "dfhl:s")

        for o, v in opts:
            if o == "-d":
                global debug
                debug = self.debug = 1
            elif o == "-f":
                self.runAsDaemon = 0
            elif o == "-h":
                self.usageMessage()
            elif o == "-l":
                global logfile
                logfile = v
                if not os.path.exists(logfile):
                    raise IOError, ("File not found: %s" % logfile)
            elif o == "-s":
                global use_syslog
                use_syslog = 1

    def loadConfig(self):
        """Load configuration files into SharedConfigParser object."""
        # pre-load configuration files, cached by SharedConfigParser
        try:
            config = gmalib.SharedConfigParser()
            config.read(["/usr/local/etc/landiallerd.conf",
                         "/etc/landiallerd.conf", "landiallerd.conf"])
        except Exception, e:
            print "Terminating - error reading config file: %s" % e
            sys.exit()

    def main(self):
        """Start the XML-RPC server."""
        try:
            self.getopt()
            self.daemonise()
            cleaner = CleanerThread()
            cleaner.start()
        except IOError, e:
            sys.stderr.write("%s\n" % e)
        except getopt.GetoptError, e:
            sys.stderr.write("%s\n" % e)
            self.usageMessage()
        
        self.config = gmalib.SharedConfigParser()

        # start the server and start taking requests
        server_port = int(self.config.get("general", "port"))
        server = MyTCPServer(("", server_port), MyHandler)
        server.serve_forever()

    def usageMessage(self):
        """Print usage message to sys.stderr and exit."""
        message = """usage: %s [-d] [-f] [-h] [-l file] [-s]

Options:

    -d          enable debug messages
    -f          run in foreground instead of as a daemon
    -h		display this message on stderr
    -l file     write log messages to file
    -s          write log messages to syslog

""" % os.path.basename(sys.argv[0])
        sys.stderr.write(message)
        sys.exit(1)


if __name__ == "__main__":
    app = App()
    app.checkPlatform()
    app.loadConfig()

    debug = 0
    logfile = None
    use_syslog = 0

    app.main()
