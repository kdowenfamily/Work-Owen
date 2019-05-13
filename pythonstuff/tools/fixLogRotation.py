#!/usr/bin/python
'''
@author dowen
'''
import os
import re
import argparse
import subprocess

# Fix the restjavad log settings on one or more machines.
allCmds = {
    "01. Size": "sed -i 's/restjavad_log.MaxFileSize=.*$/restjavad_log.MaxFileSize=10MB/' /etc/restjavad.log.conf",
    "02. Number": "sed -i 's/restjavad_log.MaxBackupIndex=.*$/restjavad_log.MaxBackupIndex=50/' /etc/restjavad.log.conf",
    "03. Restart restjavad": "bigstart restart restjavad"
}

# Fix the restjavad log settings on the given BIG-IQ.
def fixRestjavadLogsOn(box, user, passwd):
    print "Fixing restjavad log settings on {0}.".format(box)
    source = user + "@" + box
    
    # loop through the commands above to fix the settings
    for title, cmd in sorted(allCmds.items()):
        retval = subprocess.Popen(["sshpass", "-p", passwd, "ssh", source, cmd], stdout=subprocess.PIPE)
        out, err = retval.communicate()


# Fix the restjavad settings on a bunch of BIG-IQ MIPs.
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description = "Fix the restjavad log settings (to 10MB, 50 files) on each given BIG-IQ")
    parser.add_argument ("machine", nargs="+", help="IP address of a BIG-IQ device that needs to SSH to the SSL host")
    parser.add_argument ("-u", "--username", default="root", help="Username for the SSH connection to every BIG-IQ")
    parser.add_argument ("-p", "--password", default="default", help="Password for the SSH connection to every BIG-IQ")
    args = parser.parse_args()

    for box in args.machine:
        fixRestjavadLogsOn(box, args.username, args.password)
