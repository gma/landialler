# views.py - abstract View class (see the MVC pattern)
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

"""implements a base classes for the MVC View"""


import controllers


class View:

    """Base class for an MVC View component.

    See [POSA125] for more information on the MVC
    (Model-View-Controller) pattern.

    """
    
    def __init__(self, model):
        """Register with the model's publish-subscribe mechanism."""
        self.model = model
        self.model.attach(self)  # observe the model

    def show(self):
        """Create and display the user interface (abstract method)."""
        raise NotImplementedError, \
              ("%s has not implemented show()" % self.__class__)

    def update(self):
        """Update the status data.

        A view is an observer of the model. This method is called
        automatically by the model's publish-subscribe system.

        """
        print "%s.update()" % self.__class__


class ConnectingDialog(View):

    """Display a message explaining that the server is connecting.

    The dialog also has a Cancel button, allowing the user to cancel
    the connection request at any time.

    """

    def __init__(self, model):
        View.__init__(self, model)
        self.controller = controllers.ConnectingDialogController(model, self)
        self.title = "Connecting..."
        self.text = "Please wait, connecting..."
        self.buttons = [("Cancel", self.controller.cancel_cb)]

    def cleanup(self):
        """Run by the controller when the Cancel button is pressed.

        Should contain GUI toolkit specific code for closing the
        dialog box.

        """
        pass
        

##    def update(self):
##        """Check to see if the server is connected."""
##        # will need to close window after timeout expires or we go online
##        pass


class DisconnectDialog(View):

    """Ask if all other users should also be disconnected.

    If there are multiple clients using the server's connection
    simultaneously then this dialog is displayed. Asks the user if
    all other users should also be disconnected (i.e. if the server
    should really disconnect, or just unregister this user).

    The dialog has Yes and No buttons. If the toolkit supports it the
    No button should be the default.

    """

    def __init__(self, model):
        View.__init__(self, model)
        self.controller = controllers.DisconnectDialogController(model, self)
        self.title = "Disconnect"
        self.text = "Disconnect all users?"
        self.buttons = [("Yes", self.controller.yes_cb),
                        ("No", self.controller.no_cb)]

    def cleanup(self):
        """Run by the controller when the Cancel button is pressed.

        Should contain GUI toolkit specific code for closing the
        dialog box.

        """
        pass


class MainWindow(View):

    """Displays the connection status and a disconnect button.

    Shows the user whether or not the server is connected, and if so
    how many users are currently registered with the server.

    There is also a disconnect button.

    """

    def __init__(self, model):
        View.__init__(self, model)
        self.controller = controllers.MainWindowController(model, self)
        self.title = "LANdialler"
        self.status_rows = [("Connection status:", "Offline"),
                            ("Current users:", 0)]
        self.buttons = [("Disconnect", self.controller.disconnect_cb)]

    def format_time(self, seconds):
        """Returns formatted string for displaying time spent online."""
        return "(0:00:00)"
