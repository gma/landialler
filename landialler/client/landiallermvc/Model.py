# Model.py - the M in the MVC design pattern
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


import ConfigParser
import os
import xmlrpclib


class Model:

    """The Model component of landialler's MVC pattern design."""

    def __init__(self, config, server, toolkit):
        self.config = config  # ConfigParser object
        self.server = server  # connection to XML-RPC server
        self._observers = []  # observers are MVC views or controllers
        self.check_status_period = 5000  # msec between get_server_status()
        self.toolkit = toolkit # name of toolkit (lowercase), e.g. "tk"
        self.views = None     # name of toolkit support module (e.g. "tkviews")
        self.choose_gui_toolkit()
        
        # server status attributes (retrieved via RPC)
        self.is_connected = 0
        self.current_users = 0
        self.time_connected = 0
        
        # attributes for maintaining state
        self.was_connected = 0  # set to 1 if we have been online

    def attach(self, observer):
        """Attachs an observer to the publish-subscribe mechanism."""
        self._observers.append(observer)

    def detach(self, observer):
        """Detachs an observer from the publish-subscribe mechanism."""
        i = 0
        for obs in self._observers:
            if obs is observer:
                del self._observers[i]
            i += 1

    def choose_gui_toolkit(self):
        """Work out which GUI toolkit the View components should use.
        
        Imports the correct view module (e.g. tkviews) and makes
        self.toolkit an alias to the module.
        
        """
        if not self.toolkit:  # i.e. if not already set on command line
            try:
                self.toolkit = self.config.get("interface", "toolkit")
            except ConfigParser.Error:
                if os.name == "posix":
                    self.toolkit = "gtk"
                else:
                    self.toolkit = "tk"
        
        try:
            exec("import %sviews" % self.toolkit)
            exec("self.views = %sviews" % self.toolkit)
        except ImportError:
            exec("import %sviews" % "tk")
            exec("self.views = %sviews" % "tk")

    def notify(self):
        """Calls each observer's update() method."""
        for observer in self._observers:
            observer.update()

    def get_server_status(self):
        """Retrieves the status of the server's connection.
        
        Calls the XML-RPC API's get_status() method, then informs all
        observers by calling the notify() method.
        
        """
        (self.current_users, self.is_connected, self.time_connected) \
	    = self.server.get_status()
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
