# __init__.py
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


import exceptions


__all__ = ["Model", "controllers", "views", "gtkviews", "tkviews"]


class ConnectError(exceptions.Exception):

    """Raised if the remote connect procedure fails."""
    
    def __init__(self, args=None):
        self.args = args


class DisconnectError(exceptions.Exception):

    """Raised if the remote disconnect procedure fails."""

    def __init__(self, args=None):
        self.args = args


class StatusError(exceptions.Exception):

    """Raised if the remote get_status procedure fails."""

    def __init__(self, args=None):
        self.args = args
