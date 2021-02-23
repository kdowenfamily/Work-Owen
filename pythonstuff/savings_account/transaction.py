#!/usr/bin/python

import re, os
from dateutil.parser import parse
from transaction_template import Transaction_Template
from bucket import Bucket
from buckets import Buckets
from usd import USD
from constants import log

# Represents one transfer, deposit, or payment.  This corresponds to 
# one line in a Credit-Card or Savings-Account report.
class Transaction(object):
    total2trTemplate = {}
    masterPaychecks = []
    PAYCHECK_DIR = os.path.dirname(__file__) + "/budgets/private"
    OWNER_MARKER = "with subtransactions below"  # marker for the transaction in the CSV file, incase it has subs

    def __init__(self, source_account="", xact_data={}, buckets=Buckets.from_file(Buckets.BUCKETS_FILE)):
        # make map of totals to 'template' transactions 
        # (eg, if total is YYY.ZZ, it must be Dan's paycheck, if it's AAA.BB, it's Kathy's)
        if not Transaction.total2trTemplate:
            self.get_regular_xfers(Transaction.PAYCHECK_DIR)

        log.info("Creating transaction for %s." % source_account)

        # get data from the transaction line/dictionary
        try:
            self.date_time = parse(xact_data.get('Date', ""))
        except ValueError:
            log.error("Bad date string, %s." % xact_data.get('Date', ""))
            self.date_time = parse("1/1/2001")
        except AttributeError:
            log.error("Bad date string, %s." % xact_data.get('Date', ""))
            self.date_time = parse("1/1/2001")
        self.init_total = USD(xact_data.get('Amount', 0.0))
        self.payer = source_account
        self.payee = xact_data.get('Payee', "")
        self.tags = xact_data.get('Tags', "")
        self.category = xact_data.get('Category', "")
        self.note = xact_data.get('Memo/Notes', "")
        self.title = self.payee if self.payee else self.note
        self.subs = [] # If the transaction has sub-transactions, put them here
        self.xact_data = xact_data # keep the raw data around
        self.buckets = buckets.dupe()

        # try to divide the total amount given into buckets
        self.divide_total_into_buckets()

        log.info("Done setting up transaction: %s, %s (from %s to %s)." % (self.date_time, self.init_total, self.payer, self.payee) )

    # Load up all paychecks into memory, using their totals as keys
    def get_regular_xfers(self, paychk_dir=PAYCHECK_DIR):
        log.info("Parsing the paycheck breakdowns in %s." % paychk_dir)
        for fl in os.listdir(paychk_dir):
            xact = os.path.join(paychk_dir, fl)
            if not (os.path.isfile(xact) and re.search(r'\.json\s*$', xact)):
                continue
            x_template = Transaction_Template(xact)
            if not (x_template.buckets.total == 0):
                # if the total is zero, ignore it
                Transaction.total2trTemplate[str(x_template.buckets.total)] = x_template
                if not (re.search(r'\d\d\d\d\.', xact)):
                    Transaction.masterPaychecks.append(x_template)
        log.info("Done parsing the paycheck breakdowns.")

    @property
    def total(self):
        return self.buckets.total

    @property
    def description(self):
        ret = self.title
        if self.buckets.notes:
            ret += " - " + self.buckets.notes
        if self.subs and (Transaction.OWNER_MARKER not in ret):
            ret += " ("+ Transaction.OWNER_MARKER + ")"
        return ret

    @property
    def subs(self):
        return self._subs

    @subs.setter
    def subs(self, new_subs):
        self._subs = new_subs
        self.buckets = Buckets.from_file(Buckets.BUCKETS_FILE)
        for sub in new_subs:
            self.buckets += sub.buckets

    @property
    def is_sub(self):
        return (re.search(r'^\s*- ', self.note))

    @property
    def is_owner(self):
        return (Transaction.OWNER_MARKER in self.note)

    @property
    def buckets_filled(self):
        return self._buckets_filled

    @buckets_filled.setter
    def buckets_filled(self, buckets_filled):
        self._buckets_filled = buckets_filled
        if buckets_filled:
            self.reconcile_total()

    # Divide the total amount given into individual buckets.
    # Return True unless this is impossible (need user to tell us).
    def divide_total_into_buckets(self):
        self.buckets_filled = False
        
        if str(self.init_total) in Transaction.total2trTemplate.keys():
            # this looks like a paycheck, or similar
            t_tmplt = Transaction.total2trTemplate[str(self.init_total)]
            self.buckets += t_tmplt.buckets
            self.title = t_tmplt.title
            self.buckets_filled = True
        elif self.category and (self.category in self.buckets.cats2buckets):
            # Kathy left a conclusive note in Quicken - no asking
            dest_bucket = self.buckets.cats2buckets[self.category]
            new_bucket = Bucket({"title":dest_bucket.title,"total":self.xact_data["Amount"]})
            dest_bucket += new_bucket
            self.buckets_filled = True
        elif ('buckets' in self.xact_data.keys()):
            # no asking - the transaction data has buckets already, so this is final
            self.buckets += Buckets(self.xact_data['buckets'])
            self.buckets_filled = True

    # add more subs to your current set, and add their buckets to yours
    def extend_subs(self, new_subs):
        self._subs.extend(new_subs)
        for sub in new_subs:
            self.buckets += sub.buckets

    # if the total in the file is different from the bucket total, add the diff to the default bucket
    def reconcile_total(self):
        if not (self.init_total and (self.init_total != self.total)):
            return
        curr = self.init_total
        future = self.total
        diff = curr - future
        if abs(diff) >= 1:
            log.error("Original total: %s; new total: %s" % (self.init_total, self.total))
            def_bucket = self.buckets.get_default()
            def_bucket.total += diff
            log.error("Added %s to %s" % (diff, def_bucket.title))

    # make a list of the strings we need to print into the csv file
    def list_out(self):
        log.debug("Listing transaction for %s." % self.title)

        # make a list of sub transactions, if there are any
        mysubs = []
        if self.subs:
            for mysub in self.subs:
                self.buckets -= mysub.buckets
                mysubs.extend([mysub.list_out()])

        # make the csv line (date, desc, blank, total, value+) for this transaction
        ret = [str(self.date_time), self.description, "", str(self.total)] + self.buckets.list_out()
        rets = [ret]

        rets.extend(mysubs) # add the subs after the main transaction, if there are any

        return rets

    def titles(self):
        preamble = ",".join(("Date", "Transaction", "Running Total", "Total"))
        return preamble + "," + self.buckets.titles()

    def show(self):
        return ",".join((str(self.date_time), self.title, "", str(self.total)))

    def __str__(self):
        return ",".join(self.list_out())


if __name__ == "__main__":
    sample = {"Date": "11/12/1965", "Amount": 250, "Payee": "savings"}
    tr1 = Transaction(source_account="checking", xact_data=sample)
    print tr1.titles()
    print tr1.show()

    sample = {"Date": "9/4/1965", "Amount": 610, "Payee": "savings"}
    tr2 = Transaction(source_account="checking", xact_data=sample)
    print tr2.titles()
    print tr2.show()

    sample = {"Date": "7/23/19", "Amount": 2000, "Payee": "savings"}
    tr3 = Transaction(source_account="checking", xact_data=sample)
    print tr3.titles()
    print tr3.show()
