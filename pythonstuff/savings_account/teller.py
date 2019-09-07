#!/usr/bin/python

import csv, json, re, logging, os
from dateutil.parser import parse
from transaction_template import Transaction_Template
from transaction import Transaction
from start_transaction import Start_Transaction
from buckets import Buckets

PAYCHECK_DIR = "./transfers/"

logging.basicConfig(filename="savings.log",
                    format="[%(asctime)s] [%(levelname)-7s] %(message)s",
                    level=logging.DEBUG)

# Represents a bank teller, to ask the user questions and alter transactions
# as needed.
class Teller(object):
    def __init__(self, name="Kathy"):
        logging.info("Creating teller.")
        self.transaction = None
        self.name = name
        logging.info("Done creating teller.")

    # process one transaction with the user
    def process_transaction(self, source_account="", xact_data={}):
        self.transaction = Transaction(source_account, xact_data)
        self._divide_into_buckets(xact_data)
        self.transaction.reconcile_total()
        return self.transaction

    # divide the total into buckets as needed
    def _divide_into_buckets(self, xact_data={}):
        t = self.transaction
        if t.init_total in Transaction.total2trTemplate.keys():
            # this looks like a paycheck, or similar
            t_tmplt = Transaction.total2trTemplate[t.init_total]
            t.buckets += t_tmplt.buckets
            t.title = t_tmplt.title
        elif ('buckets' in xact_data.keys()):
            # no asking - this is final
            t.buckets += Buckets(xact_data['buckets'])
        else:
            # this could be anything - ask the user
            self._loop_buckets()

    def _loop_buckets(self):
        t = self.transaction
        not_done = 1
        while (not_done):
            total_so_far = t.buckets.total
            total_needed = t.init_total
            still_needed = total_needed - total_so_far

            if abs(still_needed) <= 0.01:
                not_done = 0
                print "\nFinal:"
                print self._interactive_buckets_str(0.0)
            else:
                self._query_user(still_needed)

    def _query_user(self, still_needed):
        print self._interactive_xaction_str()
        print self._interactive_buckets_str(still_needed)
        bucket_n_amt = raw_input("Enter the bucket and amount, 'q' to quit: ")
        t = self.transaction
        if bucket_n_amt == 'n':
            if abs(still_needed) >= 0.01:
                t.buckets.get_default().total += still_needed
        elif (re.search("^(\d+)\s*a$", bucket_n_amt)):
            stuff = re.search("^(\d+)\s*a$", bucket_n_amt)
            bkt_num = int(stuff.group(1))
            bkt = t.buckets.find(number = bkt_num)
            bkt.total += still_needed
        elif (re.search("^D\s*([\d\.]+)\s*$", bucket_n_amt)):
            # divide the amount evenly, by the budget
            stuff = re.search("^D\s*([\d\.]+)\s*$", bucket_n_amt)
            amt = float(stuff.group(1))
            ave_xact = Start_Transaction("Savings", "", amt)
            t.buckets += ave_xact.buckets
        elif (re.search("^D$", bucket_n_amt)):
            # divide up all that's left evenly
            ave_xact = Start_Transaction("Savings", "", still_needed)
            t.buckets += ave_xact.buckets
        elif (not re.search("^\d+\s+-?\d+(\.\d+)?$", bucket_n_amt)):
            print self._help_str()
        elif (re.search("\?", bucket_n_amt)):
            print self._help_str()
        else:
            (bkt_num, amt) = bucket_n_amt.split()
            bkt = t.buckets.find(bkt_num)
            bkt.total += float(amt)

    def _help_str(self):
        # show the options
        ret = "\n\nPlease enter in one of these formats:\n"
        ret += "\tAdd <amount> to a bucket:            <bucket-number> <amount>\n"
        ret += "\tAdd all the rest to a bucket:        <bucket-number> a\n"
        ret += "\tDivide <amount> based on budget:     D <amount>\n"
        ret += "\tDivide the rest based on budget:     D\n"
        ret += "\tNext (add the rest to the default):  n\n"
        ret += "\tPrint this help:                     ?\n"
        return ret

    def _interactive_xaction_str(self):
        # show the transaction info
        t = self.transaction
        ret = "On " + str(t.date_time) + ", '" + str(t.init_total) + "' transferred from '" + t.payer + "' to '" + t.payee + "'"
        if t.tags:
            ret += "\n\tWith these tags: " + t.tags
        if t.note:
            ret += "\n\tNote:  " + t.note

        return ret

    def _interactive_buckets_str(self, still_needed=0.0):
        # show the transaction's buckets
        t = self.transaction
        ret = "\n\nBuckets:\n"
        ret += t.buckets.show()
        ret += "\nRemaining: %3.2f\n\n" % still_needed

        return ret

    def __str__(self):
        return "Hello, my name is %s.  How can I help you?" % self.name


if __name__ == "__main__":
    sheila = Teller("Shiela")
    print sheila

    sample = {"Date": "11/12/1965", "Amount": 250, "Payee": "savings"}
    xact = sheila.process_transaction(source_account="savings", xact_data=sample)
    sample = {"Date": "9/4/1965", "Amount": 2345, "Payee": "savings"}
    xact = sheila.process_transaction(source_account="savings", xact_data=sample)
    sample = {"Date": "5/6/1995", "Amount": 1000, "Payee": "savings"}
    xact = sheila.process_transaction(source_account="savings", xact_data=sample)
    sample = {"Date": "6/5/1998", "Amount": 1950, "Payee": "savings"}
    xact = sheila.process_transaction(source_account="savings", xact_data=sample)
