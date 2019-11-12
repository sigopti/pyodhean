"""Solve a problem defined in a .json file"""
#!/usr/bin/env python3

import sys
import json
import argparse

from pprint import pprint

from pyodhean.interface import JSONInterface


# options [cf https://www.coin-or.org/Ipopt/documentation/node42.html]
options = {
    'tol': 1e-3,           # defaut: 1e-8
    # 'max_iter':,           # defaut: 3000
    # 'max_cpu_time':,           # defaut: 1e+6
    # 'dual_inf_tol':,           # defaut = 1
    # 'constr_viol_tol':,           # defaut = 0.0001
    # 'compl_inf_tol':,           # defaut = 0.0001
    # 'acceptable_tol':,           # defaut = 1e-6
    # 'acceptable_iter':,           # defaut = 15
    # 'acceptable_constr_viol_tol':,           # defaut = 0.01
    # 'acceptable_dual_inf_tol':,           # defaut = 1e+10
    # 'acceptable_compl_inf_tol':,           # defaut = 0.01
    # 'acceptable_obj_change_tol':,           # defaut = 1e+20
    # 'diverging_iterates_tol':,           # defaut = 1e+20
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
