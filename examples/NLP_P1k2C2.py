"""Solve simple case using PyODHeaN Model"""
import pyomo.environ as pe

from pyodhean.model import Model


SOLUTIONS_FILENAME = '../solution.txt'


options = {
    'tol': 1e-3,
}


production = {
    'P1': {
        'technologies': {
            'k1': {
                'C_Hprod_unit': 800,
                'C_heat_unit': 0.03,
                'Eff': 0.8,
                'rate_i': 0.015,
                'T_prod_out_max': 100,
                'T_prod_in_min': 30,
                'coverage_rate': 0.80,
            },
            'k2': {
                'C_Hprod_unit': 1000,
                'C_heat_unit': 0.08,
                'Eff': 0.9,
                'rate_i': 0.04,
                'T_prod_out_max': 100,
                'T_prod_in_min': 30,
                'coverage_rate': None,
            },
        },
    },
}

consumption = {
    'C1': {
        'H_req': 80,
        'T_req_out': 80,
        'T_req_in': 60,
    },
    'C2': {
        'H_req': 80,
        'T_req_out': 80,
        'T_req_in': 60,
    },
}

configuration = {
    'prod_cons_pipes': {
        ('P1', 'C1'): 10,
        ('P1', 'C2'): 0,
    },
    'cons_cons_pipes': {
        ('C1', 'C1'): 0,
        ('C1', 'C2'): 100,
        ('C2', 'C1'): 0,
        ('C2', 'C2'): 0,
    },
}

model = Model(
    production=production,
    consumption=consumption,
    configuration=configuration,
)

print('### Solve ###\n')
# [tee] Display iterations (default: False)
# [keepfiles] Keep .nl/.sol/.log files (default: False)
model.solve('ipopt', options, tee=True, keepfiles=False)
print('')

print('### Display ###\n')
model.display()

# Print solutions to output file
with open(SOLUTIONS_FILENAME, 'w') as f:
    f.write('/// Objective ///\n')
    f.write(str(round(pe.value(model.model.objective, 2))) + '\n')
    f.write('/// Variables ///\n')
    for var in model.model.component_objects(pe.Var, active=True):
        for index in var:
            f.write(
                '{} [{}] {}\n'
                .format(var, index, round(var[index].value, 3))
            )
