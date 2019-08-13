#!/usr/bin/python

import csv, json, re, logging
from bucket import Bucket
from buckets import Buckets

DAN_PAYCHECK = "transfers/dan.json"
DAN_PAYCHECK_2017 = "transfers/dan2017.json"
KATHY_PAYCHECK = "transfers/kathy.json"
KATHY_PAYCHECK_2017 = "transfers/kathy2017.json"

logging.basicConfig(filename="savings.log",
                    format="[%(asctime)s] [%(levelname)-7s] %(message)s",
                    level=logging.DEBUG)

class Transaction_Template(object):
    def __init__(self, template=DAN_PAYCHECK):
        # read the JSON files and make one bucket per bucket dict
        self.payer = ""
        self.payee = ""
        self.title = ""
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
            self.title = template["title"]
            self.buckets = Buckets(template["buckets"])
        except ValueError as ve:
            logging.error("Parsing ValueError in '%s':  %s", tfile, ve)
        except:
            logging.error("Parsing error in '%s'.", tfile)


    def __str__(self):
        ret = ""

        if self.buckets:
            bkt_num = 1
            values = ", ".join((self.title, str(self.buckets.get_total()),  self.payee, self.payer))
            for title in self.buckets.ordered_titles:
                bkt = self.buckets.find(number = bkt_num)
                values += ", " + str(bkt.total)
                bkt_num += 1
            ret += values + "\n"

        return ret

    def _titles(self):
        ret = ""

        if self.buckets:
            bkt_num = 1
            titles = ", ".join(("Transfer","Total","From","To"))
            for title in self.buckets.ordered_titles:
                bkt = self.buckets.find(number = bkt_num)
                titles += ", " + bkt.title
                bkt_num += 1
            ret += titles + "\n"

        return ret

    def show(self):
        ret = ""

        if self.buckets:
            bkt_num = 1
            ret += "Transfer:  " + self.title + "\n"
            ret += "Payee:     " + self.payee + "\n"
            ret += "Payer:     " + self.payer + "\n"
            for title in self.buckets.ordered_titles:
                bkt = self.buckets.find(number = bkt_num)
                ret += bkt.title + ": "
                ret += str(bkt.total) + "\n"
                bkt_num += 1
            ret += "\nTotal:  " + str(self.buckets.total) + "\n"

        return ret

if __name__ == "__main__":
    tts = Transaction_Template(DAN_PAYCHECK_2017)
    print tts._titles()
    print tts
