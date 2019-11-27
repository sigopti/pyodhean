#!/usr/bin/env python3
"""Solve a problem defined in a .json file"""

import sys
import json
import argparse

from pprint import pprint

from pyodhean.interface import JSONInterface


options = {
    'tol': 1e-3,
}


parser = argparse.ArgumentParser(description='Solve PyODHeaN model.')
parser.add_argument('-i', dest='input_file', required=True, help='Input JSON file')

args = parser.parse_args()

try:
    with open(args.input_file) as f:
        json_input = json.load(f)
except IOError as e:
    print('Input file error: {}'.format(e))
    sys.exit()


solver = JSONInterface(options)
json_output = solver.solve(json_input, tee=True, keepfiles=False)
pprint(json_output)
