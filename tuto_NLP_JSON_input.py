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
    'nodes': [
        # P1
        {'id': [0, 0], 'Dist_to_source': 0, 'kWh': 0, 'tot_kWh': 15467900, 'Type': 'Source'},
        # C1
        {'id': [2, 5], 'Dist_to_source': 10, 'kWh': 5382100.0, 'tot_kWh': 15467900},
        # C2
        {'id': [30, 50], 'Dist_to_source': 110, 'kWh': 0, 'tot_kWh': 10085800}
    ],
    'links': [
        # P1 -> C1
        {'Length': 10, 'source': [0, 0], 'target': [2, 5]},
        # C1 -> C2
        {'Length': 100, 'source': [2, 5], 'target': [30, 50]},
    ]
}


def id2str(coords):
    return ('{x}_{y}'.format(x=coords[0], y=coords[1]))


def str2id(coords):
    return [int(v) for v in coords.split('_')]


# Production / consumption nodes

production = {}
consumption = {}
for node in json_input['nodes']:
    if node.get('Type') == 'Source':
        production[id2str(node['id'])] = {
            # TODO: Get that from JSON
            'technologies': {
                'k1': {
                    'C_Hprod_unit': 800,
                    'C_heat_unit': 0.08,
                    'Eff': 0.9,
                    'rate_i': 0.04,
                    'T_prod_out_max': 100,
                    'T_prod_in_min': 30,
                },
            },
        }
    else:
        consumption[id2str(node['id'])] = {
            # TODO: Get that from JSON
            'H_req': 80,
            'T_req_out': 60,
            'T_req_in': 80,
        }


# Configuration

prod_cons_pipes = {}
cons_cons_pipes = {}
for link in json_input['links']:
    src = id2str(link['source'])
    trg = id2str(link['target'])
    if src in production:
        prod_cons_pipes[(src, trg)] = link['Length']
    elif src in consumption:
        cons_cons_pipes[(src, trg)] = link['Length']
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

print('Success:', result['success'])
print('Status:', result['status'])
print('Termination condition:', result['termination_condition'])

# Parse output

configuration_out = result['solution']

nodes = [
    {
        'id': str2id(prod_id),
        'Type': 'Source',
        **values
    }
    for prod_id, values in configuration_out['production'].items()
] + [
    {
        'id': str2id(cons_id),
        **values
    }
    for cons_id, values in configuration_out['consumption'].items()
]

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

print('success:', result['success'])
print('status:', result['status'])
print('termination condition:', result['termination_condition'])

assert result['success'] is False
assert result['status'] == 'warning'
assert result['termination_condition'] == 'maxIterations'
