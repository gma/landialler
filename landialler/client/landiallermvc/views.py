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

"""implements base classes for all GUI components

The landialler GUI is based around the Model-View-Controller design
pattern. It also supports multiple user interface toolkits. The
toolkit flexibility is achieved through the development of a separate
module of classes for each toolkit that defines how the windows and
dialogs should be displayed on screen.

landialler determines which toolkit module to use at run time. So that
the separate interfaces remain consistent (i.e. buttons have the same
names, windows have the same titles, etc.) the data required to draw
the interface is defined in a generic manner, in this module. All
toolkit modules inherit from this module, implementing the display of
the data defined in this module.

In other words, if you want to port landialler to Qt (and I hope
somebody does) you may treat the tkviews.py file as a reference
implementation, create qtviews.py, and all should be well.

"""


import controllers
import Observer


class View(Observer.Observer):

    """Abstract base class for an MVC View component.

    See [POSA125] for more information on the MVC
    (Model-View-Controller) pattern. All views that wish to be updated
    by changes to the Model should inherit from View.

    """
    
    def __init__(self, model):
        Observer.Observer.__init__(self, model)

    def draw(self):
        """Create and display the user interface (abstract method).

        All views should override this method if they need to be
        displayed on the screen.

        """
        raise NotImplementedError, \
              ("%s has not implemented draw()" % self.__class__)


class ButtonBar:

    """The beginnings of a button handler to simplify the creation and
    layout of groups of buttons. Incomplete and unused.

    """
    
    def __init__(self, model):
        View.__init__(self, model)
        self.buttons = []

    def add_button(self, text='Button', callback=None):
        self.buttons.append((text, callback))


class Window:
    """Contains basic logic for constructing a top level window.

    Needs updating to use the ButtonBar class.

    """
    
    def __init__(self):
        """Set button_side attribute to default to RIGHT."""
        self.button_store = {}  # maintain link to buttons so we config them
        self.button_bar = []
        #self.button_bar = ButtonBar()
        
    def create_button_store(self, parent=None):
        """Manipulates the buttons attribute, ready for drawing.

        A quick and dirty hack, to be replaced by the ButtonBar class.

        """        

        # We must sort the buttons into order specified by
        # self.buttons data structure (that's what the position
        # element in the tuple is for). Before we can sort them we
        # need to put them into a list.
        #
        # FIXME: There must be a better way of sorting a hash by it's
        # values than this, perhaps with a sub class of UserDict().

        for name in self.buttons.keys():
            position = self.buttons[name][0]
            callback = self.buttons[name][1]
            self.button_bar.append((name, position, callback))

        if len(self.button_bar) > 1:
            self.button_bar.sort(lambda a, b: cmp(b[1], a[1]))


class ConnectingDialog(View):

    """Display a message explaining that the server is connecting.

    The dialog has a Cancel button, allowing the user to cancel the
    connection request at any time. If the cancel button is pressed
    the application should exit (see cleanup() for how to handle
    this).

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
        """Destroy the dialog window (abstract method).

        Should be overriden in a sub class with GUI specific code for
        cleaning up the window after the cancel button has been
        pressed, or the dialog has been closed.

        """
        raise NotImplementedError, \
              ("%s has not implemented cleanup()" % self.__class__)


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
    active users and the model's is_connected attribute will be 0,
    whilst it's was_connected attribute will be 1. It is likely that
    either a) the connection has dropped out for some reason, or b)
    somebody else has hung up the connection.

    This dialog simply points that out to the user and closes when the
    user clicks OK. Note that it is a modal dialog.

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
        """Call the model.get_server_status() periodically (abstract method).

        The toolkit specific sub class should override this method to
        enable periodic status updates by calling the model's
        get_server_status() method every model.status_check_period
        milliseconds.

        """
        raise NotImplementedError, \
              ("%s has not implemented status_check()" % self.__class__)
