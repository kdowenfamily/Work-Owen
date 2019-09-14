#!/usr/bin/python

import csv, json, re, logging, os
from dateutil.parser import parse
from transaction_template import Transaction_Template
from transaction import Transaction
from start_transaction import Start_Transaction
from buckets import Buckets

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

    def _deposit_to_one_bucket(self, bkt=None, t=None, still_needed=0.0, user_words=[]):
        if not (bkt and t and still_needed and user_words):
            return (user_words, 0)
        amt = user_words.pop(0)
        if re.search(r'^a$', amt, re.IGNORECASE):
            amt = still_needed
        elif re.search(r'^-?\d+(\.\d+)?$', amt):
            amt = float(amt)
        else:
            log.error("Bad amount for bucket %s; expected 'a' or dollar amount, got '%s'" % (bkt.title, amt))
            return user_words
        bkt.total += amt
        return (user_words, amt)

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
        if not user_words:
            print self._help_str()
            return

        # nibble off and assess the first word
        cmd = user_words.pop(0)
        t = self.transaction
        if re.search(r'^n$', cmd, re.IGNORECASE):
            if abs(still_needed) >= 0.01:
                t.buckets.get_default().total += still_needed
        elif re.search(r'^\?$', cmd):
            print self._help_str()
        elif re.search(r'^d$', cmd, re.IGNORECASE):
            self._divide_evenly(t, still_needed, user_words)
        elif re.search(r'^\d+$', cmd):
            bkt = t.buckets.find(int(cmd))
            user_words, dep = self._deposit_to_one_bucket(bkt, t, still_needed, user_words)
            if user_words and len(user_words) > 1:
                self._record_comment(bkt, user_words, dep)
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
