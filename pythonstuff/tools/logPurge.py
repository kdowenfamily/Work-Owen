#!/usr/bin/python
'''
@author dowen
'''
import os
import re
import sys
import argparse
import subprocess

# purge all the restjavad logs on a given set of BIG-IQ machines
# This is good for erasing all records of an earlier test

allCmds = [
    "rm -f /var/log/restjavad.*; ",
    "touch /var/log/restjavad.0.log; ",
    "bigstart restart restjavad; ",
    "rm -f /var/log/webd/access.*; ",
    "touch /var/log/webd/access.log; ",
    "rm -f /var/log/webd/errors.*; ",
    "touch /var/log/webd/errors.log; ",
    "bigstart restart webd"
]

# purge all restjavad logs from the given BIG-IQ
def makeStatsAt(box, user, passwd):
    print "Removing various logs from {0}.".format(box)

    # loop through some commands to construct a single-line command
    cmdLine = ""
    for cmd in allCmds:
        cmdLine += cmd

    # use SSH to make the command(s) happen on the remote box
    source = user + "@" + box
    retval = subprocess.Popen(["sshpass", "-p", passwd, "ssh", source, cmdLine], stdout=subprocess.PIPE)
    out, err = retval.communicate()


# take a bunch of BIG-IQ MIPs and remove restjavad logs from each of them
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description = "remove all restjavad logs from each given BIG-IQ box")
    parser.add_argument ("machine", nargs="+", help="IP address of a BIG-IQ device")
    parser.add_argument ("-u", "--username", default="root", help="Username for the SSH connection")
    parser.add_argument ("-p", "--password", default="default", help="Password for the SSH connection")
    args = parser.parse_args()

    print "This script restarts both restjavad and webd, thus clearing all memory in both."
    print "Are you sure? [y/N]"
    answer = raw_input().lower()
    if not (re.search(r"^y", answer)):
        sys.exit(0)

    for box in args.machine:
        makeStatsAt(box, args.username, args.password)
