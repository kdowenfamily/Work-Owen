#!/usr/bin/python
'''
@author dowen
'''
import os
import re
import argparse
import subprocess

# make a list of all the Linux commands to run on each logging node
allCmds = {
    "01. Timestamp": "date",
    "02. CPU/Memory": "top -b -n 1 |head -4",
    "03. Java Processes": "top -b -n 1 |grep java",
    "04. Disk Usage": "df -h",
    "05. Free Memory": "free -k",
    "06. Idle CPU": "mpstat -P ALL |grep all",
    "07. File Descriptors": "lsof 2>/dev/null |wc -l",
    "08. Max File Descriptors": "cat /proc/sys/fs/file-max",
}

diskIO = {
    "10. Disk I/O - write": "dd if=/dev/zero of=/var/config/largefile bs=4k count=1024 2>&1 |awk '/copied/ {print $8 " "  $9}'",
    "11. Disk I/O - read": "dd if=/var/config/largefile of=/dev/null bs=4k count=1024 2>&1 |awk '/copied/ {print $8 " "  $9}'",
    "12. Disk I/O Clean Up": "rm -f /var/config/largefile",
}

diskIOroot = {
    "10. Disk I/O - write": "dd if=/dev/zero of=/largefile bs=4k count=1024 2>&1 |awk '/copied/ {print $8 " "  $9}'",
    "11. Disk I/O - read": "dd if=/largefile of=/dev/null bs=4k count=1024 2>&1 |awk '/copied/ {print $8 " "  $9}'",
    "12. Disk I/O Clean Up": "rm -f /largefile",
}

nginxCmds = {
    "20. NGINX Drops 502": "grep -c ' 502 ' /var/log/webd/access.log",
    "21. NGINX Drops 503": "grep -c ' 503 ' /var/log/webd/access.log",
    "22. NGINX Drops Cannot assign addr": "grep -c 'Cannot assign requested address' /var/log/webd/errors.log",
}

restjavadCmds = {
    "31. Out of Memory Errors": "grep -c 'OutOfMemory' /var/log/restjavad.*.log",
    "32. Broken Pipe Errors": "grep -c 'java.io.IOException: Broken pipe' /var/log/restjavad.*.log",
    "33. Username Update: Errors": "grep -c 'more than the limit 5000. Narrow Down the query' /var/log/restjavad.*.log",
    "34. Username Update: Warnings": "grep -c 'Found too many alerts, processing only' /var/log/restjavad.*.log",
    "35. Username Update: Rough Num of Skips": "grep 'Found too many alerts, processing only' /var/log/restjavad.* |grep -o 'out of [0-9]*$' |awk '{ TODO += $3; DONE += 500; DROP = TODO - DONE } END { print DROP/2 }'",
    "36. Forwarding Drops, total": "grep -c 'Queue size is full' /var/log/restjavad.*.log",
    "37. Forwarding-to-Custom Drops": "grep 'Queue size is full' /var/log/restjavad.*.log |grep -c CustomAlertForwardState",
    "38. Forwarding-to-SOC Drops": "grep 'Queue size is full' /var/log/restjavad.*.log |grep -c SocAlertForwardState",
    "39. Forwarding-to-Syslog Drops": "grep 'Queue size is full' /var/log/restjavad.*.log |grep -c SyslogAlertForwardState",
    "40. Forwarding Suspension Warnings": "grep -ci 'suspending alert consumption' /var/log/restjavad.*.log",
    "41. Forwarding Resumption Notices": "grep -ci 'Resuming alert consum' /var/log/restjavad.*.log",
    "42. Forwarding Exception Warnings": "grep -ci 'Exception while forwarding alert' /var/log/restjavad.*.log",
    "43. Forwarding 'no SOC fwd module' Drops": "grep -c 'No SOC forwarding module is found' /var/log/restjavad.*.log",
    "44. restjavad Timeouts": "grep -c 'java.util.concurrent.TimeoutException' /var/log/restjavad.*.log",
    "45. restjavad ForwardingAlertWorker Timeouts": "grep 'java.util.concurrent.TimeoutException' /var/log/restjavad.*.log |grep -c 'ForwardingAlertWorker'",
    "46. restjavad Connection Failures: ": "grep -c 'java.net.ConnectException' /var/log/restjavad.*.log",
    "47. ES Drops": "grep -c 'attachments through the bulk post' /var/log/restjavad.*.log",
    "48. ES High Ingestion Drops": "grep -o 'Dropped [0-9]* alerts because of high input rate from' /var/log/restjavad.*.log |awk '{ SUM += $2 } END { print SUM }'",
    "49. ES Fail to POST Errors": "grep -c 'Failed POST to ES' /var/log/restjavad.*.log",
    "40. Bulk Processing: Suspend Warnings": "grep -ci 'Suspending bulk request processing' /var/log/restjavad.*.log",
    "41. Bulk Processing: Resume Notices": "grep -ci 'Resuming bulk request processing' /var/log/restjavad.*.log",
    "42. All WARN Messages": "grep -c 'WARN' /var/log/restjavad.*.log",
    "43. All ERROR Messages": "grep -c 'ERROR' /var/log/restjavad.*.log",
    "44. Threshold Warnings": "grep -c 'Median threshold met' /var/log/restjavad.*.log",
}

tmmCmds = {
    "60. Client-Side Success Notices": "zgrep -c 'routed request to pool' /var/log/tmm*",
    #"61. Client-Side Rejected-by-Client Notices": "zgrep -c fpm_client_shutdown_peer /var/log/tmm*",
    "62. Server-Side Success Notices": "zgrep -c 'Publisher .* succeeded' /var/log/tmm*",
    "63. Server-Side Failure Notices": "zgrep -c 'Publisher .* failed' /var/log/tmm*",
    "64. DCD-Monitor Warnings": "zgrep -c 'investigate' /var/log/ltm*",
}

extremeCmds = {}	# constructed at run time

# sed tricks to find unique warnings and errors
findStrW = r"grep WARN /var/log/restjavad.*.log "
findStrE = r"grep ERROR /var/log/restjavad.*.log "
preambleW = r"|sed -e 's/^.*\[WARN\]\[.* EDT\]/_file_[WARN][_date_]/' "
preambleE = r"|sed -e 's/^.*\[ERROR\]\[.* EDT\]/_file_[ERROR][_date_]/' "
outOf = r"|sed -e 's/out of [0-9]*$/out of _N_/' "
need = r"|sed -e 's/Need [0-9]*,/Need _N_,/' "
rcvd = r"|sed -e 's/received [0-9]*$/received _N_/' "
droppedN = r"|sed -e 's/Dropped [0-9]* alerts/Dropped _N_ alerts/' "
uuid = r"|sed -e 's/........-....-....-....-............/_UUID_/g' "
dateStamp = r"|sed -e 's/....-..-..T..:..:..\....-..:../_date-stamp_/g' "
dateStamp2 = r"|sed -e 's/....-..-..t..-..-..-..../_date-stamp_/g' "
millis = r"|sed -e 's/ [0-9]* millis/ _N_ millis/g' "
authToken = r"|sed -e 's/em_server_auth_token=\S* /em_server_auth_token=_AUTH-TOKEN_ /' "
sortIt = r"|sort -u "

# make a long grep command to find unique warnings and errors
sedStack = uuid + outOf + need + rcvd + droppedN + dateStamp + dateStamp2 + millis + authToken + sortIt
findUniqueWarn = findStrW + preambleW + sedStack
findUniqueError= findStrE + preambleE + sedStack


# find a given file or directory on a given machine, to see if it is eligible for certain tests
def boxHas(box, filename, user, passwd):
    cmd = "ls {0} 2>/dev/null".format(filename)
    source = user + "@" + box
    retval = subprocess.Popen(["sshpass", "-p", passwd, "ssh", source, cmd], stdout=subprocess.PIPE)
    out, err = retval.communicate()
    if (out):
        return True;
    else:
        return False;


# gather stats from the given machine
def makeStatsAt(box, dir, filename, user, passwd):
    file = dir + "/" + filename
    print "Creating {0} on {1}.".format(file, box)
    tmpfile = "/tmp/" + filename + "." + str(os.getpid())

    # construct a command line (pretty much a bash script)
    topHead = "top -b -n 1 |head -7 |tail -1"   # command to get the header line from top

    # test the box for each test set
    boxCmds = allCmds
    if (boxHas(box, "/var/log/webd/access.log", user, passwd)):
        boxCmds = dict(boxCmds.items() + nginxCmds.items())
    if (boxHas(box, "/var/log/restjavad.*.log", user, passwd)):
        boxCmds = dict(boxCmds.items() + restjavadCmds.items())
        boxCmds = dict(boxCmds.items() + extremeCmds.items())
    if (boxHas(box, "/var/config", user, passwd)):
        boxCmds = dict(boxCmds.items() + diskIO.items())
    if (boxHas(box, "/var/log/tmm*", user, passwd)):
        boxCmds = dict(boxCmds.items() + tmmCmds.items())
    else:
        boxCmds = dict(boxCmds.items() + diskIOroot.items())

    # loop through the list of commands above and send them through SSH
    source = user + "@" + box
    cmdLine = 'echo "Status Readings" >' + tmpfile + '; '
    for title, cmd in sorted(boxCmds.items()):
        cmdLine += 'echo "\n' + title + ' (' + cmd + ')" >>' + tmpfile + '; '
        if ((re.search('top ', cmd)) and (re.search('java', cmd))):
            # this is a top command - get the header from top first
            cmdLine += topHead + ' >>' + tmpfile + '; '
        cmdLine += cmd + ' >>' + tmpfile 
        cmdLine += '; '

        # use SSH to make the command(s) happen on the remote box
        retval = subprocess.Popen(["sshpass", "-p", passwd, "ssh", source, cmdLine], stdout=subprocess.PIPE)
        out, err = retval.communicate()

        cmdLine = ""

    # to avoid any overwrites, move the tmp file to the final location
    retval = subprocess.Popen(["sshpass", "-p", passwd, "ssh", source, "mv", tmpfile, file], stdout=subprocess.PIPE)
    retval.communicate()


# take a bunch of BIG-IQ MIPs and collect Memory/CPU stats in files on each of them
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description = "create a file with CPU/memory stats on each given BIG-IQ (in /config)")
    parser.add_argument ("file", help="name of the file to create in /config")
    parser.add_argument ("machine", nargs="+", help="IP address of a machine with interesting CPU/memory")
    parser.add_argument ("-d", "--directory", default="/config", help="Directory to keep the stats file")
    parser.add_argument ("-u", "--username", default="root", help="Username for the SSH connection")
    parser.add_argument ("-p", "--password", default="default", help="Password for the SSH connection")
    parser.add_argument ("-x", "--xtreme", action='store_true', default=False, help="Xtreme grep and sed commands in logs")
    args = parser.parse_args()

    if (args.xtreme):
        extremeCmds["41. Unique WARNs"] = findUniqueWarn
        extremeCmds["42. Unique ERRORs"] = findUniqueError

    for box in args.machine:
        makeStatsAt(box, args.directory, args.file, args.username, args.password)
