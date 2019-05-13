#!/usr/bin/python
'''
@author dowen
'''
import os
import re
import argparse
import subprocess

# Download SSL certs and install them locally on one or more machines.
allCmds = {
    "02. Make Partition Writable": "mount -o remount,rw /usr",
    "03. Back Up Key Store": "cp /usr/lib/jvm/java-1.7.0-openjdk-1.7.0.75.x86_64/jre/lib/security/cacerts /usr/lib/jvm/java-1.7.0-openjdk-1.7.0.75.x86_64/jre/lib/security/cacerts.bak",
    "05. Install Cert in Key Store": "cd /usr/lib/jvm/java-1.7.0-openjdk-1.7.0.75.x86_64/jre/bin/; ./keytool -import -trustcacerts -keystore /usr/lib/jvm/java-1.7.0-openjdk-1.7.0.75.x86_64/jre/lib/security/cacerts -storepass changeit -noprompt -alias %s -file /tmp/botcertfile.pem",
    "06. Change Partion Back to RO": "mount -o remount,ro /usr",
    "07. Restart restjavad": "bigstart restart restjavad",
}

# from the given BIG-IQ, download an SSL cert from the given host
def downloadCertFromSSLhost(box, sslhost, alias, user, passwd):
    print "Downloading an SSL cert from {0} on {1}.".format(sslhost, box)
    source = user + "@" + box

    # download the cert file from the remote SSL host
    download = "openssl s_client -showcerts -connect {0}:443 </dev/null 2>/dev/null|openssl x509 -outform PEM >/tmp/botcertfile.pem".format(sslhost)
    allCmds["01. Download SSL Cert"] = download
    
    # loop through the rest of commands above to install the cert
    for title, cmd in sorted(allCmds.items()):
        if (re.search(r'-alias', cmd)) :
            cmd = cmd % alias
        title = re.sub(r'^\d+\.\s+', "", title)
        print "- " + title
        retval = subprocess.Popen(["sshpass", "-p", passwd, "ssh", source, cmd], stdout=subprocess.PIPE)
        out, err = retval.communicate()


# Take the IP address of an SSL host along with a bunch of BIG-IQ MIPs.  Download the SSL cert from the host to each BIG-IQ.
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description = "Download the SSL cert from the given IP to each given BIG-IQ")
    parser.add_argument ("sslhost", help="IP address of the remote SSL host")
    parser.add_argument ("keyalias", help="Alias to be used for the SSL key (any word)")
    parser.add_argument ("machine", nargs="+", help="IP address of a BIG-IQ device that needs to SSH to the SSL host")
    parser.add_argument ("-u", "--username", default="root", help="Username for the SSH connection to every BIG-IQ")
    parser.add_argument ("-p", "--password", default="default", help="Password for the SSH connection to every BIG-IQ")
    args = parser.parse_args()

    for box in args.machine:
        downloadCertFromSSLhost(box, args.sslhost, args.keyalias, args.username, args.password)
