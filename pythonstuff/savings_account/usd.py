#!/usr/bin/python3

import re
from constants import log 

class USD(object):
    def __init__(self, amount='0'):
        self._total = self.string2pennies(amount)

    def string2pennies(self, st):
        if isinstance(st, int):
            return st                           # in pennies 
        money = str(st)                         # incase it is already a number
        money = money.strip()                   # remove any leading/trailing space
        money = money.strip("$")                # remove any leading '$'
        if re.search(r'^\(', money):
            money = re.sub(r'^\(', "-", money)  # any leading "(" becomes "-"
            money = re.sub(r'\)', "", money)    # the trailing ")" goes away
        money = re.sub(r',', "", money)         # no commas
        money = re.sub(r'^$', "0", money)       # a '' translates to 0
        money = re.sub(r'^-$', "0", money)      # a '-' translates to 0
        money = re.sub(r'^-\$', "-", money)     # a '-$x.yz' translates to '-x.yz'
        money = round(float(money) * 100)       # avoid float-multiplication guesses!
        return int(money)                       # measure all money in whole pennies

    def __add__(self, other):
        my_sum = self._total + other._total
        return USD(my_sum)

    def __iadd__(self, other):
        self._total += other._total
        return self

    def __sub__(self, other):
        my_diff = self._total - other._total
        return USD(my_diff)

    def __isub__(self, other):
        self._total -= other._total
        return self

    def __mul__(self, other):
        if isinstance(other, USD):
            other = other._total
        my_prod = self._total * other
        return USD(my_prod)

    def __imul__(self, other):
        if isinstance(other, USD):
            other = other._total
        self._total *= other
        return self

    def __div__(self, other):
        if isinstance(other, USD):
            other = other._total
        my_res = self._total / other
        return USD(my_res)

    def __abs__(self):
        my_abs = self._total
        if my_abs < 0:
            return -my_abs
        return my_abs

    def __neg__(self):
        return -self._total

    def __eq__(self, other):
        if isinstance(other, USD):
            return (self._total == other._total)
        return (self._total == other)

    def __hash__(self):
        return hash(self._total)

    def as_float(self):
        return float(self._total)/100

    def __str__(self):
        return "%.2f" % self.as_float()


if __name__ == "__main__":
    mon = USD("$10.99")
    print(mon)
    mon2 = USD(20.0)
    print(mon2)
    mon3 = USD(4.29)
    print(mon3)
    mon2 = mon2 - mon
    print(mon2)
    mon2 += mon3
    print(mon2)
    print(mon2 * mon)
    print(mon3 * 3)
