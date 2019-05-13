#!/usr/bin/python
'''
@author dowen
'''
import os
import re
import sys
import argparse
import subprocess as subp
from distutils.spawn import find_executable
import socket

# Enable password-free SSH connections to a given set of machines

# Constants
CUR_USER = os.getlogin()
CUR_HOSTNAME = socket.gethostname()
PLATFORM = sys.platform

PRIV_SSH_DIR = ""
if PLATFORM == "darwin":
    PRIV_SSH_DIR = "/Users/%s/.ssh" % (CUR_USER)
elif re.search(r'^linux', PLATFORM):
    PRIV_SSH_DIR = "/home/%s/.ssh" % (CUR_USER)
SSH_HOSTS = PRIV_SSH_DIR + "/known_hosts"


# Check to see if there is an RSA already present.
def key_present():
    if "id_rsa" in os.listdir(PRIV_SSH_DIR):
        return True
    else:
        return False


# Generate an SSH Key on the local machine
def gen_key():
    os.chdir(PRIV_SSH_DIR)

    cmd = "ssh-keygen -f %s/id_rsa -t rsa -N ''" % PRIV_SSH_DIR
    retval = subp.Popen(args=cmd, shell=True, stdout=subp.PIPE, stderr=subp.STDOUT)
    out = retval.communicate()


# send the local SSH key to a remote server
def push_key(user, passwd, box, port=22):
    os.chdir(PRIV_SSH_DIR)

    print box + ":"

    # generate a local SSH key if needed
    if not key_present():
        gen_key()

    # if the remote machine already has this key, say so and return
    me = CUR_USER + "@" + CUR_HOSTNAME
    sshdir = "~/.ssh"	# the probable spot for .ssh on the remote box
    grepcmd = "\"if ! [ -e " + sshdir + " ]; then mkdir " + sshdir + "; fi; touch " + sshdir + "/authorized_keys; grep -c '" + me + "' " + sshdir + "/authorized_keys\""
    source = user + "@" + box
    cmd = "sshpass -p %s ssh %s %s" % (passwd, source, grepcmd)
    retval = subp.Popen(args=cmd, shell=True, stdout=subp.PIPE, stderr=subp.STDOUT)
    out = retval.communicate()

    # if grep -c returned a number, we are in there already
    line = re.sub(r'\n$', "", out[0])	# strip the \n off the end
    if ((re.search(r'^\d+$', line)) and (int(line) > 0)):
        print "  Should be able to SSH to " + box + " without a password already.  Skipping."
        return

    # that could also get a bad key error (need to drop and re-learn RSA key),
    #   nothing (need to learn RSA key), or
    #   "not found" (sshpass is not installed on this box)

    noSshPass = re.search(r'not found', line)
    badKeyError = re.search(r'Offending (... )?key in ([^:]+):(\d+)', line)
    noKeyError = re.search(r'The authenticity of host', line)
    nuthin = re.search(r'^$', line)
    keyFile = SSH_HOSTS
    if (noSshPass):
        # a non-starter: need sshpass on the local host to even get off the ground
        print "  The sshpass utility is not installed on this host.  Please intall it."
        sys.exit()

    if (badKeyError):
        # remove the remote host's old RSA key from the ~/.ssh/known_hosts file
        lineNum = badKeyError.group(3) + "d"
        keyFile = badKeyError.group(2)
        cmd = "sed -i %s %s" % (lineNum, keyFile)
        dropLine = subp.Popen(args=cmd, shell=True, stdout=subp.PIPE, stderr=subp.STDOUT)
        dlOut = dropLine.communicate()
        print "  Already had RSA key for %s, and it changed.  Dropped old key." % box

    if (badKeyError or noKeyError or nuthin):
        # add the remote-host's new RSA key to the ~/.ssh/known_hosts file
        cmd = "ssh-keyscan -t rsa %s" % (box)
        keyScan = subp.Popen(args=cmd, shell=True, stdout=subp.PIPE, stderr=subp.STDOUT)
        rsaData = keyScan.communicate()
        rsaKey = rsaData[0].split('\n')[1] + "\n"	# take the 2nd line
        with open (keyFile, "a") as hostFile:
            hostFile.write(rsaKey)

        print "  No RSA key for %s.  Found the latest and added it to %s." % (box, keyFile)

    # push the SSH key to the remote server, if we have the ssh-copy-id script
    if find_executable("ssh-copy-id"):
        print "  Pushing SSH key to remote server"
        sci_path = find_executable("ssh-copy-id")
        cmd = "sshpass -p %s %s %s" % (passwd, sci_path, source)
        retval = subp.Popen(args=cmd, shell=True, stdout=subp.PIPE, stderr=subp.STDOUT)
        retval.communicate()
    else:
        print "  ssh-copy-id required. Please install on %." % CUR_HOSTNAME


# take a bunch of MIPs and deliver SSH keys to each of them
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description = "Simplify SSH access to each given box")
    parser.add_argument ("machine", nargs="+", help="IP address of a remote device")
    parser.add_argument ("-u", "--username", default="root", help="Username for the SSH connection")
    parser.add_argument ("-p", "--password", default="default", help="Password for the SSH connection")
    args = parser.parse_args()

    for box in args.machine:
        push_key(args.username, args.password, box)
