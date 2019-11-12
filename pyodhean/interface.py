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
        model = Model(**problem)
        result = model.solve('ipopt', self.options, **kwargs)
        return self._parse_result(result)

    @staticmethod
    def _define_problem(json_input):

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
                    'coverage_rate': techno.get('coverage_rate'),
                }
            production[_id2str(node['id'])] = {'technologies': technologies}
        consumption = {}
        for node in json_input['nodes']['consumption']:
            consumption[_id2str(node['id'])] = {
                'H_req': node['kW'],
                'T_req_out': node['t_out'],
                'T_req_in': node['t_in'],
            }

        # Configuration
        prod_cons_pipes = {}
        cons_cons_pipes = {}
        for link in json_input['links']:
            src = _id2str(link['source'])
            trg = _id2str(link['target'])
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

        # General parameters
        general_parameters = json_input.get('parameters', {})

        return {
            'production': production,
            'consumption': consumption,
            'configuration': configuration,
            'general_parameters': general_parameters,
        }

    @staticmethod
    def _parse_result(result):

        if 'solution' not in result:
            return result

        configuration_out = result['solution']

        nodes = {
            'production': [
                {
                    'id': _str2id(prod_id),
                    **values
                }
                for prod_id, values in configuration_out['production'].items()
            ],
            'consumption': [
                {
                    'id': _str2id(cons_id),
                    **values
                }
                for cons_id, values in configuration_out['consumption'].items()
            ],
        }

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
