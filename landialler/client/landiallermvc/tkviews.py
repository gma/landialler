#!/usr/bin/env python
#
# tkviews.py - Tk interface for the landialler client
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


"""implements the Tk landialler user interface

Most classes in this file are undocumented, bacause they are simply Tk
specific sub classes of the classes in views.py that define the MVC
views. Where this is not the case they are present simply to aid the
Tk implementation, and are briefly documented to explain their
purpose.

"""


from Tkinter import *
import views


root = Tk()  # Instantiated here so that we can access it later, and we
             # don't get a spare top level window floating around.


class Window:

    """Contains basic logic for constructing a top level window."""
    
    def __init__(self):
        """Set button_side attribute to default to RIGHT."""
        self.button_side = RIGHT
        self.button_store = {}  # maintain link to buttons so we config them
        
    def draw_buttons(self, parent=None):

        """Lays out a set of buttons in a button bar.

        Packs the GUI buttons in order, aligned according to the
        button_side attribute.

        """        
        frame = Frame(parent, bd=6)  # padding frame
        self.buttons.reverse()
        for tuple in self.buttons:
            (name, cmd) = tuple
            button = Button(frame, text=name, command=cmd, state=NORMAL)
            button.pack(side=self.button_side)
            key = name.lower()
            self.button_store[key] = button
            print "button_store: %s" % self.button_store
        frame.pack(side=self.button_side)


class Dialog(Window):

    """Simple class for creating generic dialog boxes."""

    def __init__(self):
        """Set default button_side attribute to TOP."""
        Window.__init__(self)
        self.modal = 0
        self.button_side = TOP

    def show(self):
        """Displays the dialog's message and buttons."""
        win = Toplevel()
        win.title(self.title)
        frame = Frame(win, bd=6)
        label = Label(frame, text=self.text)
        label.pack()
        frame.pack()
        self.draw_buttons(win)
        if self.modal:
            win.focus_set()
            win.grab_set()
            win.wait_window()


class ConnectingDialog(Dialog, views.ConnectingDialog):
    def __init__(self, model):
        Dialog.__init__(self)
        views.ConnectingDialog.__init__(self, model)
    

class DisconnectDialog(Dialog, views.DisconnectDialog):
    def __init__(self, model):
        Dialog.__init__(self)
        views.DisconnectDialog.__init__(self, model)


class MainWindow(Window, views.MainWindow):
    def __init__(self, model):
        Window.__init__(self)
        views.MainWindow.__init__(self, model)
        self.default_var = []   # stores variable values (i.e. actual status)
        self.update_var = []  # StringVar() object's for auto label updating
        for row in self.status_rows:
            (label, value) = row
            self.default_var.append(value)
            self.update_var.append(StringVar())

    def draw_labels(self, parent=None):
        """Draws frame containing status display."""
        frame1 = Frame(parent, bd=6)                 # padding frame
        frame2 = Frame(frame1, bd=2, relief=GROOVE)  # layout frame

        row = 0
        for tuple in self.status_rows:
            (label, value) = tuple
            widget = Label(frame2, text=label)
            widget.grid(row=row, sticky=W, padx=2, pady=2)

            var = StringVar()
            var.set(self.default_var[row])
            self.update_var[row] = var
            widget = Label(frame2, textvariable=var)
            widget.grid(row=row, col=1, sticky=E, padx=2, pady=2)
            row += 1

        frame2.pack()
        frame1.pack()

    def show(self):
        """Display the main window."""
        global root
        root.title(self.title)
        self.draw_labels()
        self.draw_buttons()
        self.update()  # update labels immediately
        mainloop()

    def update(self):
        """Updates the status display."""
        if self.model.is_connected:
            self.update_var[0].set('Online')
            if self.button_store.has_key('disconnect'):
                self.button_store['disconnect'].config(state=ACTIVE)
        else:
            self.update_var[0].set('Offline')
            if self.button_store.has_key('disconnect'):
                self.button_store['disconnect'].config(state=DISABLED)
        self.update_var[1].set(self.model.current_users)
