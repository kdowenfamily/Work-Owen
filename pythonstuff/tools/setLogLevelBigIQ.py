#!/usr/bin/python
'''
@author dowen
'''
import os
import re
import argparse
import subprocess

# Fix the restjavad log levels on one or more machines.
allCmds = {
    "01. Level": "sed -i 's/log4j.rootLogger=.*, restjavad_log.*$/log4j.rootLogger=%s, restjavad_log/' /etc/restjavad.log.conf",
    "02. Restart restjavad": "bigstart restart restjavad"
}

# Fix the restjavad log settings on the given BIG-IQ.
def fixRestjavadLogsOn(box, user, passwd, level):
    print "Fixing restjavad log settings on {0}.".format(box)
    source = user + "@" + box
    
    # loop through the commands above to fix the settings
    for title, cmd in sorted(allCmds.items()):
	if "restjavad_log" in cmd:
            cmd = cmd % level
        retval = subprocess.Popen(["sshpass", "-p", passwd, "ssh", source, cmd], stdout=subprocess.PIPE)
        out, err = retval.communicate()


# Fix the restjavad settings on a bunch of BIG-IQ MIPs.
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description = "Set the restjavad log levels on each given BIG-IQ")
    parser.add_argument ("machine", nargs="+", help="IP address of a BIG-IQ device that needs to SSH to the SSL host")
    parser.add_argument ("-l", "--level", default="DEBUG", help="The log level to set, such as DEBUG or INFO")
    parser.add_argument ("-u", "--username", default="root", help="Username for the SSH connection to every BIG-IQ")
    parser.add_argument ("-p", "--password", default="default", help="Password for the SSH connection to every BIG-IQ")
    args = parser.parse_args()

    for box in args.machine:
        fixRestjavadLogsOn(box, args.username, args.password, args.level)
