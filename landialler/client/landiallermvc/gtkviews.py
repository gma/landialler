#!/usr/bin/env python
#
# gtkviews.py - GTK+ interface for the landialler client
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


"""implements the GTK+ landialler user interface

Most classes in this file are Tk specific sub classes of those in
views.py that define the MVC views. Where this is not the case they
are present simply to aid the Tk implementation. Please see views.py
for more documentation, especially for many of the methods, whose
purpose is only documented in views.py.

"""


from gtk import *
import views


class Window:
    def __init__(self):
        self.window = None


class Dialog:
    def __init__(self):
        self.window = None

    def destroy_cb(self, *args):
        self.window.hide()
        mainquit()

    def draw(self):
        """Displays the dialog's message and buttons."""
        self.window = win = GtkWindow(WINDOW_DIALOG)
        win.connect('destroy', self.destroy_cb)
        win.set_border_width(8)
        win.set_title(self.title)
        self.draw_buttons()
        win.show()
        mainloop()

    def draw_buttons(self):
        button = GtkButton("Disconnect")
        button.connect("clicked", self.button_cb)
        self.window.add(button)
        button.show()


class ButtonBar:
    def __init__(self):
        self.buttons = []


class ConnectingDialog(Dialog, views.ConnectingDialog):
    def __init__(self, model):
        Dialog.__init__(self)
        views.ConnectingDialog.__init__(self, model)

    def button_cb(self, *args):
        print "button_cb ..."


class ConnectingButtonBar(ButtonBar):
    def __init__(self, model):
        pass


class DisconnectDialog(Dialog, views.DisconnectDialog):
    def __init__(self, model):
        Dialog.__init__(self)
        views.DisconnectDialog.__init__(self, model)


class MainWindow(views.MainWindow):
    def __init__(self, model):
        views.MainWindow.__init__(self, model)

    def cleanup(self):
        """Destroy the main window."""
        print "FIXME: call server_disonnect from cleanup()"

    def draw(self):
        """Display the main window."""
        pass

    def draw_labels(self):
        """Draws frame containing status display."""
        pass

    def draw_buttons(self):
        """Lays out a set of buttons in a button bar."""
        pass
