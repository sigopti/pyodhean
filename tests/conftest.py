"""Test fixtures"""
import pytest


@pytest.fixture
def options():
    """Solver options

    cf https://www.coin-or.org/Ipopt/documentation/node42.html
    """
    return {
        'tol': 1e-3,           # defaut: 1e-8
        # max_iter':,           # defaut: 3000
        # max_cpu_time':,           # defaut: 1e+6
        # dual_inf_tol':,           # defaut = 1
        # constr_viol_tol':,           # defaut = 0.0001
        # compl_inf_tol':,           # defaut = 0.0001
        # acceptable_tol':,           # defaut = 1e-6
        # acceptable_iter':,           # defaut = 15
        # acceptable_constr_viol_tol':,           # defaut = 0.01
        # acceptable_dual_inf_tol':,           # defaut = 1e+10
        # acceptable_compl_inf_tol':,           # defaut = 0.01
        # acceptable_obj_change_tol':,           # defaut = 1e+20
        # diverging_iterates_tol':,           # defaut = 1e+20
    }


@pytest.fixture
def json_input():
    return {
        'nodes': {
            'production': [
                # P1
                {
                    'id': [0.0, 0.0],
                    'technologies': {
                        'k1': {
                            'efficiency': 0.9,
                            't_out_max': 100,
                            't_in_min': 30,
                            'production_unitary_cost': 800,
                            'energy_unitary_cost': 0.08,
                            'energy_cost_inflation_rate': 0.04,
                            'coverage_rate': 0.80,
                        },
                        'k2': {
                            'efficiency': 0.9,
                            't_out_max': 100,
                            't_in_min': 30,
                            'production_unitary_cost': 1000,
                            'energy_unitary_cost': 0.08,
                            'energy_cost_inflation_rate': 0.04,
                        },
                    },
                },
            ],
            'consumption': [
                # C1
                {
                    'id': [2.0, 5.0], 'kW': 80, 't_in': 60, 't_out': 80,
                },
                # C2
                {
                    'id': [30.0, 50.0], 'kW': 80, 't_in': 60, 't_out': 80,
                },
            ],
        },
        'links': [
            # P1 -> C1
            {'length': 10.0, 'source': [0.0, 0.0], 'target': [2.0, 5.0]},
            # C1 -> C2
            {'length': 100.0, 'source': [2.0, 5.0], 'target': [30.0, 50.0]},
        ],
        'parameters': {
            'diameter_int_max': 0.20,
            'speed_max': 2.5,
        },
    }
