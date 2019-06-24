"""Interface to PyODHeaN model"""

from pyodhean.model import Model


def _id2str(coords):
    return '{x}_{y}'.format(x=coords[0], y=coords[1])


def _str2id(coords):
    return [float(v) for v in coords.split('_')]


class JSONInterface:
    """PyODHeaN JSON interface

    :param dict options: Solver options
    """

    def __init__(self, options=None):
        self.options = options

    def solve(self, json_input, **kwargs):
        """Solve model

        Returns solver result.

        :param dict json_input: Problem description in JSON form
        """
        problem = self._define_problem(json_input)
        result = self._do_solve(problem, **kwargs)
        return self._parse_result(result)

    @staticmethod
    def _define_problem(json_input):

        # Production / consumption nodes
        production = {}
        consumption = {}
        for node in json_input['nodes']:
            if node.get('Type') == 'Source':
                production[_id2str(node['id'])] = {
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
                consumption[_id2str(node['id'])] = {
                    'H_req': node['kW'],
                    'T_req_out': node['Tout'],
                    'T_req_in': node['Tin'],
                }

        # Configuration
        prod_cons_pipes = {}
        cons_cons_pipes = {}
        for link in json_input['links']:
            src = _id2str(link['source'])
            trg = _id2str(link['target'])
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

    @staticmethod
    def _parse_result(result):

        if not result['success']:
            return result

        configuration_out = result['solution']

        nodes = [
            {
                'id': _str2id(prod_id),
                'Type': 'Source',
                **values
            }
            for prod_id, values in configuration_out['production'].items()
        ] + [
            {
                'id': _str2id(cons_id),
                **values
            }
            for cons_id, values in configuration_out['consumption'].items()
        ]

        links = [
            {
                'source': _str2id(src),
                'target': _str2id(trg),
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

    def _do_solve(self, problem, **kwargs):
        model = Model(**problem)
        return model.solve('ipopt', self.options, **kwargs)
