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


"""implements the GTK+ landialler user interface"""


import views


class Dialog(views.View):
    pass


class GoOnlineDialog(Dialog, views.GoOnLineDialog):
    pass


class ConnectingDialog(Dialog, views.ConnectingDialog):
    pass


class DisconnectDialog(Dialog, views.DisconnectDialog):
    pass


class MainWindow(views.MainWindow):
    pass
