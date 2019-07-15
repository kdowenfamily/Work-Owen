#!/usr/bin/python

import csv, json, re, logging, time
from datetime import datetime, timedelta

logging.basicConfig(filename="savings.log",
                    format="[%(asctime)s] [%(levelname)-7s] %(message)s",
                    level=logging.DEBUG)

class Transaction(object):
    def __init__(self, date=time.time, payee="", category="", tags=[], amount=0):
        self.date = date 
        self.payee = payee 
        self.category = category 
        self.tags = tags
        self.amount = amount 
        self.dest_bucket = None

    @property
    def date(self):
        return self._date

    @date.setter
    def date(self, date):
        # convert date string to datetime object
        self._date = datetime.strptime(date, '%m/%d/%Y')

    @property
    def payee(self):
        return self._payee

    @payee.setter
    def payee(self, payee):
        self._payee = str(payee)             # incase it is unicode

    @property
    def category(self):
        return self._category

    @category.setter
    def category(self, category):
        self._category = str(category)       # incase it is unicode

    @property
    def tags(self):
        return self._tags

    @tags.setter
    def tags(self, tags):
        if not isinstance(tags, list):
            tags = [tags]

        self._tags = []
        for tag in tags:
            self._tags.append(str(tag))        # incase it is unicode

    @property
    def amount(self):
        return self._amount

    @amount.setter
    def amount(self, amount):
        money = str(amount)                  # incase it is already a number

        money = money.strip()                # remove any leading/trailing space
        money = money.strip("$")             # remove any leading '$'
        money = re.sub(r',', "", money)      # no commas
        money = re.sub(r'^-$', "0", money)   # a '-' translates to 0
        money = float(money)

        self._amount = money

    @property
    def dest_bucket(self):
        return self._dest_bucket

    @dest_bucket.setter
    def dest_bucket(self, dest_bucket):
        self._dest_bucket = dest_bucket
