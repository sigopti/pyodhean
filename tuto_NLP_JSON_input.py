from pprint import pprint

from pyodhean.model import Model


# options [cf https://www.coin-or.org/Ipopt/documentation/node42.html]
options = {
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


json_input = {
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
                    },
                    'k2': {
                        'efficiency': 0.9,
                        't_out_max': 100,
                        't_in_min': 30,
                        'production_unitary_cost': 1000,
                        'energy_unitary_cost': 0.08,
                        'energy_cost_inflation_rate': 0.04,
                    },
                }
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
    ]
}


def id2str(coords):
    return '{x}_{y}'.format(x=coords[0], y=coords[1])


def str2id(coords):
    return [float(v) for v in coords.split('_')]


# Production / consumption nodes

production = {}
for node in json_input['nodes']['production']:
    technologies = {}
    for name, techno in node['technologies'].items():
        technologies[name] = {
            'Eff': techno['efficiency'],
            'T_prod_out_max': techno['t_out_max'],
            'T_prod_in_min': techno['t_in_min'],
            'C_Hprod_unit': techno['production_unitary_cost'],
            'C_heat_unit': techno['energy_unitary_cost'],
            'rate_i': techno['energy_cost_inflation_rate'],
        }
    production[id2str(node['id'])] = {'technologies': technologies}
consumption = {}
for node in json_input['nodes']['consumption']:
    consumption[id2str(node['id'])] = {
        'H_req': node['kW'],
        'T_req_out': node['t_out'],
        'T_req_in': node['t_in'],
    }


# Configuration

prod_cons_pipes = {}
cons_cons_pipes = {}
for link in json_input['links']:
    src = id2str(link['source'])
    trg = id2str(link['target'])
    if src in production:
        prod_cons_pipes[(src, trg)] = link['length']
    elif src in consumption:
        cons_cons_pipes[(src, trg)] = link['length']
    else:
        raise ValueError('Link with unknown source.')
for cons in consumption:
    for prod in production:
        prod_cons_pipes.setdefault((prod, cons), 0)
    for other_cons in consumption:
        cons_cons_pipes.setdefault((cons, other_cons), 0)

configuration = {
    'prod_cons_pipes': prod_cons_pipes,
    'cons_cons_pipes': cons_cons_pipes,
}


# Instantiate Model and solve

model = Model(
    production=production,
    consumption=consumption,
    configuration=configuration,
)

# [tee] Display iterations (default: False)
# [keepfiles] Keep .nl/.sol/.log files (default: False)
result = model.solve('ipopt', options, tee=False, keepfiles=False)
assert result['status'] == 'ok'

# Parse output

configuration_out = result['solution']

nodes = {
    'production': [
        {
            'id': str2id(prod_id),
            **values
        }
        for prod_id, values in configuration_out['production'].items()
    ],
    'consumption': [
        {
            'id': str2id(cons_id),
            **values
        }
        for cons_id, values in configuration_out['consumption'].items()
    ],
}

links = [
    {
        'source': str2id(src),
        'target': str2id(trg),
        **values
    }
    for (src, trg), values in {
        **configuration_out['prod_cons_pipes'],
        **configuration_out['cons_cons_pipes'],
    }.items()
]

json_output = {
    'nodes': nodes,
    'links': links,
    'global_indicators': configuration_out['global_indicators'],
}

pprint(json_output)


# Test solver failure

options['max_iter'] = 2
result = model.solve('ipopt', options, tee=False, keepfiles=False)
assert result['status'] == 'warning'
