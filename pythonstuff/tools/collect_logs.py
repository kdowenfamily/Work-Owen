#!/usr/bin/python
'''
@author dowen
'''
import os
import argparse
import subprocess

# sets of log files to collect from each box
logFileSets = [
               "/var/log/restjavad.*",
               "/var/log/tokumx.*",
               "/var/log/tokumon/*",
               "/var/log/tmm*",
               "/var/log/ltm*",
               "/var/log/audit",
               "/var/log/audit.*",
               "/config/*.txt",
              ]

# sets of log diretories to collect from each box
logDirSets = [
              "/var/log/elasticsearch",
             ]

# outside IPs matched with inside IPs in my vApp
boxAlias = {
            "10.255.5.46"  : "10.145.192.10",
            "10.255.6.199" : "10.145.192.22",
            "10.255.6.63"  : "10.145.192.15",
            "10.255.6.172" : "10.145.192.18",
            "10.255.6.174" : "10.145.192.20",
            "10.255.6.175" : "10.145.192.21",
            "10.255.6.173" : "10.145.192.19",
            "10.255.6.236" : "10.145.192.24",
            "10.255.6.231" : "10.145.192.23",
            "10.255.6.38"  : "10.145.192.14"
           }

def getLogsFrom(box, todir, user, passwd):
    boxdir = todir + "/" + box
    if box in boxAlias :
        # this is a vApp machine - name the directory after its internal IP
        boxdir = todir + "/" + boxAlias[box]
    if (not os.path.isdir(boxdir)):
        os.mkdir(boxdir)
    print "Copying logs from " + box + " to " + boxdir

    # get log files
    for log_files in logFileSets :
        source = user + "@" + box + ":" + log_files
        retval = subprocess.Popen(["sshpass", "-p", passwd, "scp", "-p", source, boxdir], stdout=subprocess.PIPE)
        out, err = retval.communicate()

    # get log directories, with all their logs
    for log_dirs in logDirSets :
        source = user + "@" + box + ":" + log_files
        retval = subprocess.Popen(["sshpass", "-p", passwd, "scp", "-pr", source, boxdir], stdout=subprocess.PIPE)
        out, err = retval.communicate()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description = "create a given dir and put restjavad logs from the given machine(s) in it")
    parser.add_argument ("directory", help="directory for all the collected logs")
    parser.add_argument ("machine", nargs="+", help="IP address of a machine with interesting logs")
    parser.add_argument ("-u", "--username", default="root", help="Username for the SCP connection")
    parser.add_argument ("-p", "--password", default="default", help="Password for the SCP connection")
    args = parser.parse_args()

    if (not os.path.isdir(args.directory)):
        os.mkdir(args.directory)

    for box in args.machine:
        getLogsFrom(box, args.directory, args.username, args.password)
