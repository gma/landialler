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

The author can be contacted at ashtong@users.sourceforge.net.

"""


__version__ = "0.2.1"


import getopt
import gmalib
import os
import posixpath
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


# The functions that follow whose names begin "api_" define the XML-RPC API.
#
# We maintain state via global variables:
#
#   current_users  -- the number of people sharing the connection
#   user_tracker   -- dict of clients and when they checked the status
#   is_connected   -- whether or not the server is connected
#   now_connecting -- whether or not another client has a connection pending


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
    global mutex, is_connected, now_connecting

    mutex.acquire()
    do_nothing1 = is_connected  # do_nothing vars just localise mutex code
    do_nothing2 = now_connecting
    mutex.release()
    
    if do_nothing1:
        return xmlrpclib.True   # already connected
    elif do_nothing2:
        return xmlrpclib.False  # another client began connecting, not up yet
    else:
        config = gmalib.SharedConfigParser()
        cmd = config.get("commands", "connect")
        rval = os.system("%s > /dev/null 2>&1" % cmd)

        if rval == 0:
            mutex.acquire()
            now_connecting = 1
            mutex.release()
            print "connect command run successfully"
            return xmlrpclib.True
        else:
            sys.stderr.write("connect command failed (%s)\n" % rval)
            return xmlrpclib.False


def api_disconnect(all="no", client=None):
    """Close the connection.

    If there are other users online and the all argument is not set
    then the XML-RPC True value is returned.

    Otherwise the connection is dropped by running an external dial up
    termination script. As with api_connect(), the return value of the
    external script is converted into the XML-RPC True or False value,
    and returned.

    The client argument should uniquely identify the client, and
    should be usable as a dictionary key.

    """
    global mutex, current_users, is_connected, now_connecting, user_tracker
    
    if (current_users > 1) and (all <> "yes"):  # other users still online
        del user_tracker[client]
        return xmlrpclib.True

    else:
        config = gmalib.SharedConfigParser()
        cmd = config.get("commands", "disconnect")
        rval = os.system("%s > /dev/null 2>&1" % cmd)
        if rval == 0:
            mutex.acquire()
            is_connected = 0
            now_connecting = 0
            user_tracker.clear()
            mutex.release()
            print "disconnect command run successfully"
            return xmlrpclib.True
        else:
            sys.stderr.write("disconnect command failed (%s)\n" % rval)
            return xmlrpclib.False


def api_get_status(client):
    """Return current_users and is_connected.

    The client parameter should uniquely identify the client, and
    should be usable as a dictionary key. The IP address is usually
    used.

    The two values returned are:

    current_users -- The number of users sharing the connection
    is_connected  -- 1 if connected, 0 otherwise

    """
    global mutex, is_connected, now_connecting, user_tracker

    mutex.acquire()

    # register client's connection
    user_tracker[client] = time.time()

    # get dummy_current_users and is_connected
    is_connected = check_connection_status()
    if is_connected:
        now_connecting = 0
        dummy_current_users = len(user_tracker.keys())
    else:
        dummy_current_users = 0

    mutex.release()

    return (dummy_current_users, is_connected)
    

def check_connection_status():
    """Run the external is_connected command.

    Returns 1 if the external command runs successfully, 0 otherwise.

    """
    global mutex, is_connected, now_connecting
    
    config = gmalib.SharedConfigParser()
    cmd = config.get("commands", "is_connected")
    rval = os.system("%s > /dev/null 2>&1" % cmd)

    mutex.acquire()
    if rval == 0:
        is_connected = 1
        now_connecting = 0
    else:
        is_connected = 0
    mutex.release()

    return is_connected


def count_users():
    """Counts the number of currently active clients.

    Returns the number of clients that have run the API's get_status()
    procedure in the last 30 seconds.
    
    """
    global mutex, is_connected, user_tracker

    mutex.acquire()
    timeout = 30  # number of seconds before client deemed to be dead
    for client in user_tracker.keys():
        if (time.time() - user_tracker[client]) > timeout:
            del user_tracker[client]
    num_users = len(user_tracker.keys())
    mutex.release()

    return num_users


class CleanerThread(threading.Thread, gmalib.Logger):

    """Ensures that the connection does not remain live with no clients.

    If a client is not shut down cleanly it may not be able to call
    the API's disconnect procedure, thereby leaving the connection
    open when there are no clients left. This is bad, as it could lead
    to an expensive telephone bill.

    This thread periodically makes sure that the current_users
    variable is correctly set by determining how many clients have
    connected in the last 30 seconds. If current_users is false but
    is_connected is true, the API's disconnect method is called.

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

        global mutex, debug, logfile, use_syslog
        mutex.acquire()
        self.debug = debug
        gmalib.Logger.__init__(self, logfile=logfile, use_syslog=use_syslog)
        mutex.release()

    def run(self):
        # See http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/65222
        # for a full example of the while loop's timer code.
    
        global mutex, current_users, is_connected, now_connecting, user_tracker

        while 1:
            mutex.acquire()

            current_users = count_users()
            is_connected = check_connection_status()
            self.log_debug("CleanerThread: users=%s, connected=%s" %
                           (current_users, is_connected))
            if (current_users < 1) and (now_connecting or is_connected):
                self.log_debug("CleanerThread: disconnecting")
                api_disconnect(all="yes")

            mutex.release()
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
        global mutex, debug, logfile, use_syslog
        mutex.acquire()
        self.debug = debug
        gmalib.Logger.__init__(self, logfile=logfile, use_syslog=use_syslog)
        mutex.release()

        # FIXME: iterate through all base class' __init__ methods so that
        #        class hierarchy can change without us worrying about it.
        SocketServer.BaseRequestHandler.__init__(self, *args, **kwargs)

    def call(self, method, params):
        """Call an API procedure, return it's result.

        Calls one of the methods whose name begins with "api_". For
        example, if method is set to "a_method" then the
        "api_a_method" will be called. If the method doesn't exist
        then an AttributeError is raised, returning a XML-RPC fault to
        the client.

        """
        my_api = ["connect", "disconnect", "get_status"]
        if not method in my_api:
            self.log_err("Unknown method name: %s" % method)
            raise xmlrpclib.Fault, "Unknown method name"
        else:
            if method == "get_status":
                (host, port) = self.client_address
                params = (host,)
            elif method == "disconnect":
                (host, port) = self.client_address
                params = (params[0], host)
            self.log_debug("called %s(%s)" % \
                           (method, ", ".join(map(repr, params))))
            return apply(eval("api_" + method), params)

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
        self.run_as_daemon = 1

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

        global mutex
        mutex.acquire()

        for o, v in opts:
            if o == "-d":
                global debug
                debug = self.debug = 1
            elif o == "-f":
                self.run_as_daemon = 0
            elif o == "-h":
                self.usage_message()
            elif o == "-l":
                global logfile
                logfile = v
                if not os.path.exists(logfile):
                    raise IOError, ("File not found: %s" % logfile)
            elif o == "-s":
                global use_syslog
                use_syslog = 1

        mutex.release()

    def main(self):
        """Start the XML-RPC server."""
        try:
            self.getopt()
            if self.run_as_daemon:
                self.daemonise()
            cleaner = CleanerThread()
            cleaner.start()
        except IOError, e:
            sys.stderr.write("%s\n" % e)
        except getopt.GetoptError, e:
            sys.stderr.write("%s\n" % e)
            self.usage_message()
        
        self.config = gmalib.SharedConfigParser()  # pre-cached

        # start the server and start taking requests
        server_port = int(self.config.get("general", "port"))
        self.server = MyTCPServer(("", server_port), MyHandler)
        self.server.serve_forever()

    def usage_message(self):
        """Print usage message to sys.stderr and exit."""
        message = """usage: %s [-d] [-f] [-h] [-l file] [-s]

Options:

    -d          enable debug messages
    -f          run in foreground instead of as a daemon
    -h		display this message on stderr
    -l file     write log messages to file
    -s          write log messages to syslog

""" % posixpath.basename(sys.argv[0])
        sys.stderr.write(message)
        sys.exit(1)


if __name__ == "__main__":
    if os.name != "posix":
        print "Sorry, only POSIX compliant systems are currently supported."
        sys.exit()

    # pre-load configuration files, cached by SharedConfigParser
    try:
        config = gmalib.SharedConfigParser()
        config.read(["/usr/local/etc/landiallerd.conf",
                     "/etc/landiallerd.conf", "landiallerd.conf"])
    except Exception, e:
        print "Terminating - error reading config file: %s" % e
        sys.exit()

    # global variables for maintaining consistent logging across classes
    debug = 0
    logfile = None
    use_syslog = 0

    # global variables for maintaining state
    mutex = threading.RLock()  # control access to the following globals
    user_tracker = {}  # dict of all users' IP/port numbers
    current_users = 0  # number of users online (determined from user_tracker)
    is_connected = 0   # is the connection currently up?
    now_connecting = 0 # is the connection in the process of coming up?
    
    app = App()
    app.main()
