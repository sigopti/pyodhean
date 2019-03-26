#!/usr/bin/env python3

import sys
import json
import argparse

from pprint import pprint

from pyodhean.interface import JSONInterface


# options [cf https://www.coin-or.org/Ipopt/documentation/node42.html]
options = {
    'tol': 1e-3,           # defaut: 1e-8
}


parser = argparse.ArgumentParser(description='Solve PyODHEAN model.')
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
