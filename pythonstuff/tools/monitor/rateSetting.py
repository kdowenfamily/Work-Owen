#!/usr/bin/python
'''
@author dowen
'''
import os
import re
import argparse
import subprocess

# set a new rate for all given htSender machines

# set an htSender rate for the given htSender machine
def makeStatsAt(box, rate, threads, user, passwd):
    rateDir = "/tmp"
    print "Setting rate of {0} on {1}.".format(rate, box)

    # exceptions for weird chroot boxes
    if (box == "10.255.252.104"):		# ITE box
        rateDir = "/root/f5ite/chroot/tmp"      # /tmp dir for chroot on an ITE box
    if (box == "10.255.6.53"):			# nosetest driver
        user = "testrunner"
        passwd = "testrunner"

    # loop through some commands to construct a single-line command
    rateFile = rateDir + "/rate"
    threadFile = rateDir + "/threads"
    myCmds = [
        "echo " + rate + " >" + rateFile,
        "echo " + threads + " >" + threadFile,
        "rm -f " + rateDir + "/*_target*_alert_log.txt"
    ]
    cmdLine = ""
    for cmd in myCmds:
        cmdLine += cmd + ";"

    # use SSH to make the command(s) happen on the remote box
    source = user + "@" + box
    retval = subprocess.Popen(["sshpass", "-p", passwd, "ssh", source, cmdLine], stdout=subprocess.PIPE)
    out, err = retval.communicate()


# take a bunch of htSender-box MIPs and set a file with an htSender rate on each of them
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description = "set the htSender rate on each given htSender box")
    parser.add_argument ("rate", help="the rate (APS) to set for each htSender driver (3 per box)")
    parser.add_argument ("machine", nargs="+", help="IP address of a machine with 3 htSender drivers")
    parser.add_argument ("-t", "--threads", default="1", help="Number of threads for each sender")
    parser.add_argument ("-u", "--username", default="root", help="Username for the SSH connection")
    parser.add_argument ("-p", "--password", default="default", help="Password for the SSH connection")
    args = parser.parse_args()

    for box in args.machine:
        makeStatsAt(box, args.rate, args.threads, args.username, args.password)
