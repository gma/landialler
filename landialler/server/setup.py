#!/usr/bin/env python
#
# setup.py - landialler setup/install script
#
# Usage: python setup.py install
#
# $Id$

import os, shutil

# Change these variables to comply with your system if you're not
# happy with the default settings. They should work fine on most
# Unices, and Linux.

bin_dir = '/usr/local/sbin'
bin_file = 'landiallerd.py'
conf_dir = '/usr/local/etc'
conf_file = 'landiallerd.conf'

def error_msg(message):
    global bin_file, bin_dir
    print 'Error: ', message
    print 'Please edit setup.py and try again.'


if __name__ == '__main__':
    if not os.name == 'posix':
        error_msg('only POSIX systems are supported')
    if not os.path.exists(bin_dir):
        error_msg('%s does not exist' % bin_dir)
    if not os.path.exists(conf_dir):
        error_msg('%s does not exist' % conf_dir)
    if not os.path.isdir(bin_dir):
        error_msg('%s is not a directory' % bin_dir)
    if not os.path.isdir(conf_dir):
        error_msg('%s is not a directory' % conf_dir)
    print "copying %s to %s/%s" % (bin_file, bin_dir, bin_file)
    shutil.copyfile(bin_file, "%s/%s" % (bin_dir, bin_file))
    os.chmod('%s/%s' % (bin_dir, bin_file), 0755)
    print "copying %s to %s/%s" % (conf_file, conf_dir, conf_file)
    shutil.copyfile(conf_file, "%s/%s" % (conf_dir, conf_file))
    os.chmod('%s/%s' % (conf_dir, conf_file), 0644)
