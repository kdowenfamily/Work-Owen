#!/usr/bin/python
'''
@author dowen
'''
import os
import re
import argparse
import subprocess

# Start visual VM on all given machines.
allCmds = {
    "2 Big Script": "if [ ! -e /config/iptables.save ]; then /usr/bin/enable-jmx-debugging; fi",
    "3 Restart ES": "bigstart restart elasticsearch",
}

# Start Visual VM on the given BIG-IQ.
def enableVVM(box, user, passwd):
    print "Enabling Visual VM on {0}.".format(box)
    source = user + "@" + box

    allCmds["1 Edit File"] = 'echo "' + box + '" >/service/elasticsearch/enableJMX'
    
    # loop through the commands
    for title, cmd in sorted(allCmds.items()):
        retval = subprocess.Popen(["sshpass", "-p", passwd, "ssh", source, cmd], stdout=subprocess.PIPE)
        out, err = retval.communicate()


# Start Visual VM on a bunch of BIG-IQs.
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description = "Enable Visual VM on each given BIG-IQ")
    parser.add_argument ("machine", nargs="+", help="IP address of a BIG-IQ device that you want to monitor with Visual VM")
    parser.add_argument ("-u", "--username", default="root", help="Username for the SSH connection to every BIG-IQ")
    parser.add_argument ("-p", "--password", default="default", help="Password for the SSH connection to every BIG-IQ")
    args = parser.parse_args()

    for box in args.machine:
        enableVVM(box, args.username, args.password)
