#!/usr/bin/python

import csv, json, re, logging
from bucket import Bucket
from buckets import Buckets

DAN_PAYCHECK = "transfers/dan.json"
KATHY_PAYCHECK = "transfers/kathy.json"

logging.basicConfig(filename="savings.log",
                    format="[%(asctime)s] [%(levelname)-7s] %(message)s",
                    level=logging.DEBUG)

class Transaction_Template(object):
    def __init__(self, template=DAN_PAYCHECK):
        # read the JSON files and make one bucket per bucket dict
        self.payer = ""
        self.payee = ""
        self.buckets = None

        self.init_template(template)

    def init_template(self, tfile=""):
        template = {}

        logging.info("Parsing transaction-template file, '%s'.", tfile)
        try:
            with open(tfile) as json_data:
                template = json.load(json_data) 

            self.payer = template["payer"]
            self.payee = template["payee"]
            self.buckets = Buckets(template["buckets"])
        except ValueError as ve:
            logging.error("Parsing ValueError in '%s':  %s", tfile, ve)
        except:
            logging.error("Parsing error in '%s'.", tfile)


    def __str__(self):
        ret = ""

        if self.buckets:
            ret += "Payee:  " + self.payee + "\n"
            ret += "Payer:  " + self.payer + "\n"
            for title in self.buckets.ordered_titles:
                bkt = self.buckets.find(title)
                ret += bkt.title + ": "
                ret += str(bkt.total) + "\n"
            ret += "\nTotal:  " + str(self.buckets.total) + "\n"

        return ret

if __name__ == "__main__":
    tts = Transaction_Template()
    print tts
    tts = Transaction_Template(KATHY_PAYCHECK)
    print tts
