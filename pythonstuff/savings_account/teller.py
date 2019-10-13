#!/usr/bin/python

import csv, json, re, logging, os
from dateutil.parser import parse
from copy import deepcopy
from transaction import Transaction
from transaction_template import Transaction_Template
from start_transaction import Start_Transaction
from buckets import Buckets
from xaction_csv import XactionCsv

logging.basicConfig(filename="savings.log",
        format="[%(asctime)s] [%(levelname)-7s] [%(filename)s:%(lineno)d] %(message)s",
        level=logging.DEBUG)
log = logging.getLogger(__name__)

PAYCHECK_DIR = "./transfers/"

# Represents a bank teller, to ask the user questions and alter transactions
# as needed.
class Teller(object):
    def __init__(self, name="Kathy"):
        log.info("Creating teller, %s." % name)
        self.transaction = None
        self.name = name
        log.info("Done creating teller.")

    # process one transaction with the user
    def process_transaction(self, source_account="", xact_data={}):
        self.transaction = Transaction(source_account, xact_data)
        self._divide_into_buckets(xact_data)
        self.transaction.reconcile_total()
        return self.transaction

    # process a bank statement with the user
    # return a tuple: the list of transactions, and the statement form (XactionCsv)
    def process_statement(self, csv_file="", st_type="Credit Card"):
        log.info("Processing bank-statement file, %s." % csv_file)
        transactions = []
        sttmt = None

        if csv_file:
            # parse the CSV File
            sttmt = XactionCsv(csv_file)

            # convert the rows of normalized dictionaries to transactions
            sid = Teller("Sid") # ask a new Teller to do this
            for xact_data in sttmt.raw_transactions:
                transactions.append(sid.process_transaction(st_type, xact_data))

        return transactions, sttmt

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

    def _divide_evenly(self, t=None, still_needed=0.0, user_words=[]):
        if not (t and still_needed):
            return
        amt = still_needed
        if len(user_words):
            dollars = user_words.pop(0)
            if re.search(r'-?^\d+(\.\d+)?$', dollars):
                amt = float(dollars)
            else:
                log.error("Unclear amount for -d; expected dollar amount, got '%s'" % dollars)
        if amt:
            ave_xact = Start_Transaction("Savings", "", amt)
            t.buckets += ave_xact.buckets

    def _credit_card_breakdown(self, cmd="", t=None, still_needed=0.0, user_words=[]):
        if not (cmd and t and still_needed and user_words):
            return []

        # read what the user wants
        csv = user_words.pop(0)
        if user_words:
            _ = user_words.pop(0)
            start = user_words.pop(0)
            _ = user_words.pop(0)
            end = user_words.pop(0)

        # Process the credit-card transactions. TODO - use start and end as a date range
        print "Passing this off to another teller to process the credit card."
        t.subs, _ = self.process_statement(csv)
        print "Done processing %d credit-card transactions." % len(t.subs)

    def _deposit_to_one_bucket(self, cmd="", t=None, still_needed=0.0, user_words=[]):
        if not (cmd and t and still_needed and user_words):
            return (user_words, 0)

        # find the bucket and money, and add the money to the bucket
        bkt = t.buckets.find(int(cmd))
        if not bkt: return
        amt = user_words.pop(0)
        if re.search(r'^a$', amt, re.IGNORECASE):
            amt = still_needed
        elif re.search(r'^-?\d+(\.\d+)?$', amt):
            amt = float(amt)
        else:
            log.error("Bad amount for bucket %s; expected 'a' or dollar amount, got '%s'" % (bkt.title, amt))
            return user_words
        bkt.total += amt

        # record any comment
        if user_words and len(user_words) > 1:
            self._record_comment(bkt, user_words, amt)

    def _record_comment(self, bkt=None, user_words=[], deposit=0.0):
        if not (bkt and user_words):
            return
        arg = user_words.pop(0)
        if re.search(r'^-c$', arg, re.IGNORECASE):
            comment = " ".join(user_words)
            comment += " (%.2f)" % deposit
            bkt.add_comment(comment)
        else:
            log.error("Unclear - is this a comment? Expected '-c', got '%s'" % arg)

    def _query_user(self, still_needed):
        print self._interactive_xaction_str()
        print self._interactive_buckets_str(still_needed)
        raw_answer = raw_input("Enter the bucket and amount, 'n' for next: ")

        # split up the answer
        raw_answer.strip()
        user_words = raw_answer.split()

        # nibble off and assess the first word
        cmd = ""
        if user_words:
            cmd = user_words.pop(0)
        t = self.transaction
        if re.search(r'^n$', cmd, re.IGNORECASE):
            if abs(still_needed) >= 0.01:
                t.buckets.get_default().total += still_needed
        elif re.search(r'^d$', cmd, re.IGNORECASE):
            self._divide_evenly(t, still_needed, user_words)
        elif re.search(r'^c$', cmd):
            self._credit_card_breakdown(cmd, t, still_needed, user_words)
        elif re.search(r'^\d+$', cmd):
            self._deposit_to_one_bucket(cmd, t, still_needed, user_words)
        else:
            print self._help_str()

    def _help_str(self):
        # show the options
        ret = "\n\nPlease enter in one of these formats:\n"
        ret += "\tAdd <amount> to a bucket:            <bucket-number> <amount>\n"
        ret += "\tAdd all the rest to a bucket:        <bucket-number> a\n"
        ret += "\tEither of the above, plus comment:   <bucket-number> [a | amount] -c <comment with spaces>\n"
        ret += "\tDivide <amount> based on budget:     d <amount>\n"
        ret += "\tDivide the rest based on budget:     d\n"
        ret += "\tCredit card - break down:            c <path-to-cc.csv-file> -s <start-date> -e <end-date>\n"
        ret += "\tNext (add the rest to the default):  n\n"
        ret += "\tPrint this help:                     ?\n"
        return ret

    def _interactive_xaction_str(self):
        # summarize the transaction info
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
