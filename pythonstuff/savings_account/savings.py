#!/usr/bin/python

import csv, json, re, logging, argparse
from dateutil.parser import parse
from buckets import Buckets
from transaction import Transaction
from start_transaction import Start_Transaction
from xaction_csv import XactionCsv

logging.basicConfig(filename="savings.log",
                    format="[%(asctime)s] [%(levelname)-7s] %(message)s",
                    level=logging.DEBUG)

# Represents the savings account.
class Savings(object):
    def __init__(self, name="Savings"):
        logging.info("Creating savings account, %s." % name)
        self.name = name
        self.buckets = Buckets.from_file(Buckets.BUCKETS_FILE)
        self.transactions = []
        self.snapshots = []
        logging.info("Finished savings account, %s." % name)

    @property
    def total(self):
        return self.buckets.total

    # seed the buckets and the total with the older savings-account record
    def read_history(self, savings_record=''):
        if not savings_record:
            return
        savings_now = XactionCsv(savings_record)
        self._add_transactions(savings_now.transactions)

    # feed in all the latest transaction files from Quicken
    def read_latest_transactions(self, transaction_files=[]):
        for csv_file in transaction_files:
            new_xactions = XactionCsv(csv_file)
            if ((not self.transactions) and new_xactions.start_balance):
                # no earlier savings-account spreadsheet; create a start row
                self._add_transactions([Start_Transaction("Savings", new_xactions.start_balance)])
            self._add_transactions(new_xactions.transactions)

    def _add_transactions(self, xacts=[]):
        for xact in xacts:
            self.buckets += xact.buckets
        self.transactions.extend(xacts)

    # go back and make all transactions have the final set of buckets
    def equalize_transactions(self):
        zero_set = self.buckets.dupe()
        for xact in self.transactions:
            xact.buckets += zero_set

    def _take_snapshot(self, xaction=None):
        for xaction in self.transactions:
            snapshot = {}
            snapshot["date"] = xaction.date_time
            snapshot["payer"] = xaction.payer
            snapshot["payee"] = xaction.payee
            snapshot["notes"] = xaction.notes
            snapshot["total"] = xaction.total
            snapshot["grand_total"] = self.total
            snapshot["buckets"] = self.buckets

    # output the full history of transactions, in CSV format
    def csv_out(self, out_file="/tmp/savings.csv"):
        if not self.transactions:
            return
        with open (out_file, 'wb') as f:
            csv_writer = csv.writer(f)
            csv_writer.writerow(self.transactions[-1].titles().split(","))
            csv_writer.writerow(["", "Running Total", str(self.total)] + self.buckets.list_out())
            for xaction in sorted(self.transactions, key=lambda k: k.date_time):
                csv_writer.writerow(xaction.list_out())

    def __str__(self):
        ret = "Name:  %s\n" % self.name
        ret += "\n" + self.buckets.show() + "\n"
        return ret

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', '-n', help='Name for the Savings account', default='Savings')
    parser.add_argument('--savings', '-s', help='Path to the current spreadsheed for the Savings account', default='')
    parser.add_argument('--quicken', '-q', nargs='*', help='Path(s) to Quicken transaction files', default='')
    parser.add_argument('--outfile', '-o', help='Path for the CSV output', default='/tmp/savings.csv')
    args = parser.parse_args()

    sv = Savings(args.name)
    sv.read_history(args.savings)
    sv.read_latest_transactions(args.quicken)
    sv.equalize_transactions()

    print
    sv.csv_out(args.outfile)
    print "CSV is in " + args.outfile + "\n"
    print sv
