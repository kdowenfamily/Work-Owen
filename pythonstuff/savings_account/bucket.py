#!/usr/bin/python

import re, logging
from copy import deepcopy
from usd import USD
from constants import LOGFILE

logging.basicConfig(filename=LOGFILE,
        format="[%(asctime)s] [%(levelname)-7s] [%(filename)s:%(lineno)d] %(message)s",
        level=logging.DEBUG)
log = logging.getLogger(__name__)

DEFAULT_BUCKET = {
                "total": 0.0,
                "order": 99,
                "weight": 0,
                "title": "",
                "alt_titles": [],
                "tags": [],
                "categories": [],
                "comments": [],
                "default": False
                }

class Bucket(object):
    def __init__(self, bucket=DEFAULT_BUCKET):
        self.total = bucket.get("total", DEFAULT_BUCKET['total'])
        self.order = bucket.get("order", DEFAULT_BUCKET['order'])
        self.weight = bucket.get("weight", DEFAULT_BUCKET['weight'])
        self.title = bucket.get("title", DEFAULT_BUCKET['title'])
        self.alt_titles = bucket.get("alt_titles", DEFAULT_BUCKET['alt_titles'])
        self.tags = bucket.get("tags", DEFAULT_BUCKET['tags'])
        self.categories = bucket.get("categories", DEFAULT_BUCKET['categories'])
        self.comments = bucket.get("comments", DEFAULT_BUCKET['comments'])
        self.default = bucket.get("default", DEFAULT_BUCKET['default'])

    @property
    def total(self):
        return self._total

    @total.setter
    def total(self, total):
        self._total = USD(total)

    @property
    def order(self):
        return self._order

    @order.setter
    def order(self, order):
        self._order = int(order)               # incase it is a string

    @property
    def weight(self):
        return self._weight

    @weight.setter
    def weight(self, weight):
        if isinstance(weight, USD):
            self._weight = weight.as_float()
        else:
            self._weight = float(weight)       # incase it is a string

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, title):
        self._title = str(title)               # incase it is unicode

    @property
    def alt_titles(self):
        return self._alt_titles

    @alt_titles.setter
    def alt_titles(self, alt_titles):
        if not isinstance(alt_titles, list):
            alt_titles = [alt_titles]
        self._alt_titles = []
        for atitle in alt_titles:
            self._alt_titles.append(str(atitle)) # incase it is unicode

    @property
    def tags(self):
        return self._tags

    @tags.setter
    def tags(self, tags):
        if not isinstance(tags, list):
            tags = [tags]

        self._tags = []
        for tag in tags:
            if isinstance(tag, list):
                for tg in tag:
                    self._tags.append(str(tg)) # incase it is unicode
            else:
                self._tags.append(str(tag))    # incase it is unicode

    @property
    def categories(self):
        return self._categories

    @categories.setter
    def categories(self, categories):
        if not isinstance(categories, list):
            categories = [categories]

        self._categories = []
        for cat in categories:
            if isinstance(cat, list):
                for ct in cat:
                    self._categories.append(str(ct)) # incase it is unicode
            else:
                self._categories.append(str(cat))    # incase it is unicode

    @property
    def comments(self):
        return self._comments

    @comments.setter
    def comments(self, comments):
        self._comments = deepcopy(comments)

    def add_comment(self, comment):
        self._comments.append(comment)

    @property
    def default(self):
        return self._default

    @default.setter
    def default(self, default):
        self._default = default


    def __str__(self):
        return self.total

    def show(self):
        ret = ""

        ret += "Title:          " + self.title + "\n"
        ret += "  Alternates:   " + str(self.alt_titles) + "\n"
        ret += "Total:          " + str(self.total) + "\n"
        ret += "Weight:         " + str(self.weight) + "\n"
        ret += "Order:          " + str(self.order) + "\n"
        ret += "Tags:           " + str(self.tags) + "\n"
        ret += "Categories:     " + str(self.categories) + "\n"
        if self.default:
            ret += "Default bucket\n"

        return ret

    def _match(self, another_bucket):
        if another_bucket.title in self.alt_titles:
            return True
        elif another_bucket.title == self.title:
            return True
        else:
            return False

    def __add__(self, another_bucket):
        if self._match(another_bucket):
            sum_total = self.total + another_bucket.total
            return Bucket(total=sum_total)
        else:
            return self

    def __iadd__(self, another_bucket):
        if self._match(another_bucket):
            self.total = self.total + another_bucket.total
        return self

    def __eq__(self, another_bucket):
        return (
                (self.title == another_bucket.title) and
                (self.weight == another_bucket.weight) and
                (self.total == another_bucket.total)
        )

    def __neg__(self):
        my_neg = self._total
        if my_neg != 0: # neg zero is just zero
            return -my_neg
        return my_neg

    def negate(self):
        # negate the total in the current object
        self.total = -self
        return self

if __name__ == "__main__":
    bk = Bucket({"title":"Dan's Bucket", "total":"1,000,000"})
    print bk.show()
