#!/usr/bin/python

import csv, json, re, logging
from datetime import datetime, timedelta
from copy import deepcopy
from bucket import Bucket
from transaction import Transaction

logging.basicConfig(filename="savings.log",
                    format="[%(asctime)s] [%(levelname)-7s] %(message)s",
                    level=logging.DEBUG)

BUCKET_CONFIG = 'buckets.json'
CREDIT_CARD_XACTIONS = 'cc-export-2018-12-26.csv'
OLD_SAVINGS = 'savings.csv'
NEW_SAVINGS = 'savings_update.csv'

class Savings(object):
    def __init__(self, bkts=BUCKET_CONFIG, sv=OLD_SAVINGS, cc=CREDIT_CARD_XACTIONS, nsv=NEW_SAVINGS):
        logging.info("Start - Savings Account Tally.")
        self.tags2buckets = {}
        self.titles2buckets = {} 
        self.ordered_titles = [] 
        self.transactions = [] 
        self.snapshots = {}         # date -> Savings
        self.st_total = 0

        self.init_buckets(file=bkts)
        self.load_sv(file=sv)
        self.load_cc(file=cc)
        self.csv_out(file=nsv)
        logging.info("Done - Savings Account Tally.")

    def load_sv_row(self, row, headers=[]):
        # assign headers to each value in this row
        head_pos = 0
        goodies = {}
        for header in headers:
            goodies[header] = row[head_pos]
            head_pos += 1

        # initialize all buckets with the values in this row
        for header in goodies:
            if header and goodies[header] and header in self.titles2buckets.keys():
                self.titles2buckets[header].total = goodies[header]

    def load_sv(self, file=""):
        in_data = False
        headers = []

        logging.info("Parsing Savings-Account summary, '%s'.", file)
        with open(file) as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if in_data:
                    self.load_sv_row(row, headers)

                if 'Date' in row:
                    in_data = True
                    headers = row

        for head in self.titles2buckets.keys():
            self.st_total += self.titles2buckets[head].total

        logging.info("Done parsing '%s'.", file)

    def load_cc_row(self, row, headers=[]):
        interesting = ['Date', 'Payee', 'Category', 'Tags', 'Amount']

        # put field names together with fields in a dictionary
        head_pos = 0
        goodies = {}
        for header in headers:
            if header in interesting:
                goodies[header] = row[head_pos]
            head_pos += 1

        # if we got a "Date" value, add this entry to a bucket with a matching tag
        if goodies and goodies["Date"]:
            trans = Transaction(date=goodies["Date"], category=goodies["Category"],
                                payee=goodies["Payee"], tags=goodies["Tags"],
                                amount=goodies["Amount"])
            entry = Bucket(tags=[trans.category, trans.tags, trans.payee], total=trans.amount)
            dest_bkt = None
            if entry.tags and "Savings" in entry.tags:
                # use tag matching to find the target bucket
                for mytag in entry.tags:
                    if mytag in self.tags2buckets.keys():
                        dest_bkt = self.tags2buckets[mytag]

                # it's in savings, but has no matching tag - log it
                if not dest_bkt:
                    logging.warn("Unmatched tags '%s'.", ", ".join(entry.tags))
                    logging.warn("Adding to Slush:  '%s, %s on %s'.", 
                        trans.payee, trans.amount, trans.date)
                    dest_bkt = self.titles2buckets["Slush"]

            if dest_bkt:
                trans.dest_bucket = dest_bkt
                self.transactions.append(trans)

    def load_cc(self, file=CREDIT_CARD_XACTIONS):
        in_data = False
        headers = []
        data_ct = 0

        logging.info("Parsing credit card, '%s'.", file)

        # load up all the transaction data
        with open(file) as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if in_data:
                    self.load_cc_row(row, headers)
                    data_ct += 1

                if 'Date' in row:
                    in_data = True
                    headers = row
                if 'Total Inflows:' in row:
                    in_data = False 

        # put the transactions in the buckets, ordered by transaction date
        for xact in sorted(self.transactions, key=lambda k: k.date):
            bkt = xact.dest_bucket
            self.titles2buckets[bkt.title] = bkt.transact(xact)
            self.snapshot(xact.date, xact.payee, xact.amount)

        logging.info("Done parsing credit card, %d records.", data_ct - 1)

    def init_buckets(self, file=""):
        buckets = []

        logging.info("Parsing bucket-config file, '%s'.", file)
        with open(file) as json_data:
            buckets = json.load(json_data) 

        for bucket in buckets:
            bkt = Bucket(title=bucket['title'], order=bucket['order'], weight=bucket['weight'], tags=bucket['tags'])
            self.titles2buckets[bucket['title']] = bkt
            for tag in bkt.tags:
                if tag in self.tags2buckets.keys():
                    logging.warning("Dupe tag: '%s' in config record '%s, %s'.", tag, 
                                    bkt.title, bkt.weight)
                else:
                    self.tags2buckets[tag] = bkt

        for bucket in sorted(buckets, key=lambda k: k['order']):
            self.ordered_titles.append(bucket['title'])

        logging.info("Done parsing bucket-config file, %s buckets.",
            len(self.titles2buckets.keys()))

    def snapshot(self, date, payee, amount):
        # make the new date unique
        if self.snapshots:
            while date in self.snapshots.keys():
                date+=timedelta(seconds=1) # add a second to make it unique

        # make deep copy of buckets, put in dictionary with date key
        self.snapshots[date] = {}
        self.snapshots[date]["buckets"] = deepcopy(self.titles2buckets)
        self.snapshots[date]["Payee"] = payee
        self.snapshots[date]["Amount"] = amount

    def csv_out(self, file):
        with open(file, 'w') as csvfile:
            # write out bucket titles
            titles = ['Date', 'Payee', 'Amount']
            titles.extend(self.ordered_titles)
            for title in titles:
                csvfile.write(title + ", ")
            csvfile.write("\n")

            # write one row per snapshot
            for dt in sorted(self.snapshots.keys()):
                snap = self.snapshots[dt]
                csvfile.write(str(dt) + ", ")
                for intro in [snap["Payee"], snap["Amount"]]:
                    csvfile.write(str(intro) + ", ")

                for title in self.ordered_titles:
                    csvfile.write(str(snap["buckets"][title].total) + ", ")
                csvfile.write("\n")
            csvfile.write("\n")

    def __str__(self):
        ret = "Start:  " + str(self.st_total) + "\n\n"
        total = 0
        for title in self.titles2buckets.keys():
            money_chg = self.titles2buckets[title].total
            ret += title + ":  " + str(money_chg) + "\n"
            total += money_chg

        ret += "\nTotal: " + str(total) + "\n"
        ret += "Snaps: " + str(len(self.snapshots)) + "\n"

        return ret

if __name__ == "__main__":
    sv = Savings()
    print sv
