#!/usr/bin/env python
#
# TkViews.py - GTK+ interface for the landialler client
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


"""implements the Tk landialler user interface"""


from Tkinter import *
import Views


root = Tk()
root.withdraw()


class TkDialog:
    def __init__(self):
        self.modal = 1

    def show(self):
        win = Toplevel()
        label = Label(win, text=self.text)
        label.pack()
        for (name, callback) in self.buttons:
            button = Button(win, text=name, command=callback)
            button.pack()
        if self.modal:
            win.focus_set()
            win.grab_set()
            win.wait_window()


class TkGoOnlineDialog(Views.GoOnlineDialog, TkDialog):
    pass


class TkConnectingDialog(Views.ConnectingDialog, TkDialog):
    pass
    

class TkDisconnectDialog(Views.DisconnectDialog, TkDialog):
    pass


class TkMainWindow(Views.MainWindow):
    pass
