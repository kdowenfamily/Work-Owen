#!/usr/bin/python3

import csv, json, re, argparse, shutil, os
import datetime
from buckets import Buckets
from teller import Teller
from manager import Manager
from transaction import Transaction
from starter_transaction import Starter_Transaction
from constants import log

TEMP_OUT_FILE = '/tmp/savings/savings.csv'
if not os.path.exists('/tmp/savings'):
    os.makedirs('/tmp/savings')
PERM_OUT_FILE = './data/private/spending.csv'

# Represents the savings account.
class Savings(object):
    def __init__(self, name="Savings"):
        log.info("Creating savings account, %s." % name)
        self.name = name
        self.buckets = Buckets.from_file(Buckets.BUCKETS_FILE)
        self.transactions = []
        self.sig2trans = {}
        self.teller = Teller()
        self.sv_expert = Teller("Susie Q")
        self.manager = Manager()
        log.info("Finished savings account, %s." % name)

    @property
    def total(self):
        return self.buckets.total

    # seed the buckets and the total from the current savings-account record
    def read_history(self, savings_record=''):
        if not savings_record:
            return
        savings_now, statement = self.sv_expert.process_statement(savings_record)
        self._extend_transactions(savings_now)

    # feed in all the new transaction files from Quicken (like savings-yyyy-mm-dd.csv)
    def read_latest_transactions(self, transaction_files=[]):
        for csv_file in transaction_files:
            new_trs, sttmnt = self.sv_expert.process_statement(csv_file)
            if ((not self.transactions) and sttmnt.start_balance):
                # no earlier savings-account spreadsheet; create a start row
                self._extend_transactions([Starter_Transaction("Savings", sttmnt.start_date, sttmnt.start_balance)])
            self._extend_transactions(new_trs)

    # let the user manually re-balance the buckets
    def rebalance(self):
        date = str(self.transactions[-1].date_time + datetime.timedelta(hours=1))
        self._extend_transactions([self.manager.play_in_vault(self.buckets, date)])

    # extend our list of transactions with some new ones
    def _extend_transactions(self, xacts=[]):
        for xact in xacts:
            self.buckets += xact.buckets
            self.sig2trans[(xact.date_time, xact.total)] = xact
        self.transactions.extend(xacts)

    # Different transactions may have different sets of buckets;
    # at the beginning of the year, you may have been saving for 
    # Little League, by mid-year, you might be saving for Christmas.
    # As transactions are read in, the master set of buckets is 
    # the union of all bucket lists (with both Little League and Xmas).
    # Go back and make all transactions have the final set of buckets.
    def equalize_transactions(self):
        zero_set = self.buckets.dupe() # make an empty set of all buckets
        for xact in self.transactions:
            xact.buckets += zero_set

    # output the full history of transactions, in CSV format
    def csv_out(self, out_file=TEMP_OUT_FILE):
        if not self.transactions:
            return
        with open (out_file, 'w') as f:
            csv_writer = csv.writer(f)
            csv_writer.writerow(self.transactions[-1].titles().split(",")) # titles
            csv_writer.writerow(["", "Running Total", "", str(self.total)] + self.buckets.list_out())
            for xaction in sorted(self.sig2trans.values(), key=lambda k: k.date_time):
                my_list = xaction.list_out()
                csv_writer.writerows(my_list)

    # make all dates progressive, so that the order in the CSV is constant
    def kragle_order(self):
        last_date = None
        delta = datetime.timedelta(seconds=0)
        for xaction in sorted(self.sig2trans.values(), key=lambda k: k.date_time):
            if xaction.date_time == last_date:
                delta += datetime.timedelta(seconds=1)
                xaction.date_time += delta
            else:
                delta = datetime.timedelta(seconds=0)
                last_date = xaction.date_time

    def __str__(self):
        ret = "Name:  %s\n" % self.name
        ret += "\n" + self.buckets.show() + "\n"
        return ret

    def commit(self):
        shutil.copy(TEMP_OUT_FILE, PERM_OUT_FILE)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', '-n', help='Name for the Savings account', default='Savings')
    parser.add_argument('--savings', '-s', help='Path to the current spreadsheed for the Savings account', default=PERM_OUT_FILE)
    parser.add_argument('--quicken', '-q', nargs='*', help='Path(s) to Quicken transaction files', default='')
    parser.add_argument('--outfile', '-o', help='Path for the CSV output', default=TEMP_OUT_FILE)
    parser.add_argument('--edit', '-e', help='Edit the buckets at the end - trade between them', action='store_true')
    parser.add_argument('--commit', '-c', help='Commit the changes in ' + TEMP_OUT_FILE, action='store_true')
    args = parser.parse_args()

    sv = Savings(args.name)
    if args.commit:
        sv.commit()
    sv.read_history(args.savings)
    sv.read_latest_transactions(args.quicken)
    sv.equalize_transactions()
    if args.edit:
        sv.rebalance()
    sv.kragle_order()

    print()
    sv.csv_out(args.outfile)
    print("CSV is in " + args.outfile + "\n")
    print(sv)
