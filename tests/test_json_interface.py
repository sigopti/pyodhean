"""Test simple case using PyODHeaN JSON interface"""
from pyodhean.interface import JSONInterface


def test_solver_success(options, json_input):
    solver = JSONInterface(options)
    json_output = solver.solve(json_input)
    assert json_output['status'] == 'ok'


def test_solver_failure(options, json_input):
    options['max_iter'] = 2
    solver = JSONInterface(options)
    json_output = solver.solve(json_input)
    assert json_output['status'] == 'warning'
