#!/usr/bin/env python
#
# controllers.py - Controller compenents (see the MVC pattern)
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


"""implements the MVC Controllers"""


class Controller:

    """The Controller component of the Model-View-Controller pattern.

    See [POSA125] for more information on the MVC pattern.

    """
    
    def __init__(self, model, view):
        self.model = model
        # self.model.attach(self)  # observe the model
        self.view = view

    def update(self):
        """Called by the model's notify() method.

        The controllers don't currently need to observe the model,
        though may in the future. This method is included here for
        completeness/documentation purposes.

        """
        pass


class GoOnlineDialogController(Controller):
    def yes_cb(self):
        """Called when the Yes button is pressed."""
        print "GoOnlineDialogController.yes_cb called"
        self.model.server_connect()

    def no_cb(self):
        """Called when the No button is pressed."""
        print "GoOnlineDialogController.no_cb called"


class ConnectingDialogController(Controller):
    def cancel_cb(self):
        """Called when the Cancel button is pressed."""
        print "ConnectingDialogController.cancel_cb called"
        self.model.server_disconnect()


class DisconnectDialogController(Controller):
    def yes_cb(self):
        """Called when the Yes button is pressed."""
        print "DisconnectDialogController.yes_cb called"
        
    def no_cb(self):
        """Called when the No button is pressed."""
        print "DisconnectDialogController.no_cb called"


class MainWindowController(Controller):
    def disconnect_cb(self):
        """Called when the Disconnect button is pressed."""
        print "MainWindowController.disconnect_cb called"
