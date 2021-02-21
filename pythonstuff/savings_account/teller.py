#!/usr/bin/python

import re, logging, os
from transaction import Transaction
from sub_transaction import SubTransaction
from starter_transaction import Starter_Transaction
from buckets import Buckets
from bucket import Bucket
from xaction_csv import XactionCsv
from usd import USD

logging.basicConfig(filename="/var/log/savings/savings.log",
        format="[%(asctime)s] [%(levelname)-7s] [%(filename)s:%(lineno)d] %(message)s",
        level=logging.DEBUG)
log = logging.getLogger(__name__)

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
        if not self.transaction.buckets_filled:
            # this amount didn't default to any bucket set - ask the user
            self._loop_buckets()

    # process a bank statement with the user
    # return a tuple: the list of transactions, and the statement form (XactionCsv)
    def process_statement(self, csv_file="", st_type="Credit Card", start="1970-01-01", end="2500-12-31"):
        log.info("%s processing bank-statement file, %s." % (self.name, csv_file))
        transactions = []
        sttmt = None

        if not csv_file:
            return transactions, sttmt

        # parse the CSV File
        sttmt = XactionCsv(csv_file, start, end)

        # convert the rows of normalized dictionaries to transactions
        sub_owner = None    # latest sub-transaction owner to be found
        sid = Teller("Sid") # ask a new Teller to do this
        for xact_data in sttmt.raw_transactions:
            sid.process_transaction(st_type, xact_data)
            curr_trans = sid.transaction

            # re-link transactions with their sub-transactions
            if (curr_trans.is_owner):
                # this holds subs - just hold onto it
                sub_owner = curr_trans
            elif (curr_trans.is_sub and (sub_owner != None)):
                # this is a sub, and we previously held onto an owner
                next_sub = SubTransaction(curr_trans.payer, curr_trans.xact_data, sub_owner)  # make it a sub now
                sub_owner.extend_subs([next_sub])   # add this sub to the owner
            else:
                # this is not a sub or an owner
                if sub_owner and sub_owner.subs:
                    transactions.append(sub_owner)
                    sub_owner = None
                transactions.append(curr_trans)

        # if a sub_owner is at the end, add it
        if sub_owner and sub_owner.subs:
            transactions.append(sub_owner)
            sub_owner = None

        log.info("%s done processing %s." % (self.name, csv_file))
        return transactions, sttmt

    def _loop_buckets(self):
        t = self.transaction
        log.info("Asking user which buckets get $%s." % t.init_total)
        not_done = 1
        while (not_done):
            still_needed = t.init_total - t.total
            if abs(still_needed) <= 0.01:
                not_done = 0
                print "\nFinal:"
                print self._interactive_buckets_str(0.0)
            else:
                self._query_user(still_needed)

    def _divide_evenly(self, still_needed=0.0, user_words=[]):
        if not still_needed:
            return
        amt = still_needed
        if len(user_words):
            dollars = user_words.pop(0)
            if re.search(r'-?^\d+(\.\d+)?$', dollars):
                amt = USD(dollars)
            else:
                log.error("Unclear amount for -d; expected dollar amount, got '%s'" % dollars)
        if amt:
            ave_xact = Starter_Transaction("Savings", "", amt)
            self.transaction.buckets += ave_xact.buckets

    def _credit_card_breakdown(self, cmd="", still_needed=0.0, user_words=[]):
        if not (cmd and still_needed and user_words):
            return

        # read what the user wants
        csv, start, end = self._parse_cc_instructions(user_words)

        # Process the credit-card transactions. Make them subtransactions of the Teller's transaction.
        log.info("Processing the new credit-card statement, %s." % csv)
        cc_trans, _ = self.process_statement(csv, start=start, end=end)
        num_subs = self._demote_cc_transactions(cc_trans)
        log.info("Done processing %d credit-card transactions." % num_subs)

    def _parse_cc_instructions(self, user_words=""):
        if not user_words:
            return
        
        csv = user_words.pop(0)
        if not os.path.exists(csv):
            print "No such file, %s." % csv
            return
        start = "1970-01-01"    # default: start at dawn of time
        end = "2500-12-31"      # default: end at end of days
        if user_words:
            user_words.pop(0)
        if user_words:          # if there are words left, take next 2
            start = user_words.pop(0)
            user_words.pop(0)
        if user_words:          # if there are still words left, take next
            end = user_words.pop(0)

        return csv, start, end

    def _demote_cc_transactions(self, cc_trans):
        cc_subs = []
        for sub in cc_trans:
            my_sub = SubTransaction(sub.payer, sub.xact_data, self.transaction)
            my_sub.buckets = sub.buckets
            cc_subs.append(my_sub)
        self.transaction.extend_subs(cc_subs)
        return len(cc_subs)

    def _deposit_to_one_bucket(self, cmd="", still_needed=0.0, user_words=[]):
        if not (cmd and still_needed and user_words):
            return

        # find the bucket and money, and add the money to the bucket
        bkt = self.transaction.buckets.find(int(cmd))
        if not bkt:
            return
        amt = user_words.pop(0)
        if re.search(r'^a$', amt, re.IGNORECASE):
            amt = still_needed
        elif re.search(r'^-?\d+(\.\d+)?$', amt):
            amt = USD(amt)
        else:
            log.error("Bad amount for bucket %s; expected 'a' or dollar amount, got '%s'" % (bkt.title, amt))
            return
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
            comment += " (%s)" % deposit
            bkt.add_comment(comment)
        else:
            log.error("Unclear - is this a comment? Expected '-c', got '%s'" % arg)
            print "Unclear comment, dropped: %s." % arg

    def _query_user(self, still_needed):
        print self._interactive_xaction_str()
        print self._interactive_buckets_str(still_needed)
        raw_answer = raw_input("Enter the bucket and amount, '?' for help: ")

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
            self._divide_evenly(still_needed, user_words)
        elif re.search(r'^c$', cmd):
            self._credit_card_breakdown(cmd, still_needed, user_words)
        elif re.search(r'^\d+$', cmd):
            self._deposit_to_one_bucket(cmd, still_needed, user_words)
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
        ret += "\tCredit card - break down:            c <path-to-cc.csv-file> range <start-date> - <end-date>\n"
        ret += "\tNext (add the rest to the default):  n\n"
        ret += "\tPrint this help:                     ?\n"
        return ret

    def _interactive_xaction_str(self):
        # summarize the transaction info
        t = self.transaction
        ret = "On " + str(t.date_time) + ", '" + str(t.init_total) + "' transferred from '" + t.payer + "' to '" + t.payee + "'"
        if t.tags:
            ret += "\n\tWith these tags: " + t.tags
        if t.category:
            ret += "\n\tCategory: " + t.category
        if t.note:
            ret += "\n\tNote:  " + t.note

        return ret

    def _interactive_buckets_str(self, still_needed=0.0):
        # show the transaction's buckets
        t = self.transaction
        ret = "\n\nBuckets:\n"
        ret += t.buckets.show()
        ret += "\nRemaining: %s\n\n" % still_needed

        return ret

    def __str__(self):
        return "Hello, my name is %s.  How can I help you?" % self.name


if __name__ == "__main__":
    sheila = Teller("Shiela")
    print sheila

    sample = {"Date": "11/12/1965", "Amount": 250.00, "Payee": "savings"}
    sheila.process_transaction(source_account="savings", xact_data=sample)
    sample = {"Date": "9/4/1965", "Amount": 2345.00, "Payee": "savings"}
    sheila.process_transaction(source_account="savings", xact_data=sample)
    sample = {"Date": "5/6/1995", "Amount": 1000.00, "Payee": "savings"}
    sheila.process_transaction(source_account="savings", xact_data=sample)
    sample = {"Date": "6/5/1998", "Amount": 1950.00, "Payee": "savings"}
    sheila.process_transaction(source_account="savings", xact_data=sample)
