#!/usr/bin/env python
#
# landialler.py - the landialler client
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

"""set up a shared network connection (via the server)

LANdialler enables several computers on a home LAN to remotely control
a dial up device (e.g. modem) that is connected to a single Unix
workstation. This scenario is explained in more detail on the
LANdialler web site.

There are two programs that make up a complete LANdialler system; the
client (landialler) and the server (landiallerd). This program is the
client.

When you run landialler it contacts the server and determines if it is
currently connected (e.g. dialled up). If so, the user is informed
that they are currently online. Otherwise the client asks the server
to connect, displaying confirmation to the user that the server is
connecting.

Once the server reports that the connection is made, the client
displays the number of users currently using the connection. The user
has the option to disconnect at any time. If there are other users
online then the user has the option to simply unregister themselves
(thereby allowing the server to disconnect when all users have
unregistered), or to actually terminate the connection, disconnecting
all other users at the same time.

If the connection drops out at any time (let's face it, it can happen
a lot with modems) a dialog box pops up alerting the user, after which
landialler exits (at some point in the future there will be an option
for the user to attempt to reconnect instead).

All client-server communication takes place via the LANdialler XML-RPC
API, which is covered in landiallerd's documentation.

The configuration file tells landialler how to contact the server. A
sample configuration file looks like this:

  [xmlrpcserver]
  hostname: 192.168.1.1  # your Unix box
  port: 6543             # the default port

  [dialup]
  timeout: 120           # not currently used

The configuration file should be called "landialler.conf". On POSIX
operating systems (e.g. Unix or similar) it can either be placed in
/usr/local/etc, or the current directory. On other operating systems
it must be placed in the current directory.

On POSIX operating systems, error, informational and debugging
messages are written to the syslog.

More information on landialler is available at the project home page:

  http://landialler.sourceforge.net/

The author can be contacted at ashtong@users.sourceforge.net.

"""

# For more information on the Model-View-Controller design pattern,
# see http://www.ootips.org/mvc-pattern.html


import exceptions
import ConfigParser
import gmalib
import os
import socket
import xmlrpclib


__version__ = "0.2pre2"


class ConnectError(exceptions.Exception):

    """Raised if the remote connect procedure fails."""
    
    def __init__(self, args=None):
        self.args = args


class DisconnectError(exceptions.Exception):

    """Raised if the remote disconnect procedure fails."""

    def __init__(self, args=None):
        self.args = args


class StatusError(exceptions.Exception):

    """Raised if the remote get_status procedure fails."""

    def __init__(self, args=None):
        self.args = args


class Model:

    """The Model component of the Model-View-Controller pattern.

    See [POSA125] for more information.

    """

    def __init__(self, config, server):
        self.config = config  # ConfigParser object
        self.server = server  # connection to XML-RPC server
        self._observers = []  # observers are MVC views or controllers
        self.check_status_period = 5000  # msec between get_server_status()
        self.toolkit = None   # toolkit specific view library
        self.choose_gui_toolkit()

        # server status attributes (retrieved via RPC)
        self.is_connected = 0
        self.current_users = 0

        # attributes for maintaining state
        self.was_connected = 0  # set to 1 if we have been online

    def attach(self, observer):
        """Attachs an observer to the publish-subscribe mechanism."""
        self._observers.append(observer)

    def detach(self, observer):
        """Detachs an observer from the publish-subscribe mechanism."""
        for observer in self._observers:
            if observer is observer:
                self._observers.remove[observer]

    def choose_gui_toolkit(self):
        """Work out which GUI toolkit the View components should use.

        Imports the correct view module (e.g. tkviews) and makes
        self.toolkit an alias to the module.

        """
        try:
            toolkit = self.config.get("interface", "toolkit")
        except ConfigParser.Error:
            if os.name == "posix":
                toolkit = "gtk"
            else:
                toolkit = "tk"

        try:
            exec("from landiallermvc import %sviews" % toolkit)
            exec("self.toolkit = %sviews" % toolkit)
        except ImportError:
            exec("from landiallermvc import %sviews" % "tk")
            exec("self.toolkit = %sviews" % "tk")

    def notify(self):
        """Calls each observer's update() method."""
        for observer in self._observers:
            observer.update()

    def get_server_status(self):
        """Retrieves the status of the server's connection.

        Calls the XML-RPC API's get_status() method, then informs all
        observers by calling the notify() method.
        
        """
        (self.current_users, self.is_connected) = self.server.get_status()
        self.notify()
        if self.is_connected == 1 and self.was_connected == 0:
            self.was_connected = 1  # can now determine if connection dropped
    
    def server_connect(self):
        """Instructs the server to start the dial up connection.

        Calls the XML-RPC API's connect() method. Raises a
        ConnectError exception if the connect() method returns false.

        """
        rval = self.server.connect()
        if rval.value == xmlrpclib.False:
            raise ConnectError

    def server_disconnect(self, all="no"):
        """Instructs the server to disconnect the dial up connection.

        Calls the XML-RPC API's disconnect() method. Returns 1 if the
        server reported that it's disconnect command exited successfully,
        0 otherwise.

        """
        rval = self.server.disconnect(all)
        if rval.value == xmlrpclib.True:
            return 1
        else:
            return 0


class App(gmalib.Logger):
    def __init__(self):
        """Calls the base class's initialisor."""
        gmalib.Logger.__init__(self, use_syslog=0)

    def main(self):
        """The main method, runs the application.

        Begins by reading the landialler.conf configuration file. Then
        connects to the XML-RPC server (as specified in the config
        file).

        Initialises and launches the user interface.

        """
        # load config file
        config = ConfigParser.ConfigParser()
        files = []
        if os.name == "posix":
            files.append("/usr/local/etc/landialler.conf")
        files.append("landialler.conf")
        config.read(files)

        # run the core of the application
        hostname = config.get("xmlrpcserver", "hostname")
        port = config.get("xmlrpcserver", "port")
        
        server = xmlrpclib.Server("http://%s:%s/" % (hostname, port))
        self.log_debug("connected to %s:%s" % (hostname, port))
        self.model = Model(config, server)
        window = self.model.toolkit.MainWindow(self.model)
        window.draw()

        try:
            self.model.get_server_status()
            if not self.model.is_connected:
                dialog = self.model.toolkit.ConnectingDialog(self.model)
                dialog.draw()
                self.model.server_connect()
            window.start_event_loop()

        except ConnectError:
            self.handle_connect_error()
        except DisconnectError:
            self.handle_disconnect_error()
        except StatusError:
            self.handle_status_error()
        except socket.error, e:
            self.handle_socket_error(e)
        except Exception, e:
            self.handle_error(e)

    def handle_connect_error(self):
        self.log_err("Error: ConnectError")
        title = "Connect error"
        msg = "There was a problem\nconnecting to the network."
        dialog = self.model.toolkit.FatalErrorDialog(self.model, title=title,
                                                message=msg)
        dialog.draw()
        dialog.start_event_loop()

    def handle_disconnect_error(self):
        self.log_err("Error: DisconnectError")
        title = "Disconnect error"
        msg = "There was a problem disconnecting\nfrom the network. " + \
            "You may not have\nbeen disconnected properly!"
        dialog = self.model.toolkit.FatalErrorDialog(self.model, title=title, 
                                                message=msg)
        dialog.draw()
        dialog.start_event_loop()

    def handle_socket_error(self, e):
        self.log_err("Error: socket error")
        msg = "Socket error: %s (%d)" % (e.args[1], int(e.args[0]))
        self.log_err(msg)
        dialog = self.model.toolkit.FatalErrorDialog(self.model, message=msg)
        dialog.draw()
        dialog.start_event_loop()

    def handle_status_error(self):
        self.log_err("Error: StatusError")
        title = "Error"
        msg = "LANdialler is unable to determine the\nstatus of your " + \
            "network connection.\n\nPlease check the connection and\n" + \
            "the server and try again."
        dialog = self.model.toolkit.FatalErrorDialog(self.model, title=title, 
                                                message=msg)
        dialog.draw()
        dialog.start_event_loop()

    def handle_error(self, e):
        self.log_err("Error: %s" % e)
        title = "Error"
        msg = "Error: %s" % e
        dialog = self.model.toolkit.FatalErrorDialog(self.model, title=title, 
                                                message=msg)
        dialog.draw()
        dialog.start_event_loop()


if __name__ == "__main__":
    app = App()
    app.debug = 1
    app.main()
