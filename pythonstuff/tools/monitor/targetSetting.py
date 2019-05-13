#!/usr/bin/python
'''
@author dowen
'''
import os
import re
import argparse
import subprocess

# set up to 3 new target logging nodes for all given htSender machines

# set a loggging-node target for the given htSender machine
def setTargetsAt(box, targets, dcd, https, user, passwd):
    targetDir = "/tmp"
    print "Setting logging-node targets on {0}.".format(box)

    # exceptions for weird chroot boxes
    if (box == "10.255.252.104"):		# ITE box
        targetDir = "/root/f5ite/chroot/tmp"    # chroot /tmp dir on an ITE box
    if (box == "10.255.6.53"):			# nosetest driver
        user = "testrunner"
        passwd = "testrunner"

    # create Linux commands to do what you want
    myCmds = [
        "rm -f " + targetDir + "/*_target*_alert_log.txt",
        "rm -f " + targetDir + "/target*_DCD.txt",
        "rm -f " + targetDir + "/target*_HTTPS.txt"
    ]
    for file, lognode in targets.items():
        tFile = targetDir + "/" + file + ".txt"
        myCmds.append("echo '" + lognode + "' >" + tFile)
        if dcd:
            tFile = targetDir + "/" + file + "_DCD.txt"
            myCmds.append("touch " + tFile)
        if https:
            tFile = targetDir + "/" + file + "_HTTPS.txt"
            myCmds.append("touch " + tFile)

    # loop through those commands to construct a single-line command
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
        description = "set 3 logging-node addresses as targets on each given htSender box")
    parser.add_argument ("machine", nargs="+", help="IP address of a machine with 3 htSender drivers")
    parser.add_argument ("-a", "--target_a", default="", help="Target A, a logging-node listener address")
    parser.add_argument ("-b", "--target_b", default="", help="Target B, a logging-node listener address")
    parser.add_argument ("-c", "--target_c", default="", help="Target C, a logging-node listener address")
    parser.add_argument ("-d", "--dcd", action='store_true', default=False, help="Raise this flag if the targets are DCDs, lower it for VIPs")
    parser.add_argument ("-s", "--https", action='store_true', default=False, help="Raise this flag to send over HTTPS, lower it for HTTP")
    parser.add_argument ("-u", "--username", default="root", help="Username for the SSH connection")
    parser.add_argument ("-p", "--password", default="default", help="Password for the SSH connection")
    args = parser.parse_args()

    targets = {}
    file_names = ["targetA", "targetB", "targetC"]
    ct = 0
    for t in [args.target_a, args.target_b, args.target_c]:
        if (t != ""):
            targets[file_names[ct]] = t
        ct += 1

    for box in args.machine:
        setTargetsAt(box, targets, args.dcd, args.https, args.username, args.password)
