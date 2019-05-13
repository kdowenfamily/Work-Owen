#!/usr/bin/python
'''
@author dowen
'''
import os
import argparse
import subprocess

def sendFileTo(box, destDir, srcPath, user, passwd):
    # sanity check the file
    if (not os.path.exists(srcPath)):
        return

    # send file
    dest = user + "@" + box + ":" + destDir 
    print "Sending " + srcPath + " to " + dest + "."
    retval = subprocess.Popen(["sshpass", "-p", passwd, "scp", "-p", srcPath, dest], stdout=subprocess.PIPE)
    out, err = retval.communicate()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description = "Send a given file to the given machine(s), in the given directory")
    parser.add_argument ("file", help="path to local file")
    parser.add_argument ("directory", help="directory for the file, on all machines")
    parser.add_argument ("machine", nargs="+", help="IP address of a machine that needs the file")
    parser.add_argument ("-u", "--username", default="root", help="Username for the SCP connection")
    parser.add_argument ("-p", "--password", default="default", help="Password for the SCP connection")
    args = parser.parse_args()

    for box in args.machine:
        sendFileTo(box, args.directory, args.file, args.username, args.password)
