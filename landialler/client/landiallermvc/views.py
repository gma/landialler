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

    def draw(self):
        """Create and display the user interface (abstract method)."""
        raise NotImplementedError, \
              ("%s has not implemented draw()" % self.__class__)

    def update(self):
        """Update the status data.

        A view is an observer of the model. This method is called
        automatically by the model's publish-subscribe system. Views
        that want to do something when notified of changes should
        override this method, as it does nothing.

        """
        pass


class ConnectingDialog(View):

    """Display a message explaining that the server is connecting.

    The dialog also has a Cancel button, allowing the user to cancel
    the connection request at any time. If the cancel button is
    pressed the application should exit (see cleanup() for how to
    handle this).

    """

    def __init__(self, model):
        View.__init__(self, model)
        self.controller = controllers.ConnectingDialogController(model, self)
        self.title = "Connecting"
        self.text = "Please wait, connecting..."
        # we use lambda to pass parameters into the callback method
        callback = (lambda c=self.cleanup, s=self: s.controller.cancel_cb(c))
        # buttons = { name: (position in list, callback) }
        self.buttons = { 'cancel': (0, callback) }

    def cleanup(self):
        """Destroy the dialog window.

        GUI specific code for cleaning up the window after the cancel
        button has been pressed, or the dialog has been closed, should
        be put in this method. Override it in the sub class.

        """
        pass


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
        # we use lambda to pass parameters into the callback method
        yes_cb = (lambda c=self.cleanup, s=self: s.controller.yes_cb(c))
        no_cb = (lambda c=self.cleanup, s=self: s.controller.no_cb(c))
        # buttons = { name: (position in list, callback) }
        self.buttons = { 'yes': (0, yes_cb), 'no': (1, no_cb) }


class DroppedDialog(View):

    """Warn user that the connection has been dropped.

    If the connection has suddenly gone off line there will be 0
    active users and self.model.is_connected will be 0. It is likely
    that either a) the connection has dropped out for some reason, or
    b) somebody else has hung up the connection.

    This dialog simply points that out to the user and then quits the
    application when the user clicks OK.

    """

    def __init__(self, model):
        View.__init__(self, model)
        self.controller = controllers.DroppedDialogController(model, self)
        self.title = "Dropped"
        self.text = "Connection dropped (perhaps somebody hung up)"
        # we use lambda to pass parameters into the callback method
        callback = (lambda c=self.cleanup, s=self: s.controller.ok_cb(c))
        # buttons = { name: (position in list, callback) }
        self.buttons = { 'OK': (0, callback) }


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
        # we use lambda to pass parameters into the callback method
        callback = (lambda c=self.cleanup, s=self:
                    s.controller.disconnect_cb(c))
        # buttons = { name: (position in list, callback) }
        self.buttons = { 'disconnect': (0, callback) }

    def status_check(self):
        """Call the model.get_server_status() periodically.

        The toolkit specific sub class should override this method to
        enable periodic status updates.

        """
        print "FIXME: %s.status_check() is not written!!!" % self.__class__
