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

        The controllers can observe the model if required, in which
        they should override this method.

        """
        pass


class ConnectingDialogController(Controller):
    def cancel_cb(self, cleanup_view):
        """Called when the Cancel button is pressed.

        The cleanup_view argument should be a function object that can
        be run to close down the toolkit's main window and cleanly
        exit the application.

        The XML-RPC API's server_disconnect() method is called, then
        the cleanup_view object is called. Note that this method is
        typically called when either the main window's close button or
        the Disconnect button are clicked.

        """
        self.model.server_disconnect()
        cleanup_view()


class DisconnectDialogController(Controller):
    def yes_cb(self, cleanup_view):
        """Called when the Yes button is pressed."""
        self.model.server_disconnect(all='yes')
        cleanup_view()
        
    def no_cb(self, cleanup_view):
        """Called when the No button is pressed."""
        self.model.server_disconnect(all='no')
        cleanup_view()


class DroppedDialogController(Controller):
    def ok_cb(self, cleanup_view):
        """Called when the OK button is pressed.

        Simply exits the application.

        """
        cleanup_view()
        

class MainWindowController(Controller):
    def disconnect_cb(self, cleanup_view):
        """Called when the Disconnect button is pressed.

        The cleanup_view argument should be a function object that can
        be run to close down the toolkit's main window and cleanly
        exit the application.

        The model's server_disconnect() method is called, then the
        cleanup_view object is called. Note that this method is
        typically called when either the main window's close button or
        the Disconnect button are clicked.

        """
        if self.model.current_users > 1:
            dialog = self.model.toolkit.DisconnectDialog(self.model)
            dialog.draw()
        else:
            self.model.server_disconnect()
        cleanup_view()
