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

"""set up a connection on the landialler server"""


import ConfigParser
import gmalib
import os
import socket
import xmlrpclib


__version__ = "0.2pre1"


class Model:

    """The Model component of the Model-View-Controller pattern.

    See [POSA125] for more information.

    """

    def __init__(self, config, server):
        self.config = config  # ConfigParser object
        self.server = server  # connection to XML-RPC server
        self._observers = []  # observers are MVC views or controllers
        self.status_check_period = 5000  # msec between get_server_status()
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
        # determine which GUI toolkit to use
        # FIXME: Improve behaviour when no toolkit entry in config file
        # so that gtk can be the default on Unix. :)
        try:
            toolkit = self.config.get("interface", "toolkit")
        except ConfigParser.NoOptionError:
            toolkit = "tk"
        except ImportError:
            toolkit = tk
            
        exec("from landialler import %sviews" % toolkit)
        exec("self.toolkit = %sviews" % toolkit)

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
        if self.is_connected == 1 and self.was_connected == 0:
            self.was_connected = 1  # can now determine if connection dropped
        self.notify()
    
    def server_connect(self):
        """Instructs the server to start the dial up connection.

        Calls the XML-RPC API's connect() method. Returns 1 if the
        server reported that it's connect command exited successfully,
        0 otherwise.

        """
        rval = self.server.connect()
        if rval.value == xmlrpclib.True:
            return 1
        else:
            return 0

    def server_disconnect(self, all='no'):
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


class App(gmalib.Application):
    def __init__(self):
        """Calls the base class's initialisor."""
        gmalib.Application.__init__(self)

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

        # connect to XML-RPC server
        # (should this be in the model if we want to be able to pop up
        # dialog's with error messages in, rather than print
        # statements?)

        hostname = config.get("xmlrpcserver", "hostname")
        port = config.get("xmlrpcserver", "port")
        
        try:
            server = xmlrpclib.Server("http://%s:%s/" % (hostname, port))
            self.log_info("connected to %s:%s" % (hostname, port))
        except socket.error, e:
            self.log_err("Error %d: %s" % (e.args[0], e.args[1]))
            if e.args[0] == 111:  # connection refused
                print "Sorry, I couldn't connect to the " + \
                      "landialler server. Is it turned on?"
            else:
                print "%d: %s" % (e.args[0], e.args[1])

        # start the GUI
        model = Model(config, server)
        model.get_server_status()
        if not model.is_connected:
            dialog = model.toolkit.ConnectingDialog(model)
            dialog.draw()
            model.server_connect()
        window = model.toolkit.MainWindow(model)
        window.draw()  # starts event handling loop


if __name__ == '__main__':
    app = App()
    app.debug = 1
    app.main()
