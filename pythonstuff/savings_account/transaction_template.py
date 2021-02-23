#!/usr/bin/python

import csv, json, re, os, argparse
from bucket import Bucket
from buckets import Buckets
from constants import log

# Represents a template for a regular (weekly, bi-monthly, etc.) transfer.
# This is currently used only for regular post-paycheck transfers (budgets).
class Transaction_Template(object):
    TEMPLATE_DIR = os.path.dirname(__file__) + "/budgets/private"

    def __init__(self, template=TEMPLATE_DIR + "/dan.json"):
        # read the JSON files and make one bucket per bucket dict
        self.payer = ""
        self.payee = ""
        self.title = ""
        self.per_year = 0
        self.buckets = None

        self.init_template(template)

    def init_template(self, tfile=""):
        template = {}

        log.info("Parsing transaction-template file, '%s'.", tfile)
        try:
            with open(tfile) as json_data:
                template = json.load(json_data) 

            self.payer = template["payer"]
            self.payee = template["payee"]
            self.title = template["title"]
            self.per_year = int(template["per_year"])
            self.buckets = Buckets(template["buckets"])
        except ValueError as ve:
            log.error("Parsing ValueError in '%s':  %s", tfile, ve)
        except:
            log.error("Parsing error in '%s'.", tfile)


    def __str__(self):
        ret = ""

        if self.buckets:
            bkt_num = 1
            values = ", ".join((self.title, str(self.buckets.total),  self.payee, self.payer))
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
    parser = argparse.ArgumentParser()
    parser.add_argument('--json', '-j', help='Path to JSON file', default=Transaction_Template.TEMPLATE_DIR + '/dan.json')
    args = parser.parse_args()

    tts = Transaction_Template(template=os.path.dirname(__file__) + "/" + args.json)
    print tts._titles()
    print tts
    print
    print tts.buckets.show()
