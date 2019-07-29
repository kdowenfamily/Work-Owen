#!/usr/bin/python

import csv, json, re, logging
from bucket import Bucket


logging.basicConfig(filename="savings.log",
                    format="[%(asctime)s] [%(levelname)-7s] %(message)s",
                    level=logging.DEBUG)

class Buckets(object):
    BUCKETS_FILE = "data/buckets.json"

    @classmethod
    def from_file(cls, file_path=""):
        # read the JSON file and make one bucket per bucket dict
        buckets = []

        logging.info("Parsing bucket-config file, '%s'.", file_path)
        with open(file_path) as json_data:
            buckets = json.load(json_data) 

        return Buckets(buckets)

    def __init__(self, buckets=[]):
        # read the JSON file and make one bucket per bucket dict
        logging.info("Setting up %s raw buckets." % len(buckets))
        self.titles2buckets = {}
        self.tags2buckets = {}
        self.ordered_titles = []
        self.contents = self.init_buckets(buckets)
        logging.info("Done setting up %s buckets, total of %.2f." % (len(self.contents), self.get_total()))

    def init_buckets(self, buckets=[]):
        bkts = []
        for bucket in buckets:
            bkt = Bucket(bucket)
            bkts.append(bkt)

            self.titles2buckets[bkt.title] = bkt
            for tag in bkt.tags:
                if tag in self.tags2buckets.keys():
                    logging.warning("Dupe tag: '%s' in config record '%s, %s'.", tag, 
                                    bkt.title, bkt.total)
                else:
                    self.tags2buckets[tag] = bkt

        for bucket in sorted(bkts, key=lambda k: k.order):
            self.ordered_titles.append(bucket.title)

        return bkts

    def get_total(self):
        tot = 0
        for bkt in self.contents:
            tot += bkt.total
        return tot

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
        if not number:
            return None

        title = self.ordered_titles[int(number) - 1]
        return self.titles2buckets[title]

    def find_non_zero(self):
        non_zero = []

        for bkt in self.contents:
            if bkt.total:
                non_zero.append(bkt)

        return non_zero

    def show(self):
        ret = ""
        ct = 0

        for title in self.ordered_titles:
            ct += 1
            ct_str = str(ct)
            bkt = self.titles2buckets[title]
            ret += "%3d. %-24s %-6.2f" % (ct, bkt.title, bkt.total)
            if bkt.default:
                ret += " (default)"
            ret += "\n"

        return ret

    def _print_titles(self):
        ret = ""

        for title in self.ordered_titles:
            ret += self.titles2buckets[title].title + ","

        return ret

    def __str__(self):
        ret = ""

        for title in self.ordered_titles:
            ret += str(self.titles2buckets[title].total) + ","

        return ret

    def __iadd__(self, other_buckets):
        for title in self.titles2buckets:
            my_bkt = self.titles2buckets[title]
            if title in other_buckets.titles2buckets:
                my_bkt += other_buckets.titles2buckets[title]

        return self

    def __eq__(self, other_buckets):
        for title in self.ordered_titles:
            my_bkt = self.titles2buckets[title]
            o_bkt = other_buckets.titles2buckets[title]
            if not (my_bkt == o_bkt):
                return False

        return True 

if __name__ == "__main__":
    bks = Buckets.from_file(Buckets.BUCKETS_FILE)
    print bks._print_titles()
    print bks
