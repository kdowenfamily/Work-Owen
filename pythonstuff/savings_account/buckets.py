#!/usr/bin/python3

import csv, json, re, os
from copy import deepcopy
from bucket import Bucket
from usd import USD
from constants import log


class Buckets(object):
    BUCKETS_FILE = os.path.dirname(__file__) + "/data/buckets.json"

    @classmethod
    def from_file(cls, file_path=""):
        # read the JSON file and make one bucket per bucket dict
        buckets = []

        log.info("Parsing bucket-config file, '%s'.", file_path)
        with open(file_path) as json_data:
            buckets = json.load(json_data) 

        return Buckets(buckets)

    def __init__(self, buckets=[]):
        # read the list of bucket dicts and make one bucket per bucket dict
        log.info("Setting up %s raw buckets." % len(buckets))
        self.titles2buckets = {}
        self.tags2buckets = {}
        self.cats2buckets = {}
        self.alias2title = {}
        self.ordered_titles = []
        self.contents = []
        self.init_buckets(buckets)
        log.info("Done setting up %s buckets, total of %s." % (len(self.contents), self.total))

    @property
    def total(self):
        tot = USD(0)
        for bkt in self.contents:
            tot += bkt.total
        return tot

    @property
    def notes(self):
        ret = ""
        for bkt in self.contents:
            if len(bkt.comments):
                ret += " %s:" % bkt.title
            for cmt in bkt.comments:
                ret += " %s;" % cmt
        return ret.rstrip(';')

    def init_buckets(self, buckets=[]):
        for bucket in buckets:
            bkt = Bucket(bucket)
            self.insert_bucket(bkt)

        self.sort_buckets()

    def insert_bucket(self, bucket=None):
        if not bucket:
            return

        bkt = deepcopy(bucket)
        self.contents.append(bkt)
        self.titles2buckets[bkt.title] = bkt
        for tag in bkt.tags:
            if tag in self.tags2buckets.keys():
                log.warning("Dupe tag: '%s' in config record '%s, %s'.", tag, 
                                bkt.title, bkt.total)
            else:
                self.tags2buckets[tag] = bkt
        for cat in bkt.categories:
            if cat in self.cats2buckets.keys():
                log.warning("Dupe category: '%s' in config record '%s, %s'.", cat, 
                                bkt.title, bkt.total)
            else:
                self.cats2buckets[cat] = bkt
        for al in bkt.alt_titles:
            self.alias2title[al] = bkt.title

    def drop_bucket(self, bkt=None):
        if not bkt:
            return

        if bkt.title in self.ordered_titles:
            self.ordered_titles.remove(bkt.title)
        if bkt.title in self.titles2buckets.keys():
            del self.titles2buckets[bkt.title]
        self.contents.remove(bkt)

    def sort_buckets(self):
        self.ordered_titles = []
        for bucket in sorted(self.contents, key=lambda k: k.order):
            self.ordered_titles.append(bucket.title)

    def prune(self):
        # merge all buckets with alias titles into the buckets with the real titles
        to_drop = []
        for bucket in self.contents:
            if bucket.title not in self.alias2title.keys():
                continue
            real_title = self.alias2title[bucket.title]
            log.debug("Pruning %s and adding %s to %s." % (bucket.title, bucket.total, real_title) )
            real_bkt = self.titles2buckets[real_title]
            real_bkt += bucket
            to_drop.append(bucket)

        for dropped in to_drop:
            self.drop_bucket(dropped)

    def get_default(self):
        for bkt in self.contents:
            if bkt.default:
                return bkt

    def reset_default(self, bucket=None):
        if not bucket:
            return False

        # remove any default
        for bkt in self.contents:
            if bkt.default:
                bkt.default = False

        # set the new default
        bucket.default = True

    def find(self, number=0):
        if ((not number) or (abs(int(number)) > len(self.contents))):
            return None

        title = self.ordered_titles[int(number) - 1]
        return self.titles2buckets[title]

    def find_non_zero(self):
        non_zero = []

        for bkt in self.contents:
            if bkt.total:
                non_zero.append(bkt)

        return non_zero

    def dupe(self):
        twin = deepcopy(self)
        for bkt in twin.contents:
            bkt.total = 0
        return twin

    def show(self):
        ret = ""
        ct = 0

        for title in self.ordered_titles:
            ct += 1
            ct_str = str(ct)
            bkt = self.titles2buckets[title]
            money_str = str(bkt.total)
            ret += "%3d. %-24s %-6.2f" % (ct, bkt.title, float(money_str))
            if bkt.default:
                ret += " (default)"
            if bkt.notes:
                ret += " - " + bkt.notes
            ret += "\n"

        ret += "\nTotal:  %s\n" % self.total

        return ret

    def titles(self):
        ret = ""

        for title in self.ordered_titles:
            ret += self.titles2buckets[title].title + ","

        return ret.rstrip(",")

    def list_out(self):
        ret = []
        for title in self.ordered_titles:
            ret.append(str(self.titles2buckets[title].total))
        return ret

    def __str__(self):
        return ",".join(self.list_out())

    def __iadd__(self, other_buckets):
        # from self: for all my buckets, if I find a same-named bucket in the other set, add it
        for title in self.titles2buckets.keys():
            my_bkt = self.titles2buckets[title]
            if title in other_buckets.titles2buckets:
                my_bkt += other_buckets.titles2buckets[title]

        # from other: for all 'other' buckets NOT in the 'self' set, insert them as new buckets
        added_new = False
        for otitle in other_buckets.titles2buckets.keys():
            if otitle not in self.titles2buckets.keys():
                o_bkt = other_buckets.titles2buckets[otitle]
                self.insert_bucket(o_bkt)
                added_new = True

        # if there were any new buckets, prune aliases and sort again
        if added_new:
            self.prune()
            self.sort_buckets()

        return self

    def __isub__(self, other_buckets):
        obkts = deepcopy(other_buckets)
        for bkt in obkts.contents:
            bkt.negate()
        return self.__iadd__(obkts)

    def __eq__(self, other_buckets):
        for title in self.ordered_titles:
            my_bkt = self.titles2buckets[title]
            o_bkt = other_buckets.titles2buckets[title]
            if not (my_bkt == o_bkt):
                return False

        return True 

if __name__ == "__main__":
    bks = Buckets.from_file(Buckets.BUCKETS_FILE)
    print(bks.titles())
    print(bks)
