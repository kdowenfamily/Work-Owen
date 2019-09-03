#!/usr/bin/python

import csv, json, re, logging, os
from dateutil.parser import parse
from transaction_template import Transaction_Template
from buckets import Buckets

PAYCHECK_DIR = "./transfers/"

logging.basicConfig(filename="savings.log",
                    format="[%(asctime)s] [%(levelname)-7s] %(message)s",
                    level=logging.DEBUG)

# Represents one transfer, deposit, or payment.  This corresponds to 
# one line in a Credit-Card or Savings-Account report.
class Transaction(object):
    total2trTemplate = {}
    masterPaychecks = []

    # Load up all paychecks into memory, using their totals as keys
    @classmethod
    def get_regular_xfers(cls, paychk_dir=PAYCHECK_DIR):
        logging.info("Parsing the paycheck breakdowns in %s." % paychk_dir)
        for fl in os.listdir(paychk_dir):
            xact = os.path.join(paychk_dir, fl)
            if not (os.path.isfile(xact) and re.search(r'\.json\s*$', xact)):
                continue
            x_template = Transaction_Template(xact)
            cls.total2trTemplate[x_template.buckets.get_total()] = x_template
            if not (re.search(r'\d\d\d\d\.', xact)):
                cls.masterPaychecks.append(x_template)
        logging.info("Done parsing the paycheck breakdowns.")

    def __init__(self, source_account="", xact_data={}):
        # make map of totals to 'template' transactions 
        # (eg, if total is XXX.YY, it must be Dan's paycheck, if it's AAA.BB, it's Kathy's)
        if not Transaction.total2trTemplate:
            Transaction.get_regular_xfers()

        logging.info("Creating transaction for %s." % source_account)

        # get data from the transaction line/dictionary
        try:
            self.date_time = parse(xact_data.get('Date', ""))
        except ValueError:
            logging.error("Bad date string, %s." % xact_data.get('Date', ""))
            self.date_time = parse("1/1/2001")
        except AttributeError:
            logging.error("Bad date string, %s." % xact_data.get('Date', ""))
            self.date_time = parse("1/1/2001")
        self.init_total = xact_data.get('Amount', 0.0)
        self.payer = source_account
        self.payee = xact_data.get('Payee', "")
        self.tags = xact_data.get('Tags', "")
        self.note = xact_data.get('Memo/Notes', "")
        self.title = self.payee if self.payee else self.note
        self.buckets = Buckets.from_file(Buckets.BUCKETS_FILE)

        # divide the transaction into buckets
        self._divide_into_buckets(xact_data)

        # as verification, set the total to the bucket total
        self._reconcile_total()

        logging.info("Done creating transaction: %s, %3.2f (from %s to %s)." % (self.date_time, self.total, self.payer, self.payee) )

    @property
    def total(self):
        return self.buckets.total

    def ask(self):
        print self.interactive_xaction_str()

        # ask if user wants to break it down
        want_breakdown = raw_input("Do you want to assign (or split up) this transaction? [y/n]: ")
        if want_breakdown == 'y':
            self.loop_buckets()
        else:
            # drop it all into the default bucket
            self.buckets.get_default().total = self.total

    def loop_buckets(self):
        not_done = 1
        while (not_done):
            total_so_far = self.buckets.total
            total_needed = self.init_total
            still_needed = total_needed - total_so_far

            if abs(still_needed) <= 0.01:
                not_done = 0
            else:
                print self.interactive_buckets_str(total_so_far, still_needed)
                self._query_user(still_needed)

    def _query_user(self, still_needed):
        bucket_n_amt = raw_input("Enter the bucket and amount, 'q' to quit: ")
        if bucket_n_amt == 'q':
            if still_needed != 0.0:
                self.buckets.get_default().total += still_needed
        elif (re.search("^\d+ a$", bucket_n_amt)):
            (bkt_num, amt) = bucket_n_amt.split()
            bkt = self.buckets.find(number = bkt_num)
            bkt.total += still_needed
        elif (not re.search("^\d+ -?\d+(\.\d+)?$", bucket_n_amt)):
            print "\n\nPlease enter in this format: '<bucket-number> <amount>'."
        else:
            (bkt_num, amt) = bucket_n_amt.split()
            if abs(round(float(amt),2)) > abs(round(still_needed,2)):
                print "\n\nERROR:  %3.2f is too much.  Please enter %3.2f or less.\n\n" % (float(amt), still_needed)
                return
            bkt = self.buckets.find(number = bkt_num)
            bkt.total += float(amt)

    def interactive_xaction_str(self):
        # show the transaction info
        ret = "On " + str(self.date_time) + ", '" + str(self.init_total) + "' transferred from '" + self.payer + "' to '" + self.payee + "'"
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

    # if the total in the file is different from the bucket total, add the diff to the default bucket
    def _reconcile_total(self):
        if self.init_total and (self.init_total != self.total):
            curr = "%.2f" % self.init_total
            future = "%.2f" % self.total
            diff = float(curr) - float(future)
            if diff:
                logging.error("Original total: %.2f; new total: %.2f" % (self.init_total, self.total))
                def_bucket = self.buckets.get_default()
                def_bucket.transact(diff)
                logging.error("Added %.2f to %s" % (diff, def_bucket.title))

    # divide the total into buckets as needed
    def _divide_into_buckets(self, xact_data={}):
        if self.init_total in Transaction.total2trTemplate.keys():
            # this looks like a paycheck, or similar
            self.buckets += Transaction.total2trTemplate[self.init_total].buckets
        elif ('buckets' in xact_data.keys()):
            # no asking - this is final
            self.buckets += Buckets(xact_data['buckets'])
        else:
            # this could be anything - ask the user
            self.ask()

    # make a list of the strings we need to print out
    def list_out(self):
        return [str(self.date_time), self.title, str(self.total)] + self.buckets.list_out()

    def titles(self):
        preamble = ", ".join(("Date", "Transaction", "Total"))
        return preamble + ", " + self.buckets.titles()

    def show(self):
        return ", ".join((str(self.date_time), self.title, str(self.total)))

    def __str__(self):
        return ",".join(self.list_out())


if __name__ == "__main__":
    bkts = Buckets.from_file(Buckets.BUCKETS_FILE)

    sample = {"Date": "11/12/1965", "Amount": 250, "Payee": "savings"}
    tr1 = Transaction(source_account="checking", xact_data=sample)
    bkts += tr1.buckets
    print "\n\nTransaction (Kathy Paycheck):\n"
    print tr1.show()
    print "\nFinal Transaction Breakdown:\n"
    print tr1.buckets.show()
    print "\nBucket Breakdown:\n"
    print bkts.show()

    sample = {"Date": "9/4/1965", "Amount": 610, "Payee": "savings"}
    tr2 = Transaction(source_account="checking", xact_data=sample)
    bkts += tr2.buckets
    print "\n\nTransaction (Dan Paycheck):\n"
    print tr2.show()
    print "\nFinal Transaction Breakdown:\n"
    print tr2.buckets.show()
    print "\nBucket Breakdown:\n"
    print bkts.show()

    sample = {"Date": "7/23/19", "Amount": 2000, "Payee": "savings"}
    tr3 = Transaction(source_account="checking", xact_data=sample)
    bkts += tr3.buckets
    print "\n\nTransaction (Windfall!):\n"
    print tr3.show()
    print "\nFinal Transaction Breakdown:\n"
    print tr3.buckets.show()

    print "\nTotal Transaction Breakdown:\n"
    print bkts.show()
