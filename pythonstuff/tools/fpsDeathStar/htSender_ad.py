import urllib3
import logging
import sys
import re
import time
import thread
from os import listdir
from os.path import isfile, join
from BaseHTTPServer import BaseHTTPRequestHandler
from StringIO import StringIO
from optparse import OptionParser
from threading import Thread
import threading

urllib3.disable_warnings()
LOGGER = logging.getLogger(__name__)

class HTTPRequest(BaseHTTPRequestHandler):
    def __init__(self, request_text):
        self.rfile = StringIO(request_text)
        self.raw_requestline = self.rfile.readline()
        self.error_code = self.error_message = None
        self.parse_request()
        self.body = ""
        self.headers = {}
        self.length = 0
        self.verbose = False
        rfile = StringIO(request_text)
        line = rfile.readline() #skip request line
        line = rfile.readline()
        while (len(line.strip())>0):
            if self.verbose:
                print line.strip()
            ar = line.split('=')
            key = ar[0].strip().lower()
            val = ar[1].strip()
            if self.verbose:
                print "  got: '" + key + "' : '" + val + "'"
            if (key == 'content-length'):
                self.length = int(val)
	    #elif (key.lower()== 'connection'):
                #pass
            else:
                self.headers[key] = val
            line = rfile.readline()
        
        if (self.length > 0):
            self.body = rfile.read()
            self.length = len(self.body)
 
    def send_error(self, code, message):
        self.error_code = code
        self.error_message = message

    @property
    def verbose(self):
        return self.verbose
    @verbose.setter
    def verbose (self, value):
        self.verbose = value

def GetURL(logiq_ip, proto, port, path):
    if (proto == "https"):
        return "https://"+logiq_ip+""+path
    else:
        return "http://"+logiq_ip+":"+str(port)+path

totalLatency = 0
latencySample = 0
lockLat = threading.RLock()
def SampleLat(latency):
    global lockLat
    global totalLatency
    global latencySample
    lockLat.acquire()
    totalLatency += latency
    latencySample += 1
    lockLat.release()
    
def PrintLat():
    global latencySample
    if (latencySample>0):
        global lockLat
        global totalLatency
        lockLat.acquire()
        print "Average Latency is " + str(totalLatency/latencySample) + "ms"    
        lockLat.release()
    

def send_alerts(mypath, server, rate, fpspath, tcp_port=8008, verbose=False, protocol='http') :
    if rate > 0:
        current_milli_time = lambda: int(round(time.time() * 1000))
    http = urllib3.PoolManager()
    onlyfiles = [ f for f in listdir(mypath) if isfile(join(mypath,f)) ]
    if rate > 0:
        start = current_milli_time()
        delta = round(1000.0/rate)
        iteration = 0
        if verbose:
            print "rate is " + str(delta) + " per ms"

    good_alerts = 0
    for currFile in onlyfiles:
        if rate > 0:
            diff = (delta*iteration) - current_milli_time() + start
            if (diff > 10):
               time.sleep(diff/1000.0)
            iteration += 1
        with open(mypath+currFile, "rb") as myfile:
            alert = HTTPRequest(myfile.read())
            path_in_file = re.search(r'^(\/[^\/]+)\/', alert.path)
            p_in_file = path_in_file.group(1)
            if not (p_in_file == fpspath):
                alert.path = re.sub(r'^\/[^\/]+\/', fpspath + "/", alert.path)
            alert.verbose = verbose
            if verbose:
                print "\n\nAlert file: " + currFile + ", Destination: " + server + ":", tcp_port 
            if (alert.error_code):
                if verbose:
                    print "Error! " + str(alert.error_code) + " " + alert.error_message
                continue
            
            LOGGER.debug("Sending this to the Logging Node:")
            LOGGER.debug("{0} {1} {2} {3}".format(alert.command, alert.path, alert.body, alert.headers))
            if verbose:
                print "\nSending this to the Logging Node:"
                print alert.command, alert.path, alert.body, alert.headers
            try:
                before = current_milli_time()
                response = http.request(alert.command, GetURL(server, protocol, tcp_port, alert.path), None, body=alert.body, headers=alert.headers)
                SampleLat(current_milli_time()-before)
                if (response.status == 200):
                    if verbose:
                       print "."+ currFile
                       print "\nSuccess!"
                    good_alerts += 1
                else:
                    if verbose:
                       print "\nThe Logging Node's response:"
                       print response.status, response.reason
                LOGGER.info("Log node response to alert: {0}".format(response.status))
            except:
                exctype, value = sys.exc_info()[:2]
                if verbose:
                    print "Alert " + currFile + "not being sent due  to error " + str(e)
        if rate > 0:
            end = current_milli_time()
            if verbose:
                print "Average time between alerts " +str((end-start)/iteration)

    print good_alerts


if __name__ == '__main__':
    parser = OptionParser(usage="Usage: python htSender.py -l <IP Address>")
    parser.add_option ("-l", "--log-iq", dest='logiq', help="IP address of the LOG-IQ")
    parser.add_option ("-p", "--path", dest="path", help="Absolute path upto data directory containing alerts", default="./data")
    parser.add_option ("-v", "--verbose", dest='verbose', help="Enable logging during alert sending", action='store_true')
    parser.add_option ("-P", "--protocol", dest='protocol', help="Protocol to be used for sending alerts (http/https)", 
                       default="http")
    parser.add_option ("-t", "--tcp-port", dest="port", help="TCP port to be used for connection, only needed for HTTP", default=8008)
    parser.add_option ("-r", "--rate", dest="rate", help="desired alert send rate per second")
    parser.add_option ("-R", "--rate-file", dest="ratefile", help="path to a file with desired send-APS rate")
    parser.add_option ("-u", "--users", dest="totalThreads", help="Number of simultaneous users", default=1)
    parser.add_option ("-U", "--users-file", dest="threadsfile", help="path to a file with the Number of simultaneous users")
    parser.add_option ("-f", "--fps-path", dest="fps_path", help="'Alert Path' setting for FPS", default="/rstats")
    
    if len(sys.argv) < 2:
       parser.error("Insufficient arguments - please use -l to provide the IP address for the logging node")
       sys.exit(1)
    (options, args) = parser.parse_args()
    verbose = False
    SERVER = options.logiq
    path_to_alert_files_folder = options.path
    if (options.threadsfile):
        tFile = open(options.threadsfile, 'r')
        totalThreads = int(tFile.read())
        if (totalThreads <= 0):
            totalThreads = 1
    else:
        totalThreads = int(options.totalThreads)

    if (options.verbose):
       verbose = options.verbose
    if (options.protocol):
       proto = options.protocol
    if (options.port):
       port = options.port
    alert_rate=0
    if (options.ratefile):
       rateFile = open(options.ratefile, 'r')
       alert_rate = int(rateFile.read())
       if (alert_rate == 0):
          # message from file - just sleep and exit
          time.sleep(10)
          sys.exit(0)
    elif (options.rate):
       alert_rate = float(options.rate)

    # Now send your alerts
    mypath = "{0}/".format(path_to_alert_files_folder)
    threads = []
    print 'Simulating {0} users'.format(totalThreads )
    for itr in range(0, totalThreads):
       threads.append(Thread(target=send_alerts, kwargs={'mypath':mypath, 'server':SERVER, 'rate':alert_rate, 'fpspath':options.fps_path, 'tcp_port':port, 'verbose':verbose, 'protocol':proto} ))
    for t in threads:
       t.start()
    for t in threads:
       while (t.isAlive()):
           t.join(5)

    PrintLat()
