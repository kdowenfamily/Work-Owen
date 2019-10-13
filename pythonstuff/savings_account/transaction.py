#!/usr/bin/python

import csv, json, re, logging, os
from dateutil.parser import parse
from datetime import timedelta
from copy import deepcopy
from transaction_template import Transaction_Template
from buckets import Buckets

logging.basicConfig(filename="savings.log",
        format="[%(asctime)s] [%(levelname)-7s] [%(filename)s:%(lineno)d] %(message)s",
        level=logging.DEBUG)
log = logging.getLogger(__name__)

PAYCHECK_DIR = "./transfers/"

# Represents one transfer, deposit, or payment.  This corresponds to 
# one line in a Credit-Card or Savings-Account report.
class Transaction(object):
    total2trTemplate = {}
    masterPaychecks = []

    # Load up all paychecks into memory, using their totals as keys
    @classmethod
    def get_regular_xfers(cls, paychk_dir=PAYCHECK_DIR):
        log.info("Parsing the paycheck breakdowns in %s." % paychk_dir)
        for fl in os.listdir(paychk_dir):
            xact = os.path.join(paychk_dir, fl)
            if not (os.path.isfile(xact) and re.search(r'\.json\s*$', xact)):
                continue
            x_template = Transaction_Template(xact)
            cls.total2trTemplate[x_template.buckets.get_total()] = x_template
            if not (re.search(r'\d\d\d\d\.', xact)):
                cls.masterPaychecks.append(x_template)
        log.info("Done parsing the paycheck breakdowns.")

    def __init__(self, source_account="", xact_data={}):
        # make map of totals to 'template' transactions 
        # (eg, if total is YYY.ZZ, it must be Dan's paycheck, if it's AAA.BB, it's Kathy's)
        if not Transaction.total2trTemplate:
            Transaction.get_regular_xfers()

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
        self.init_total = xact_data.get('Amount', 0.0)
        self.payer = source_account
        self.payee = xact_data.get('Payee', "")
        self.tags = xact_data.get('Tags', "")
        self.note = xact_data.get('Memo/Notes', "")
        self.title = self.payee if self.payee else self.note
        self.buckets = Buckets.from_file(Buckets.BUCKETS_FILE)
        self.subs = [] # If the transaction has sub-transactions, put them here

        log.info("Done setting up transaction: %s, %3.2f (from %s to %s)." % (self.date_time, self.init_total, self.payer, self.payee) )

    @property
    def total(self):
        return self.buckets.total

    @property
    def description(self):
        ret = self.title
        if self.buckets.notes:
            ret += " - " + self.buckets.notes
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

    # if the total in the file is different from the bucket total, add the diff to the default bucket
    def reconcile_total(self):
        if not (self.init_total and (self.init_total != self.total)):
            return
        curr = "%.2f" % self.init_total
        future = "%.2f" % self.total
        diff = float(curr) - float(future)
        if diff:
            log.error("Original total: %.2f; new total: %.2f" % (self.init_total, self.total))
            def_bucket = self.buckets.get_default()
            def_bucket.transact(diff)
            log.error("Added %.2f to %s" % (diff, def_bucket.title))

    # make a list of the strings we need to print out
    def list_out(self):
        rets = []
        subs = []
        if self.subs:
            for sub in self.subs:
                self.buckets -= sub.buckets
                subs.append(sub.list_out_as_sub(self.date_time))
            ret = [str(self.date_time), self.description, "", str(self.total)] + self.buckets.list_out()
            rets = [ret]
            rets.extend(subs)
        else:
            ret = [str(self.date_time), self.description, "", str(self.total)] + self.buckets.list_out()
            rets = [ret]
        return rets

    # make a list of the strings we need to print out, as a sub-transaction
    def list_out_as_sub(self, date_of_master=None):
        # make temporary alterations
        otitle = self.title
        self.title = "- %s (%s)" % (self.title, str(self.date_time))
        odate = self.date_time
        self.date_time = date_of_master + timedelta(hours=1)
        ret = [str(self.date_time), self.description, "", str(self.total)] + self.buckets.list_out()

        # undo the alterations, in case we need to do this again
        self.title = otitle
        self.date_time = odate

        return ret

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
