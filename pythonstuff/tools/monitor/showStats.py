#!/usr/bin/python
'''
@author dowen
'''
import os
import argparse
import subprocess


# show stats from the given BIG-IQs
def showStatsAt(box, dir, filename, user, passwd):
    filename = dir + "/" + filename

    # use top to gather stats
    print "\nMIP {0} ({1}).".format(box, filename)
    showCmds = 'cat ' + filename
    source = user + "@" + box
    retval = subprocess.Popen(["sshpass", "-p", passwd, "ssh", source, showCmds], stdout=subprocess.PIPE)
    out, err = retval.communicate()
    print out


# take a bunch of BIG-IQ MIPs and show the Memory/CPU-stats files on each of them
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description = "show a file with CPU/memory stats on each given BIG-IQ (in /config)")
    parser.add_argument ("file", help="name of the file(s) to show in /config")
    parser.add_argument ("machine", nargs="+", help="IP address of a machine with interesting CPU/memory")
    parser.add_argument ("-d", "--directory", default="/config", help="Directory to keep the stats file")
    parser.add_argument ("-u", "--username", default="root", help="Username for the SSH connection")
    parser.add_argument ("-p", "--password", default="default", help="Password for the SSH connection")
    args = parser.parse_args()

    for box in args.machine:
        showStatsAt(box, args.directory, args.file, args.username, args.password)
