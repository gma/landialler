#!/usr/bin/env python
#
# landiallerd.py - the LANdialler daemon
#
# Copyright (C) 2001-2004 Graham Ashton
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


"""serves LANdialler clients, manages connections

LANdialler enables several computers on a home LAN to remotely control
a dial up device (e.g. modem) that is connected to a single Unix
workstation. This scenario is explained in more detail on the
LANdialler web site.

There are two programs that make up a complete LANdialler system; the
client (landialler.py) and the server (landiallerd.py). You're reading
the documentation for the server that runs on the Unix workstation.

The client and server communicate via XML-RPC. The server runs in the
background (as a daemon) waiting for clients to connect to it and
request an Internet connection (through the LANdialler XML-RPC API).
By default the server listen for connections on port 6543.

The client/server API defines three procedures that the client can
call; connect(), disconnect() and get_status(). These are individually
documented below. Each procedure runs an external script/program to
perform their task, making the server more portable between different
versions of Unix, or distributions of Linux. Each command should
return immediately and exit with a non zero return code if there is an
error. Commands are specified in the [commands] section of the
landiallerd.conf configuration file.

A sample configuration file should be included with the package, but
the following should serve as a good example:

  [commands]
  connect: /usr/local/bin/start-connection
  disconnet: /usr/local/bin/stop-connection
  is_connected: /sbin/ifconfig ppp0 | grep "inet addr" >/dev/null

  [server]
  port: 6543

Note that you can also configure the TCP port number that landiallerd.py
uses to talk to the clients.

The connect and disconnect scripts referenced in the config file
should both make sure that they exit immediately; the connect command
MUST NOT block before the connection has been made, but should only
check that the commands that it has run have started correctly (errors
should be indicated with a non zero exit code). If you know how to
integrate LANdialler cleanly with your own operating system's dial up
systems then please send suggestions in and they will be made
available on the web site (with credits).

To see a list of the available command line options, use the -h
switch. For example, error, informational and debugging messages can
be written to the syslog if the -s switch is used, or to a separate
log file if -l is used.

More information on LANdialler is available at the project home page:

  http://landialler.sourceforge.net/

The author can be contacted at ashtong@users.sourceforge.net.

"""


__version__ = "0.2.1"


# import ConfigParser
# import getopt
import os
# import SimpleXMLRPCServer
# import SocketServer
# import sys
# import threading
import time
import xmlrpclib


class Timer:

    """Simple timer class to record elapsed times."""

    def __init__(self):
        """Run the start() method."""
        self._start_time = None  # seconds since epoch
        self._stop_time = None
        self.reset()
        self.is_running = False

    def start(self):
        """Start the timer."""
        self._start_time = time.time()
        self.is_running = True

    def stop(self):
        """Stop the timer."""
        self._stop_time = time.time()
        self.is_running = False

    def reset(self):
        """Reset the timer to zero.

        Note that reset() neither stops or starts the timer.

        """
        self._start_time = time.time()
        self._stop_time = time.time()

    def _get_elapsed_seconds(self):
        """Return seconds since timer started."""
        if self.is_running:
            return int('%.0f' % (time.time() - self._start_time))
        else:
            return int('%.0f' % (self._stop_time - self._start_time))

    elapsed_seconds = property(_get_elapsed_seconds)


class Modem:

    def __init__(self, config_parser):
        self._config_parser = config_parser
        self.timer = Timer()

    def dial(self):
        self.timer.reset()
        command = self._config_parser.get('commands', 'connect')
        return os.system(command) == 0

    def hang_up(self):
        self.timer.stop()
        command = self._config_parser.get('commands', 'disconnect')
        return os.system(command) == 0

    def is_connected(self):
        if not self.timer.is_running:
            self.timer.start()
        command = self._config_parser.get('commands', 'is_connected')
        return os.system(command) == 0


class ModemProxy:

    CLIENT_TIMEOUT = 30

    def __init__(self, modem):
        self._modem = modem
        self._clients = {}
        self._is_dialling = False  # TODO: remove/sort this attribute out

    def _add_client(self, client_id):
        if client_id not in self._clients:
            self._clients[client_id] = time.time()

    def refresh_client(self, client_id):
        self._clients[client_id] = time.time()

    def remove_old_clients(self):
        for client_id, time_last_seen in self._clients.items():
            if (time.time() - time_last_seen) > self.CLIENT_TIMEOUT:
                self.hang_up(client_id)

    def count_clients(self):
        return len(self._clients.keys())

    def dial(self, client_id):
        self._add_client(client_id)
        if self.is_connected() or self._is_dialling:
            return True
        else:
            self._is_dialling = True
            return self._modem.dial()

    def hang_up(self, client_id, all=False):
        if client_id in self._clients:
            del self._clients[client_id]
        if self.is_connected() and (all or not self._clients):
            return self._modem.hang_up()
        else:
            return True

    def is_connected(self):
        return self._modem.is_connected()

    def get_time_connected(self):
        return self._modem.timer.elapsed_seconds


class API:
    
    """Implements the LANdialler API.

    All accessible methods in this class form a part of the LANdialler
    XML-RPC API, and are called directly whenever a client makes an
    HTTP request to the server.

    """

    def __init__(self, modem_proxy):
        self._modem_proxy = modem_proxy

    def connect(self, client_id):
        """Open the connection.

        The client parameter should be a hashable (e.g. string) that
        uniquely identifies the client (e.g. the IP address).

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
        return self._modem_proxy.dial(client_id)

    def disconnect(self, client_id, all=xmlrpclib.False):
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
        if self._modem_proxy.is_connected():
            return self._modem_proxy.hang_up(client_id, bool(all))
        else:
            return True
                
    def get_status(self, client_id):
        """Returns the number of clients and connection status.

        The client parameter should uniquely identify the client, and
        should be usable as a dictionary key. The IP address is
        usually used.

        The values returned are:

        current_clients -- The number of users sharing the connection
        is_connected    -- 1 if connected, 0 otherwise
        time_connected  -- Number of seconds connected

        """
        self._modem_proxy.refresh_client(client_id)
        return (self._modem_proxy.count_clients(),
                self._modem_proxy.is_connected(),
                self._modem_proxy.get_time_connected())
    

# class CleanerThread(threading.Thread):

#     """Ensures that the connection does not remain live with no clients."""

#     def __init__(self, modem, interval=10):
#         """Setup the thread object."""
#         threading.Thread.__init__(self, name=CleanerThread)
#         self._modem = modem
#         self._pause_interval = interval
#         self._pauser = threading.Event()
#         self.setDaemon(True)

#     def run(self):
#         # See http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/65222
#         # for a full example of the while loop's timer code.
#         while 1:
#             self._modem.forget_old_clients()
#             if self._modem.count_clients() < 1:
#                 if self._modem.is_connecting or self._modem.is_connected:
#                     log.info("clients timed out, terminating connection")
#                     api = API(self._modem)
#                     api.disconnect(all="yes")

#             self._pauser.wait(self._pause_interval)


# class ReusableTCPServer(SocketServer.TCPServer):

#     """We override TCPServer so that we can set the allow_reuse_socket
#     attribute to true (so we can restart immediately and the TCP
#     socket doesn't sit in the CLOSE_WAIT state instead).

#     """
    
#     def __init__(self, server_address, request_handler_class):
#         self.allow_reuse_address = 1
#         SocketServer.TCPServer.__init__(self, server_address,
#                                         request_handler_class)


# class RequestHandler(SimpleXMLRPCServer.SimpleXMLRPCRequestHandler):

#     """Handles XML-RPC requests."""

#     def __init__(self, modem):
#         SimpleXMLRPCServer.SimpleXMLRPCRequestHandler.__init__(self)
#         self._modem = modem

#     def call(self, procedure, params):
#         """Call an API procedure, return it's result.

#         Calls one of the API's methods on an instance of the API
#         class. If the procedure isn't supported then an AttributeError
#         is raised, returning a XML-RPC fault to the client.

#         """
#         if not procedure in ["connect", "disconnect", "get_status"]:
#             log.err("Unknown procedure name: %s" % procedure)
#             raise xmlrpclib.Fault, "Unknown procedure name: %s" % procedure
#         else:
#             api = API(self._modem)
#             method = getattr(api, procedure)
#             if procedure in ["connect", "get_status"]:
#                 (host, port) = self.client_address
#                 params = (host,)
#             elif procedure == "disconnect":
#                 (host, port) = self.client_address
#                 disconnect_all_users = params[0]
#                 params = (disconnect_all_users, host)
#             log.debug("RequestHandler.call(): called %s(%s)" % \
#                       (procedure, ", ".join(map(repr, params))))
#             return apply(method, params)


# class App:

#     """A simple wrapper class that initialises and runs the server."""

#     def __init__(self):
#         self._become_daemon = True
#         self._config = self._load_config_file()
#         self._modem = SharedModem(self._config)

#     def _load_config_file(self):
#         try:
#             config = ConfigParser.ConfigParser()
#             config.read(["/usr/local/etc/landiallerd.conf",
#                          "/etc/landiallerd.conf", "landiallerd.conf"])
#         except Exception, e:
#             print "Terminating - error reading config file: %s" % e
#             sys.exit()

#     def check_platform(self):
#         if os.name != "posix":
#             print "Sorry, only POSIX compliant systems are supported."
#             sys.exit()

#     def daemonise(self):
#         """Become a daemon process (POSIX only)."""
#         if not self._become_daemon:
#             return
#         if os.name != "posix":
#             print "unable to run as a daemon (POSIX only)"
#             return None

#         # See "Python Standard Library", pg. 29, O'Reilly, for more
#         # info on the following.
#         pid = os.fork()
#         if pid:  # we're the parent if pid is set
#             os._exit(0)

#         os.setpgrp()
#         os.umask(0)

#         class DevNull:

#             def write(self, message):
#                 pass
            
#         sys.stdin.close()
#         sys.stdout = DevNull()
#         sys.stderr = DevNull()

#     def getopt(self):
#         """Parse command line arguments.

#         Reads the command line arguments, looking for the following:

#         -d          enable debugging for extra output
#         -f          run in the foreground (not as a daemon)
#         -h          print usage message to stderr
#         -l file     log events to file
#         -s          log events to syslog

#         """
#         opts, args = getopt.getopt(sys.argv[1:], "dfhl:s")

#         for o, v in opts:
#             if o == "-d":
#                 # TODO: set debug level on the logging object
#                 pass
#             elif o == "-f":
#                 self._become_daemon = False
#             elif o == "-h":
#                 self.usage_message()
#             elif o == "-l":
#                 global log_file
#                 log_file = v
#                 if not os.path.exists(log_file):
#                     raise IOError, ("File not found: %s" % log_file)
#             elif o == "-s":
#                 global use_syslog
#                 use_syslog = 1

#     def main(self):
#         """Start the XML-RPC server."""
#         self.check_platform()
#         self.pre_load_config()
#         try:
#             log.info("starting up")
#             self.getopt()
#             self.daemonise()
#             cleaner = CleanerThread(self._modem)
#             cleaner.start()
#         except IOError, e:
#             sys.stderr.write("%s\n" % e)
#         except getopt.GetoptError, e:
#             sys.stderr.write("%s\n" % e)
#             self.usage_message()
        
#         # start the server and start taking requests
#         server_port = int(self.config.get("general", "port"))

#         def handler_factory():
#             return RequestHandler(self._modem)

#         server = ReusableTCPServer(("", server_port), handler_factory, False)
#         try:
#             server.serve_forever()
#         except KeyboardInterrupt:
#             print "Caught Ctrl-C, shutting down."

#     def usage_message(self):
#         """Print usage message to sys.stderr and exit."""
#         message = """usage: %s [-d] [-f] [-h] [-l file] [-s]

# Options:

#     -d          enable debug messages
#     -f          run in foreground instead of as a daemon
#     -h		display this message on stderr
#     -l file     write log messages to file
#     -s          write log messages to syslog

# """ % os.path.basename(sys.argv[0])
#         sys.stderr.write(message)
#         sys.exit(1)
    

if __name__ == "__main__":
    app = App()
    app.main()
