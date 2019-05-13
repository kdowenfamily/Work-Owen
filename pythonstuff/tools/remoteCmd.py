#!/usr/bin/python
'''
@author dowen
'''
import os
import re
import sys
import csv
import argparse
import subprocess

# Run any command on a given set of machines

# Run some commands on the given machine
def runCmdAt(box, cmds, user, passwd):
    # use SSH to make the command(s) happen on the remote box
    source = user + "@" + box
    sub = subprocess	# short hand
    print box + ":"
    for cmd in cmds:
        retval = sub.Popen(["sshpass", "-p", passwd, "ssh", source, cmd], stdout=sub.PIPE, stderr=sub.STDOUT)
        out, err = retval.communicate()
        print out


# take a bunch of MIPs and run a command on each of them
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description = "Run command any on each given box")
    parser.add_argument ("command", help="any command that runs on all the given machines, or path to a CSV file with commands (one command per row)")
    parser.add_argument ("machine", nargs="+", help="IP address of a remote device")
    parser.add_argument ("-u", "--username", default="root", help="Username for the SSH connection")
    parser.add_argument ("-p", "--password", default="default", help="Password for the SSH connection")
    args = parser.parse_args()

    # if this is a CSV file, put all the commands into a list
    commands = []
    if os.path.exists(args.command):
        with open(args.command, 'rb') as commandfile:
            cmdlist = csv.reader(commandfile, delimiter=" ")
            for cmd in cmdlist:
                commands.append(" ".join(cmd))
    else:
        commands.append(args.command)

    # send the command(s) to every machine
    for box in args.machine:
        runCmdAt(box, commands, args.username, args.password)
