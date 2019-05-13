#!/usr/bin/python
'''
@author dowen
'''
from __future__ import division
import os
import re
import argparse
import subprocess

SAMPLE_SIZE = 10

# read all the alert-rate/latency logs from the given BIG-IQs
def showRatesAt(box, filename, alert_rates, latencies, user, passwd):
    rateDir = "/tmp"

    # exceptions for weird chroot boxes
    if (box == "10.255.252.104"):		# ITE box
        rateDir = "/root/f5ite/chroot/tmp"      # /tmp dir for chroot on an ITE box
    if (box == "10.255.6.53"):			# nosetest driver
        user = "testrunner"
        passwd = "testrunner"

    print "{0}: reading {1}/{2}.".format(box, rateDir, filename)

    # get all the file(s)
    rateLog = rateDir + "/" + filename
    showCmds = 'ls ' + rateLog
    source = user + "@" + box
    retval = subprocess.Popen(["sshpass", "-p", passwd, "ssh", source, showCmds], stdout=subprocess.PIPE)
    out, err = retval.communicate()
    files = out.split()

    # for each file, get the contents calculate the rate sent to the target, and record the latencies
    for log in files:
        cmd = "cat " + log
        retval = subprocess.Popen(["sshpass", "-p", passwd, "ssh", source, cmd], stdout=subprocess.PIPE)
        out, err = retval.communicate()
        lines = out.splitlines()

        # find the first sample - shoot for SAMPLE_SIZE minutes ago
        sample1 = -SAMPLE_SIZE
        if (len(lines) < SAMPLE_SIZE):
            sample1 = 0

        # sample the alert counts
        start = re.search(r'^(\d+)\s+(\d+)(\s\d+)?$', lines[sample1])
        end = re.search(r'^(\d+)\s+(\d+)(\s\d+)?$', lines[-1])
        seconds = int(end.group(1)) - int(start.group(1))
        alerts_sent = int(end.group(2)) - int(start.group(2))

        # calculate and record the send rate
        if (seconds == 0):
            rate = 0
        else:
            rate = alerts_sent/seconds
        parts = log.split("/")	       # TODO - the name of the log file must follow this pattern: <target-ip>_...
        targetSrch = re.search(r'^([\d\.]+)_', parts[-1])
        target = targetSrch.group(1)
        if (target not in alert_rates):
            alert_rates[target] = {}
        if (box not in alert_rates[target]):
            alert_rates[target][box] = 0.0
        alert_rates[target][box] += rate

        # record all the latencies (ms)
        if (target not in latencies):
            latencies[target] = {}
        end = re.search(r'^\d+\s+\d+(\s\d+)?$', lines[-1])
        if (end.group(1)):
            ct = sample1
            latencies[target][box] = ""
            while (ct <= -1):
               start = re.search(r'^\d+\s+\d+(\s(\d+))?$', lines[ct])
               if (start.group(1)):
                   latencies[target][box] += start.group(2)
                   if (ct != -1):
                       latencies[target][box] += ", "
               ct += 1 
        


# take a bunch of driver IPs and show the alert-count files on each of them
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description = "show alert rates from each given htSender driver")
    parser.add_argument ("file", help="name of the file(s) in /tmp with rate information - you can use wildcards")
    parser.add_argument ("driver", nargs="+", help="IP address of a driver machine")
    parser.add_argument ("-u", "--username", default="root", help="Username for the SSH connection")
    parser.add_argument ("-p", "--password", default="default", help="Password for the SSH connection")
    args = parser.parse_args()

    alert_rates = {}
    latencies = {}

    for box in args.driver:
        showRatesAt(box, args.file, alert_rates, latencies, args.username, args.password)

    print "Latencies in the last {0} minutes (ms):".format(SAMPLE_SIZE)
    for target_ip in latencies:
        for driver in latencies[target_ip]:
            print "{0: >15} -> {1: >15}: {2}".format(driver, target_ip, latencies[target_ip][driver])

    full_rate = 0
    for target_ip in alert_rates:
        target_rate = 0
        for driver in alert_rates[target_ip]:
            full_rate += alert_rates[target_ip][driver]

    print "Send rate is {0}.".format(round(full_rate, 2))
