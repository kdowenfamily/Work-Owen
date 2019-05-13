#!/usr/bin/python
'''
@author dowen
'''
from __future__ import division
import os
import re
import argparse
import subprocess

# thresholds to monitor
MAX_DISKFULL = 80
MIN_FREEMEM = 10
MIN_IDLECPU = 40

# summarize stats from the given BIG-IQs
def summarizeStatsAt(box, filedir, filename, allData, user, passwd):
    filename = filedir + "/" + filename

    # use top to gather stats
    print "MIP {0} ({1}).".format(box, filename)
    showCmds = 'cat ' + filename
    source = user + "@" + box
    retval = subprocess.Popen(["sshpass", "-p", passwd, "ssh", source, showCmds], stdout=subprocess.PIPE)
    out, err = retval.communicate()
    countable = 0
    findCPU = 0
    findMem = 0
    findFreeMem = 0
    findDisk = 0
    findIOr = 0
    findIOw = 0
    findERROR = 0
    findWARN = 0
    name = ""
    for line in out.splitlines():
       # find the start of a section
       if (re.search(r'^\d+\.\s+[^\(]+ \(', line)):
           if (re.search(r'(Drops|Timeouts|Errors|Warnings|Messages|Notices|Skips|Failures)', line)):
               countable = 1

               # get the name of this section from the title
               dtQuery = re.search(r'^\d+\.\s+([^\(]+) \(', line)
               name = dtQuery.group(1)
               if name not in allData:
                    allData[name] = 0
           elif (re.search(r'CPU/Memory', line)):
               findMem = 1
           elif (re.search(r'Idle CPU', line)):
               findCPU = 1
           elif (re.search(r'Free Memory', line)):
               findFreeMem = 1
           elif (re.search(r'Disk Usage', line)):
               findDisk = 1
           elif (re.search(r'Disk I/O - write', line)):
               findIOw = 1
           elif (re.search(r'Disk I/O - read', line)):
               findIOr = 1
           elif (re.search(r'Unique ERRORs', line)):
               findERROR = 1
           elif (re.search(r'Unique WARNs', line)):
               findWARN = 1
           continue

       # find the end of a section
       if (re.search(r'^\s*$', line)):
           countable = 0
           findCPU = 0
           findMem = 0
           findFreeMem = 0
           findDisk = 0
           findIOr = 0
           findIOw = 0
           findERROR = 0
           findWARN = 0
           name = ""
           continue 

       # in a countable section, add to the count
       if (countable):
           number = re.search(r'/var/log/[^:]+:(\d+)', line)
           if (number):
               allData[name] += int(number.group(1))
           else:
               if (re.search(r'^\d+$', line)):
                   allData[name] += int(line)
               else:
                   # some non numbers in there - punt
                   allData[name] += 0

       # in the Idle CPU section, get the percentage of idle CPU
       if (findCPU):
           columns = line.split()
           if (len(columns) == 11):
               tcpu = re.search(r'\s+(\d+\.\d+)\s+\d+\.\d+$', line)
               if (tcpu.group(1) < MIN_IDLECPU):
                   allData["Idle CPU"][box] = tcpu.group(1)
           elif ((len(columns) == 12) or (len(columns) == 13)):
               tcpu = re.search(r'\s+(\d+\.\d+)$', line)
               if (tcpu.group(1) < MIN_IDLECPU):
                   allData["Idle CPU"][box] = tcpu.group(1)

       # in the free memory section, add the total and free space
       if ((findFreeMem) and (re.search(r'^Mem:', line))):
           tmem = re.search(r'^Mem:.\s+([\d]+)\s+([\d]+)\s+([\d]+)', line)
           allData["Total Memory"][box] = int(tmem.group(1))
           allData["Free Memory"][box] = int(tmem.group(3))
           percent = (100 * allData["Free Memory"][box])/allData["Total Memory"][box]
           allData["Percent Memory"][box] = percent

       # in the free memory section, available memory (free + swap + cache - a true number)
       # See https://access.redhat.com/solutions/406773
       if ((findFreeMem) and (re.search(r'^-/\+ buffers', line))):
           amem = re.search(r'^-/\+ buffers/cache:\s+([\d]+)\s+([\d]+)', line)
           allData["Available Memory"][box] = int(amem.group(2))
           percent = (100 * allData["Available Memory"][box])/allData["Total Memory"][box]
           allData["Percent Memory"][box] = percent

       # remove any uninteresting percentages
       if ((box in allData["Percent Memory"]) and (allData["Percent Memory"][box] >= MIN_FREEMEM)):
           del allData["Percent Memory"][box]

       # in the Disk Usage section, find disks that are scary full
       if (findDisk):
           # /dev/md4              287M  207M   66M  76% /
           thresh = MAX_DISKFULL
           disk = re.search(r'^([\/\S]+)?\s+.+\s+(\d+)\%\s+(\S+)$', line)
           if (disk):
               if (disk.group(3) == "/usr"):
                   # This is usually 91 on BIG-IQ
                   thresh = 92
               if (int(disk.group(2)) >= thresh):
                   if (box not in allData["Disk"]):
                       allData["Disk"][box] = {}
                   allData["Disk"][box][disk.group(3)] = int(disk.group(2)) 

       # in the Disk I/O read section, get the read I/O rates for each machine
       if ((findIOr) and (re.search(r'[\d\.]+..\/s', line))):
           io = re.search(r'([\d\.]+..\/s)', line)
           allData["DiskIOr"][box] = io.group(1)

       # in the Disk I/O write section, get the write I/O rates for each machine
       if ((findIOw) and (re.search(r'[\d\.]+..\/s', line))):
           io = re.search(r'([\d\.]+..\/s)', line)
           allData["DiskIOw"][box] = io.group(1)

       # in the ERRORs section, add the ERROR strings to a list 
       if (findERROR):
           allData["ERRORs"].append(str(line[:220])) 

       # in the WARNs section, add the WARN strings to a list 
       if (findWARN):
           allData["WARNs"].append(str(line[:220])) 

    return allData 


# take a bunch of BIG-IQ MIPs and show the Memory/CPU-stats files on each of them
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description = "summarize a file with CPU/memory stats on each given BIG-IQ")
    parser.add_argument ("file", help="name of the file(s) to show in /config")
    parser.add_argument ("machine", nargs="+", help="IP address of a machine with interesting CPU/memory")
    parser.add_argument ("-d", "--directory", default="/config", help="Directory to keep the stats file")
    parser.add_argument ("-u", "--username", default="root", help="Username for the SSH connection")
    parser.add_argument ("-p", "--password", default="default", help="Password for the SSH connection")
    args = parser.parse_args()

    bigNumbers = {}
    bigNumbers["Idle CPU"] = {}
    bigNumbers["Free Memory"] = {}
    bigNumbers["Available Memory"] = {}
    bigNumbers["Total Memory"] = {}
    bigNumbers["Percent Memory"] = {}
    bigNumbers["Disk"] = {}
    bigNumbers["DiskIOr"] = {}
    bigNumbers["DiskIOw"] = {}
    bigNumbers["ERRORs"] = []
    bigNumbers["WARNs"] = []
    subcategories = {}
    subcategories["Full System"] = r'^(All [A-Z]+ Messages|Broken Pipe Errors|Out of Memory Errors)$'
    subcategories["BIG-IP"] = r'^(Client-Side|Server-Side|DCD-Monitor)'
    subcategories["NGINX"] = r'^NGINX'
    subcategories["restjavad"] = r'^(restjavad|Threshold Warnings|Bulk Processing)'
    subcategories["restjavad Forwarding"] = r'^Forwarding'
    subcategories["restjavad Username Update"] = r'^Username'
    subcategories["elasticsearch"] = r'^ES '
    for box in args.machine:
        summarizeStatsAt(box, args.directory, args.file, bigNumbers, args.username, args.password)

    print "\nFPS-Log Summary"
    subcat = {}
    for f in sorted(bigNumbers):
        if not ((f == "Free Memory") or (f == "Available Memory") or (f == "Total Memory") or (f == "Percent Memory") or (f == "Idle CPU")  or (f == "Disk") or (f == "DiskIOr") or (f == "DiskIOw") or (f == "ERRORs") or (f == "WARNs")):
            for scname in subcategories:
                if (scname not in subcat):
                    subcat[scname] = {}
                cat = re.search(subcategories[scname], f)
                if cat:
                    subcat[scname][f] = bigNumbers[f]
    for scn in ("BIG-IP", "Full System", "NGINX", "restjavad", "restjavad Forwarding", "restjavad Username Update", "elasticsearch"):
        print "  " + scn
        for fieldname in sorted(subcat[scn]):
            print "    {0}: {1}".format(fieldname, subcat[scn][fieldname])

    print "\nIdle CPU Too Low (< " + str(MIN_IDLECPU) + "%)"
    if (bigNumbers["Idle CPU"]):
        for b in sorted(bigNumbers["Idle CPU"]):
            print "{0}: {1}%".format(b, bigNumbers["Idle CPU"][b])
    else:
        print "- All OK"

    print "\nFree + Available Memory Too Low (< " + str(MIN_FREEMEM) + "%)"
    if (bigNumbers["Percent Memory"]):
        for b in sorted(bigNumbers["Free Memory"]):
            if (b in bigNumbers["Percent Memory"]):
                if ((b in bigNumbers["Total Memory"]) and (b in bigNumbers["Available Memory"])):
                    percent = bigNumbers["Percent Memory"][b]
                    avail = bigNumbers["Available Memory"][b]/1024
                    aUnit = "M"
                    if (avail > 999.0) :
                        avail = avail/1024
                        aUnit = "G"
                    total = bigNumbers["Total Memory"][b]/(1024 * 1024)
                    print "{0}: {1}% ({2}{3}/{4}G)".format(b, round(percent, 3), round(avail, 2), aUnit, round(total, 2))
                else:
                    print "{0}: {1} free".format(b, bigNumbers["Free Memory"][b])
    else:
        print "- All OK"

    print "\nDisk Too Full (>= " + str(MAX_DISKFULL) + "%)"
    if (bigNumbers["Disk"]):
        for b in sorted(bigNumbers["Disk"]):
            print "{0}:".format(b)
            for disk, pct in bigNumbers["Disk"][b].items():
                print "  {0} - {1}%".format(disk, pct)
    else:
        print "- All OK"

    if (bigNumbers["DiskIOw"] and bigNumbers["DiskIOr"]):
        print "\nDisk I/O at /var/config"
        for b in sorted(set(bigNumbers["DiskIOw"])):
            print "{0}: {1} writes, {2} reads".format(b, bigNumbers["DiskIOw"][b], bigNumbers["DiskIOr"][b])

    if (bigNumbers["ERRORs"]):
        print "\nUnique ERROR Logs"
        for e in sorted(set(bigNumbers["ERRORs"])):
            print e

    if (bigNumbers["WARNs"]):
        print "\nUnique WARN Logs"
        for w in sorted(set(bigNumbers["WARNs"])):
            print w
