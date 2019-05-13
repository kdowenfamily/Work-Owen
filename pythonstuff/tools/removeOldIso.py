#!/usr/bin/python
'''
@author dowen
'''
import os
import re
import argparse
import subprocess

# make a list of all the Linux commands to run on each logging node
allCmds = {
    "01. Remove Useless ISO": "rm -f /shared/images/BIGIQ-*.iso",
    "02. Remove previous hotfix": "rm -f /shared/images/Hotfix-BIG-IQ-5.1.0.0.14.631-ENG.iso"
}

# clean the given BIG-IQ
def cleanUp(box, user, passwd):
    print "Cleaning {0}.".format(box)

    # loop through the list of commands above to construct a single-line command
    for title, cmd in sorted(allCmds.items()):
        # use SSH to make the command(s) happen on the remote box
        source = user + "@" + box
        retval = subprocess.Popen(["sshpass", "-p", passwd, "ssh", source, cmd], stdout=subprocess.PIPE)
        out, err = retval.communicate()


# take a bunch of BIG-IQ MIPs and collect Memory/CPU stats in files on each of them
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description = "Clean up an old hotfix ISO on each given BIG-IQ")
    parser.add_argument ("machine", nargs="+", help="IP address of a machine with old ISO")
    parser.add_argument ("-u", "--username", default="root", help="Username for the SSH connection")
    parser.add_argument ("-p", "--password", default="default", help="Password for the SSH connection")
    args = parser.parse_args()

    for box in args.machine:
        cleanUp(box, args.username, args.password)
