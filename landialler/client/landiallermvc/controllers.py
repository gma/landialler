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


"""implements the MVC Controllers

landialler uses the Model-View-Controller design pattern to separate
the application logic from the presentation of the user interface. The
controllers are used to link the interface with the application data
and logic. For example, buttons in the GUI run controller methods when
they're clicked. The controllers are responsible for interfacing with
the application.

Each window or dialog (see the landialler.views module) has it's own
corresponding controller class which contains methods specific to that
view.

"""


class Controller:

    """Basic controller component."""
    
    def __init__(self, model, view):
        self.model = model
        # self.model.attach(self)  # observe the model
        self.view = view

##    def update(self):
##        """Called by the model's notify() method.

##        The controllers can observe the model if required, in which
##        they should override this method. They should also call their
##        model's attach() method, as this is currently done
##        automatically for controllers.

##        """
##        pass


class ConnectingDialogController(Controller):

    """Controller for the ConnectingDialog view class."""
    
    def cancel_cb(self, cleanup_view):
        """Called when the Cancel button is pressed.

        The XML-RPC API's server_disconnect() method is called, then
        the cleanup_view object is called. cleanup_view should be a
        function object that can be run to close down the toolkit's
        main window and cleanly exit the application.

        Note that this method is typically called when either the main
        window's close button or the Disconnect button are clicked.

        """
        self.model.server_disconnect()
        cleanup_view()


class DisconnectDialogController(Controller):

    """Controller for the DisconnectDialog view class."""
    
    def yes_cb(self, cleanup_view):
        """Called when the Yes button is pressed.

        The model's server_disconnect() method is called with the
        "all" argument set to "yes".

        The cleanup_view argument should be a GUI toolkit specific
        function object that can be run to close the dialog window, if
        required by the toolkit.

        """
        self.model.server_disconnect(all='yes')
        cleanup_view()
        
    def no_cb(self, cleanup_view):
        """Called when the No button is pressed.

        The model's server_disconnect() method is called with the
        "all" argument set to "yes".

        The cleanup_view argument should be a GUI toolkit specific
        function object that can be run to close the dialog window, if
        required by the toolkit.

        """
        self.model.server_disconnect(all='no')
        cleanup_view()


class DroppedDialogController(Controller):
    def ok_cb(self, cleanup_view):
        """Called when the OK button is pressed.

        Simply calls the cleanup_view function object, which should
        close the dialog and return control to the main window.

        """
        cleanup_view()
        

class MainWindowController(Controller):
    def disconnect_cb(self, cleanup_view):
        """Called when the Disconnect button is pressed.

        If there are other users a DisconnectDialog class is
        instantiated. Otherwise the model's server_disconnect() method
        is called.

        Either way, the cleanup_view function object is called, which
        should exit the application.

        Note that disconnect_cb() is also called when the window
        manager's close button is pressed.

        """
        if self.model.current_users > 1:
            dialog = self.model.toolkit.DisconnectDialog(self.model)
            dialog.draw()
        else:
            self.model.server_disconnect()
        cleanup_view()
