#!/usr/bin/python

import csv, json, re, logging, argparse
from dateutil.parser import parse
from buckets import Buckets
from transaction import Transaction
from xaction_csv import XactionCsv

logging.basicConfig(filename="savings.log",
                    format="[%(asctime)s] [%(levelname)-7s] %(message)s",
                    level=logging.DEBUG)

# Represents the savings account.
class Savings(object):
    def __init__(self, name="Savings"):
        logging.info("Creating savings account, %s." % name)
        self.name = name
        self.total = 0.0
        self.buckets = None
        self.transactions = []
        self.snapshots = []
        logging.info("Finished savings account, %s." % name)

    def read_history(self, savings_record=''):
        # seed the buckets and the total with the older savings-account record
        savings_now = XactionCsv(savings_record)
        self.transactions.extend(savings_now.transactions)
        self._sum_transactions()

    def read_latest_transactions(self, transaction_files=[]):
        # feed in all the latest transaction files from Quicken
        for csv_file in transaction_files:
            new_xactions = XactionCsv(csv_file)
            self.transactions.extend(new_xactions.transactions)
        self._sum_transactions()

    def _sum_transactions(self):
        self.buckets = Buckets.from_file(Buckets.BUCKETS_FILE)
        for xact in self.transactions:
            self.buckets += xact.buckets
        self.total = self.buckets.get_total()

    def csv_out(self):
        # output the full history in CSV format
        for xaction in sorted(self.transactions, key=lambda k: k.date_time):
            print xaction

    def __str__(self):
        ret = ""

        ret += "Name:  %s\n" % self.name
        ret += "Total: %5.2f\n" % self.total
        ret += "\n" + self.buckets.show() + "\n"

        return ret

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', '-n', help='Name for the Savings account', default='Savings')
    parser.add_argument('--savings', '-s', help='Path to the current spreadsheed for the Savings account', default='')
    parser.add_argument('--quicken', '-q', nargs='*', help='Path(s) to Quicken transaction files', default='')
    args = parser.parse_args()

    sv = Savings(args.name)
    sv.read_history(args.savings)
    sv.read_latest_transactions(args.quicken)

    print
    sv.csv_out()
    print
    print sv
