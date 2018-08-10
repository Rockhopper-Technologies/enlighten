# Copyright 2018 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Example FTP downloader
"""

import ftplib
import os

import enlighten


SITE = 'test.rebex.net'
USER = 'demo'
PASSWD = 'password'
DIR = 'pub/example'
DEST = '/tmp'
DEBUG = 0  # 0, 1, 2 are valid
MANAGER = enlighten.get_manager()


class Writer(object):
    """
    Context manager for handling download writes
    """

    def __init__(self, filename, size, directory=None):
        self.filename = filename
        self.size = size
        if directory:
            self.dest = os.path.join(directory, filename)
        else:
            self.dest = filename
        self.status = self.fileobj = None

    def __enter__(self):
        self.status = MANAGER.counter(total=self.size, desc=self.filename,
                                      unit='bytes', leave=False)
        self.fileobj = open(self.dest, 'wb')
        return self

    def __exit__(self, *args):
        self.fileobj.close()
        self.status.close()

    def write(self, block):
        """
        Write to local file and update progress bar
        """
        self.fileobj.write(block)
        self.status.update(len(block))


def download():
    """
    Download all files from an FTP share
    """

    ftp = ftplib.FTP(SITE)
    ftp.set_debuglevel(DEBUG)
    ftp.login(USER, PASSWD)
    ftp.cwd(DIR)
    filelist = ftp.nlst()
    filecounter = MANAGER.counter(total=len(filelist), desc='Downloading',
                                  unit='files')

    for filename in filelist:

        with Writer(filename, ftp.size(filename), DEST) as writer:
            ftp.retrbinary('RETR %s' % filename, writer.write)
        print(filename)
        filecounter.update()

    ftp.close()


if __name__ == '__main__':
    download()
