#!/usr/bin/env python
# $Id$


"""landialler setup/install script

Usage: python setup.py install

"""


import distutils.core
import os
import shutil
import sys


def error_msg(message):
    print 'Error: %s' % message
    sys.exit(1)


if __name__ == '__main__':
    distutils.core.setup(name="landialler",
                         version="0.2",
                         description="LANdialler client",
                         author="Graham Ashton",
                         author_email="ashtong@users.sourceforge.net",
                         url="http://landialler.sourceforge.net/",
                         packages=['landiallermvc'])

    if sys.argv[1] <> 'install':
        sys.exit(0)   # Only continue if we're doing an "install"

    # Copy stuff into /usr/local if we're on a POSIX system.
    if os.name == 'posix':
        bin_dir = '/usr/local/bin'
        bin_file = 'landialler.py'
        conf_dir = '/usr/local/etc'
        conf_file = 'landialler.conf'

        # install landialler.py
        print 'copying %s to %s' % (bin_file, bin_dir)
        if (not os.path.exists(bin_dir)) or (not os.path.isdir(bin_dir)):
            error_msg('%s is not a directory' % bin_dir)
        shutil.copyfile(bin_file, '%s/%s' % (bin_dir, bin_file))
        os.chmod('%s/%s' % (bin_dir, bin_file), 0755)

        # install landialler.conf
        print 'copying %s to %s' % (conf_file, conf_dir)
        if (not os.path.exists(conf_dir)) or (not os.path.isdir(conf_dir)):
            error_msg('%s is not a directory' % conf_dir)
        shutil.copyfile(conf_file, '%s/%s' % (conf_dir, conf_file))
        os.chmod('%s/%s' % (conf_dir, conf_file), 0644)

    # Tell windows users to do it themselves.
    else:
        print """
Please copy landialler.py and landialler.conf into the same directory
(e.g. C:\Program Files\landialler on Windows). Edit the landialler.conf
file to point to your LANdialler server, and then run "python landialler.py"
from a command prompt.

If you would prefer to run LANdialler without the command prompt
window rename landialler.py to landialler.pyw and create a desktop
shortcut to run "python landialler.pyw" for you, but make sure that the 
shortcut starts in the landialler directory.
"""
