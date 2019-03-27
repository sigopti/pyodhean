from pyodhean.model import Model


def id2str(coords):
    return ('{x}_{y}'.format(x=coords[0], y=coords[1]))


def str2id(coords):
    return [int(v) for v in coords.split('_')]


class JSONInterface:
    """PyODHEAN JSON interface"""

    def __init__(self, options):
        self.options = options

    def solve(self, json_input, **kwargs):
        problem = self.define_problem(json_input)
        result = self.do_solve(problem, **kwargs)
        return self.parse_result(result)

    def define_problem(self, json_input):

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

        return {
            'production': production,
            'consumption': consumption,
            'configuration': configuration,
        }

    def parse_result(self, result):

        if not result['success']:
            return result

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

        result['solution'] = {
            'nodes': nodes,
            'links': links,
            'global_indicators': configuration_out['global_indicators'],
        }

        return result

    def do_solve(self, problem, **kwargs):
        model = Model(**problem)
        return model.solve('ipopt', self.options, **kwargs)