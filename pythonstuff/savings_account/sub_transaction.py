#!/usr/bin/python

import re
from datetime import timedelta
from transaction import Transaction 
from constants import log

# Represents one transfer, deposit, or payment.  This corresponds to 
# one line in a Credit-Card or Savings-Account report.
class SubTransaction(Transaction):
    def __init__(self, source_account="", xact_data={}, parent=None):
        log.info("Creating sub-transaction for %s." % source_account)
        super(SubTransaction, self).__init__(source_account, xact_data)
        self.parent = parent
        self.subdate = self.date_time
        self.subtitle = self.title
        self.title = self.title + " (sub)"
        self.date_time = self.parent.date_time
        self._increase_date()
        log.info("Done setting up sub-transaction: %s, %s (from %s to %s)." 
                % (self.date_time, self.init_total, self.payer, self.payee) )


    @property
    def subtitle(self):
        return self._subtitle

    @subtitle.setter
    def subtitle(self, title):
        self._subtitle = self._add_date(title)
        self._subtitle = self._indent(self._subtitle)

    # make the official date-time stamp (copied from the parent's date-time) unique
    def _increase_date(self):
        log.debug("fixing up the sub-transaction date")
        yr = self.subdate.year
        day = self.subdate.timetuple().tm_yday
        plus_secs = 3600 + yr + day
        self.date_time = self.date_time + timedelta(seconds=plus_secs)

    # add the actual date of the subtransaction in parens at the end of the subtitle,
    # unless already done
    def _add_date(self, title):
        if re.search(r'\(..., [\d\/]+\)$', title):
            return title
        else:
            return "%s (%s)" % (title, self.subdate.strftime("%a, %m/%d/%y"))

    # indent the subtitle with a "-" in front of it, unless already done
    def _indent(self, title):
        if re.search(r'^\s*- ', title):
            return title
        else:
            return "- " + title

    @property
    def description(self):
        ret = self.subtitle
        if self.buckets.notes:
            ret += self._indent(self.buckets.notes)
        return ret

    # make a list of the strings we need to print out, as a sub-transaction
    def list_out(self):
        log.debug("Listing sub-transaction for %s." % self.title)
        return [str(self.date_time), self.description, "", str(self.total)] + self.buckets.list_out()


if __name__ == "__main__":
    sample = {"Date": "11/12/1965", "Amount": 250, "Payee": "savings"}
    tr1 = Transaction(source_account="checking", xact_data=sample)
    print tr1.titles()
    print tr1.list_out()
    print

    sample2 = {"Date": "9/4/1965", "Amount": 610, "Payee": "Beth Israel"}
    str1 = SubTransaction(source_account="checking", xact_data=sample2, parent=tr1)

    sample3 = {"Date": "7/23/19", "Amount": 2100.00, "Payee": "savings"}
    str2 = SubTransaction(source_account="checking", xact_data=sample3, parent=tr1)

    tr1.extend_subs([str1, str2])
    print tr1.titles()
    tr_list = tr1.list_out()
    for tr in tr_list:
        print tr
