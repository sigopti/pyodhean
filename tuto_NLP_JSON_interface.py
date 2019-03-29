from pprint import pprint

from pyodhean.interface import JSONInterface


# options [cf https://www.coin-or.org/Ipopt/documentation/node42.html]
options = {
    'tol': 1e-3,           # defaut: 1e-8
}


json_input = {
    'nodes': [
        # P1
        {'id': [0, 0], 'kWh': 0, 'tot_kWh': 15467900, 'Type': 'Source'},
        # C1
        {'id': [2, 5], 'kWh': 5382100.0, 'tot_kWh': 15467900},
        # C2
        {'id': [30, 50], 'kWh': 0, 'tot_kWh': 10085800}
    ],
    'links': [
        # P1 -> C1
        {'Length': 10, 'source': [0, 0], 'target': [2, 5]},
        # C1 -> C2
        {'Length': 100, 'source': [2, 5], 'target': [30, 50]},
    ]
}


# Test solver success
solver = JSONInterface(options)
json_output = solver.solve(json_input, tee=False, keepfiles=False)
pprint(json_output)


# Test solver failure
options['max_iter'] = 2
solver = JSONInterface(options)
json_output = solver.solve(json_input, tee=False, keepfiles=False)
assert json_output['success'] is False
assert json_output['status'] == 'warning'
assert json_output['termination_condition'] == 'maxIterations'
