#!/usr/bin/python

import csv, json, re, logging

logging.basicConfig(filename="savings.log",
                    format="[%(asctime)s] [%(levelname)-7s] %(message)s",
                    level=logging.DEBUG)

Class Moment:
    _total = 0
    _date = ""
    
    def __init__(total=0, date=""):
        _total = total
        _date = date 
