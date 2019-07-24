#!/usr/bin/python

import csv, json, re, logging
from dateutil.parser import parse
from transaction_template import Transaction_Template
#from savings import Savings
from buckets import Buckets

PAYCHECKS = ["transfers/dan.json", "transfers/kathy.json"]
BUCKETS_FILE = "data/buckets.json"

logging.basicConfig(filename="savings.log",
                    format="[%(asctime)s] [%(levelname)-7s] %(message)s",
                    level=logging.DEBUG)

# Represents one transfer, deposit, or payment.  This corresponds to 
# one line in a Credit-Card or Savings-Account report.
class Transaction(object):
    total2trTemplate = {}

    # Load up all paychecks into memory, using their totals as keys
    @classmethod
    def get_regular_xfers(cls, file_paths=PAYCHECKS):
        for xact in file_paths:
            x_template = Transaction_Template(xact)
            cls.total2trTemplate[x_template.buckets.get_total()] = x_template

    # TODO - Handle past, bucketized transactions, loaded from savings-account spreadsheets.
    #        xact_data should be formatted with amount (not total), note (not transaction),
    #        and a buckets list with those titles/totals
    def __init__(self, source_account="", xact_data={}, final=False):
        # make map of totals to 'template' transactions 
        # (eg, if total is XXX.YY, it must be Dan's paycheck, if it's AAA.BB, it's Kathy's)
        if not Transaction.total2trTemplate:
            Transaction.get_regular_xfers()

        # get data from the transaction line/dictionary
        self.date_time = parse(xact_data.get('date', ""))
        self.total = xact_data.get('amount', 0.0)
        self.payer = source_account
        self.payee = xact_data.get('payee', "")
        self.tags = xact_data.get('tags', "")
        self.note = xact_data.get('note', "")
        #self.buckets = Savings.empty_buckets
        self.buckets = Buckets.from_file(BUCKETS_FILE)

        # divide the transaction into buckets
        if self.total in Transaction.total2trTemplate.keys():
            # this looks like a paycheck, or similar
            self.buckets = Transaction.total2trTemplate[self.total].buckets
        elif (final):
            # no asking - this is final
            return
        else:
            # this could be anything - ask the user
            #self.buckets = self.ask()
            self.ask()

        logging.info("Done creating transaction: %s, %3.2f (from %s to %s)." % (self.date_time, self.total, self.payer, self.payee) )

    def ask(self):
        print self.interactive_xaction_str()

        # ask if user wants to break it down
        want_breakdown = raw_input("Do you want to split up this transaction? [y/n]: ")
        if want_breakdown == 'y':
            self.loop_buckets()
        else:
            # drop it all into the default bucket
            self.buckets.get_default().total = self.total

    def loop_buckets(self):
        not_done = 1
        while (not_done):
            total_so_far = self.buckets.get_total()
            total_needed = self.total
            still_needed = total_needed - total_so_far

            if still_needed == 0.0:
                not_done = 0
            else:
                print self.interactive_buckets_str(total_so_far, still_needed)
                bucket_n_amt = raw_input("Enter the bucket and amount, or 'q' to quit: ")
                if bucket_n_amt == 'q':
                    if still_needed != 0.0:
                        self.buckets.get_default().total += still_needed
                    not_done = 0
                elif (not re.search("^\d+ \d+[\.\d+]?$", bucket_n_amt)):
                    print "\n\nPlease enter in this format: '<bucket-number> <amount>'."
                else:
                    (bkt_num, amt) = bucket_n_amt.split()
                    if round(float(amt),2) > round(still_needed,2):
                        print "\n\nERROR:  %3.2f is too much.  Please enter %3.2f or less.\n\n" % (float(amt), still_needed)
                        continue
                    bkt = self.buckets.find(number = bkt_num)
                    bkt.total += float(amt)

    def _titles(self):
        ret = ""

        for title in ("Date", "Total", "Payer", "Payee"):
            ret += title + ", "

        return ret

    def interactive_xaction_str(self):
        # show the transaction info
        ret = "On " + str(self.date_time) + ", '" + str(self.total) + "' transferred from '" + self.payer + "' to '" + self.payee + "'"
        if self.tags:
            ret += "\n\tWith these tags: " + self.tags
        if self.note:
            ret += "\n\tNote:  " + self.note

        return ret

    def interactive_buckets_str(self, total_so_far=0.0, still_needed=0.0):
        # show the transaction's buckets
        ret = "\n\nBuckets:\n"
        ret += self.buckets.show()
        ret += "\nTotal:     %3.2f" % total_so_far
        ret += "\nRemaining: %3.2f\n\n" % still_needed

        return ret

    def __str__(self):
        ret = ""

        for value in (self.date_time, self.total, self.payer, self.payee):
            ret += str(value) + ", "

        return ret

if __name__ == "__main__":
    bkts = Buckets.from_file(BUCKETS_FILE)

    sample = {"date": "11/12/1965", "amount": 190, "payee": "savings"}
    tr1 = Transaction(source_account="checking", xact_data=sample)
    print "\n\nTransaction (Kathy Paycheck):\n"
    print tr1
    print "\nFinal Transaction Breakdown:\n"
    print tr1.buckets.show()

    sample = {"date": "9/4/1965", "amount": 1525, "payee": "savings"}
    tr2 = Transaction(source_account="checking", xact_data=sample)
    print "\n\nTransaction (Dan Paycheck):\n"
    print tr2
    print "\nFinal Transaction Breakdown:\n"
    print tr2.buckets.show()

    sample = {"date": "7/23/19", "amount": 2000, "payee": "savings"}
    tr3 = Transaction(source_account="checking", xact_data=sample)
    print "\n\nTransaction (Windfall!):\n"
    print tr3
    print "\nFinal Transaction Breakdown:\n"
    print tr3.buckets.show()

    bkts += tr1.buckets
    bkts += tr2.buckets
    bkts += tr3.buckets
    print "\nTotal Transaction Breakdown:\n"
    print bkts.show()
