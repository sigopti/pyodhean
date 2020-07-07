"""This file defines the PyODHeaN model class"""
# pylint: disable=too-many-lines

import math

import pyomo.environ as pe
import pyomo.opt as po

from .defaults import DEFAULT_PARAMETERS
from .utils import pluck


class Model:
    """PyODHeaN model class"""

    def __init__(self, production, consumption, configuration, general_parameters=None):
        # Store inputs
        self.production = production
        self.consumption = consumption
        self.configuration = configuration
        # Create model
        self.model = pe.ConcreteModel()
        self.def_production(production)
        self.def_consumption(consumption)
        self.def_configuration(configuration)
        self.def_problem({**DEFAULT_PARAMETERS, **(general_parameters or {})})

    def solve(self, solver, options=None, **kwargs):
        """Solve model

        :param str solver: Solver to use (e.g. 'ipopt')
        :param dict options: Solver options
        :param dict kwargs: Kwargs passed to solver's solve method
        """
        opt = po.SolverFactory(solver)
        opt.set_options(options or {})
        # Load solutions only on success to avoid a warning
        kwargs.setdefault('load_solutions', False)
        result = opt.solve(self.model, **kwargs)
        status = result.solver.status
        ret = {
            'status': str(status),
        }
        if status == po.SolverStatus.ok:
            self.model.solutions.load_from(result)
            ret['solution'] = self._get_solution()
        return ret

    def _get_solution(self):

        # Production
        prod_mapping = {
            'flow_rate': 'M_prod_tot',
            't_supply': 'T_prod_tot_out',
            't_return': 'T_prod_tot_in',
        }
        prod_techno_mapping = {
            'flow_rate': 'M_prod',
            't_supply': 'T_prod_out',
            'power': 'H_inst',
        }
        production = {
            prod_id: {
                **{
                    k: pe.value(getattr(self.model, v)[prod_id])
                    for k, v in prod_mapping.items()
                },
                'technologies': {
                    techno_id: {
                        **{
                            k: pe.value(getattr(self.model, v)[
                                (prod_id, '{}/{}'.format(prod_id, techno_id))
                            ])
                            for k, v in prod_techno_mapping.items()
                        },
                        # t_return is common to all technologies
                        't_return': pe.value(self.model.T_prod_tot_in[prod_id]),
                    }
                    for techno_id in prod['technologies']
                }
            }
            for prod_id, prod in self.production.items()
        }

        # Consumption
        cons_mapping = {
            'flow_rate_in_exchanger': 'M_hx',
            'flow_rate_before_exchanger': 'M_supply',
            'flow_rate_after_exchanger': 'M_return',
            'exchanger_power': 'H_hx',
            'exchanger_surface': 'A_hx',
            'exchanger_t_in': 'T_hx_in',
            'exchanger_t_out': 'T_hx_out',
            'exchanger_t_supply': 'T_supply',
            'exchanger_t_return': 'T_return',
            'exchanger_DTLM': 'DTLM',
            'exchanger_delta_t_hot': 'DT1',
            'exchanger_delta_t_cold': 'DT2',
            'exchanger_building_t_in': 'T_req_in',
            'exchanger_building_t_out': 'T_req_out',
        }
        consumption = {
            cons_id: {
                k: pe.value(getattr(self.model, v)[cons_id])
                for k, v in cons_mapping.items()
            }
            for cons_id, cons in self.consumption.items()
        }

        # Pipes
        # Supply is indexed as CC_parallel[src, target]
        # Return is indexed as CC_return[src, target]
        cons_cons_mapping = {
            'speed': 'V_lineCC_parallel',
            'diameter_int': 'Dint_CC_parallel',
            'flow_rate': 'M_lineCC_parallel',
            't_supply_in': 'T_lineCC_parallel_in',
            't_supply_out': 'T_lineCC_parallel_out',
            't_return_in': 'T_lineCC_return_in',
            't_return_out': 'T_lineCC_return_out',
        }
        cons_cons_pipes = {
            ccp: {
                **{
                    k: pe.value(getattr(self.model, v)[ccp])
                    for k, v in cons_cons_mapping.items()
                },
                'diameter_out': pe.value(
                    getattr(self.model, 'Dint_CC_parallel')[ccp] +
                    self.model.tk_insul + self.model.tk_pipe
                ),
            }
            for ccp, length in self.configuration['cons_cons_pipes'].items()
            if length
        }
        # Supply is indexed as PC[src, target]
        # Return is indexed as CP[target, src]
        prod_cons_mapping_PC = {
            'speed': 'V_linePC',
            'diameter_int': 'Dint_PC',
            'flow_rate': 'M_linePC',
            't_supply_in': 'T_linePC_in',
            't_supply_out': 'T_linePC_out',
        }
        prod_cons_mapping_CP = {
            't_return_in': 'T_lineCP_in',
            't_return_out': 'T_lineCP_out',
        }
        prod_cons_pipes = {
            pcp: {
                **{
                    k: pe.value(getattr(self.model, v)[pcp])
                    for k, v in prod_cons_mapping_PC.items()
                },
                'diameter_out': pe.value(
                    getattr(self.model, 'Dint_PC')[pcp] +
                    self.model.tk_insul + self.model.tk_pipe
                ),
                **{
                    k: pe.value(getattr(self.model, v)[(pcp[1], pcp[0])])
                    for k, v in prod_cons_mapping_CP.items()
                },
            }
            for pcp, length in self.configuration['prod_cons_pipes'].items()
            if length
        }
        # Add derived indicators common to cons-cons and prod-cons pipes
        for pipe in {**cons_cons_pipes, **prod_cons_pipes}.values():
            pipe['power'] = pe.value(
                pipe['flow_rate'] *
                self.model.Cp *
                (pipe['t_supply_out'] - pipe['t_return_in'])
            )
            pipe['yearly_energy'] = pe.value(
                pipe['power'] * self.model.period
            )

        # Global indicators
        globals_mapping = {
            'production_intallation_cost': 'C_Hinst',
            'exchangers_installation_cost': 'C_hx',
            'network_cost': 'C_line_tot',
            'trenches_cost': 'C_tr',
            'pipes_cost': 'C_pipe',
            'network_length': 'L_tot',
            'pumps_operation_cost': 'C_pump',
            'heat_production_cost': 'C_heat',
        }
        global_indicators = {
            k: pe.value(getattr(self.model, v))
            for k, v in globals_mapping.items()
        }
        # XXX: This should be fixed in the model instead
        for indicator in (
            'production_intallation_cost',
            'exchangers_installation_cost',
            'network_cost',
            'trenches_cost',
            'pipes_cost',
            'pumps_operation_cost',
            'heat_production_cost',
        ):
            global_indicators[indicator] *= 1_000_000
        global_indicators['total_capex'] = (
            global_indicators['production_intallation_cost'] +
            global_indicators['exchangers_installation_cost'] +
            global_indicators['network_cost']
        )
        global_indicators['total_opex'] = (
            global_indicators['pumps_operation_cost'] +
            global_indicators['heat_production_cost']
        )
        global_indicators['total_cost'] = (
            global_indicators['total_capex'] +
            global_indicators['total_opex']
        )
        global_indicators['yearly_production'] = pe.value(
            self.model.period *
            self.model.simultaneity_rate *
            (1 + self.model.heat_loss_rate) *
            sum(self.model.H_inst[i, k] for k in self.model.k for i in self.model.i)
        )
        global_indicators['total_production'] = (
            global_indicators['yearly_production'] *
            pe.value(self.model.depreciation_period)
        )

        configuration = {
            'production': production,
            'consumption': consumption,
            'prod_cons_pipes': prod_cons_pipes,
            'cons_cons_pipes': cons_cons_pipes,
            'global_indicators': global_indicators,
        }
        return configuration

    def display(self):
        """Display model"""
        self.model.display()

    def def_production(self, production):
        """Define production"""
        technologies = {}
        technos_per_prod = {}
        for prod_id, prod in production.items():
            technos = prod['technologies']
            for techno_id, techno in technos.items():
                # Prefix techno_id with prod_id to prevent id collision
                techno_id = '{}/{}'.format(prod_id, techno_id)
                technologies[techno_id] = techno
                technos_per_prod[(prod_id, techno_id)] = 1

        self.model.i = pe.Set(
            initialize=production.keys(),
            doc='indice des noeuds producteurs')
        self.model.k = pe.Set(
            initialize=technologies.keys(),
            doc='indice technologie de production')
        self.model.C_Hprod_unit = pe.Param(
            self.model.k, initialize=pluck(technologies, 'C_Hprod_unit'),
            doc='coût unitaire de la chaudiere installée (€/kW)')
        self.model.C_heat_unit = pe.Param(
            self.model.k, initialize=pluck(technologies, 'C_heat_unit'),
            doc="coût unitaire de la chaleur suivant l'énergie de la technologie employee "
                "et la periode selon inflation (€/kWh)")
        self.model.Eff = pe.Param(
            self.model.k, initialize=pluck(technologies, 'Eff'),
            doc='rendement de la technologie k (%)')
        self.model.rate_i = pe.Param(
            self.model.k, initialize=pluck(technologies, 'rate_i'),
            doc="inflation de l'énergie liée à la technologie k (%)")
        self.model.T_prod_out_max = pe.Param(
            self.model.k, initialize=pluck(technologies, 'T_prod_out_max'),
            doc='température max autorisée en sortie de chaudiere de la techno k (°C)')
        self.model.T_prod_in_min = pe.Param(
            self.model.k, initialize=pluck(technologies, 'T_prod_in_min'),
            doc='température min autorisée en entree de chaudiere de la techno k (°C)')
        self.model.coverage_rate = pe.Param(
            self.model.k, domain=pe.Any, initialize=pluck(technologies, 'coverage_rate'),
            doc='taux de couverture de la techno k')
        self.model.Y_P = pe.Param(
            self.model.i, self.model.k, initialize=technos_per_prod,
            doc='Existence techno k au lieu de production Pi')

    def def_consumption(self, consumption):
        """Define consumption"""
        self.model.j = pe.Set(
            initialize=consumption.keys(),
            doc='indice des noeuds consommateurs')
        self.model.o = pe.Set(
            initialize=consumption.keys(),
            doc='indice des noeuds consommateurs')
        self.model.H_req = pe.Param(
            self.model.j, initialize=pluck(consumption, 'H_req'),
            doc='besoin de chaleur (kW)')
        self.model.T_req_out = pe.Param(
            self.model.j, initialize=pluck(consumption, 'T_req_out'),
            doc='température entree reseau secondaire du consommateur (°C)')
        self.model.T_req_in = pe.Param(
            self.model.j, initialize=pluck(consumption, 'T_req_in'),
            doc='température retour reseau secondaire du consommateur (°C)')

    def def_configuration(self, configuration):
        """Define configuration"""
        table_Y_linePC = {
            (c, p): 1 if e else 0
            for (c, p), e in configuration['prod_cons_pipes'].items()
        }

        table_Y_lineCP = {
            (c, p): e for (p, c), e in table_Y_linePC.items()
        }
        self.model.Y_linePC = pe.Param(
            self.model.i, self.model.j, initialize=table_Y_linePC,
            doc='Existence canalisation PC')
        self.model.Y_lineCP = pe.Param(
            self.model.j, self.model.i, initialize=table_Y_lineCP,
            doc='Existence canalisation CP')

        table_Y_lineCC_parallel = {
            (c, p): 1 if e else 0
            for (c, p), e in configuration['cons_cons_pipes'].items()
        }
        table_Y_lineCC_return = {
            (c2, c1): e for (c1, c2), e in table_Y_lineCC_parallel.items()
        }
        self.model.Y_lineCC_parallel = pe.Param(
            self.model.j, self.model.o, initialize=table_Y_lineCC_parallel,
            doc='Existence canalisation CC aller')
        self.model.Y_lineCC_return = pe.Param(
            self.model.o, self.model.j, initialize=table_Y_lineCC_return,
            doc='Existence canalisation CC retour')

        # Distances
        self.model.L_PC = pe.Param(
            self.model.i, self.model.j,
            initialize=configuration['prod_cons_pipes'],
            doc='matrice des longueurs de canalisations')

        self.model.L_CP = pe.Param(
            self.model.j, self.model.i,
            initialize={
                (c, p): e
                for (p, c), e in configuration['prod_cons_pipes'].items()},
            doc='matrice des longueurs de canalisations')

        self.model.L_CC_parallel = pe.Param(
            self.model.j, self.model.o,
            initialize=configuration['cons_cons_pipes'],
            doc='matrice des longueurs de canalisations')

        self.model.L_CC_return = pe.Param(
            self.model.o, self.model.j, initialize={
                (c, p): e
                for (p, c), e in configuration['cons_cons_pipes'].items()},
            doc='matrice des longueurs de canalisations')

    def def_problem(self, general_parameters):
        """Define problem"""
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements

        def has_power_demand(j_idx):
            """Return True if the node has power demand

            If the power demand is 0, the node is a network node.
            """
            return bool(self.model.H_req[j_idx])

        # Température maximale pour les températures de retour/sortie
        # Il s'agit de la plus grande température parmis les températures maximales
        # de départ des technologies de production
        T_prod_out_max = max(self.model.T_prod_out_max[k] for k in self.model.k)
        # Température minimale pour les températures de départ/entrée
        # Il s'agit de la plus petite température parmi les températures minimales
        # de retour des technologies de production
        T_prod_in_min = min(self.model.T_prod_in_min[k] for k in self.model.k)

        # Parameters

        self.model.C_tr_unit = pe.Param(
            initialize=general_parameters['trench_unit_cost'],
            doc='coût unitaire de tranchee aller-retour (€/ml)')
        self.model.period = pe.Param(
            initialize=general_parameters['operation_time'],
            doc='durée de fonctionnement annuelle du RCU (h)')
        self.model.depreciation_period = pe.Param(
            initialize=general_parameters['depreciation_period'],
            doc="duree d'amortissement (année)")

        # Définition des paramètres ne dépendant pas de la taille du problème
        # Valeur affectée
        self.model.T_hx_pinch = pe.Param(
            initialize=general_parameters['exchanger_t_pinch_min'],
            doc="température de pincement minimum a l'échangeur (°C)")
        self.model.K_hx = pe.Param(
            initialize=general_parameters['exchanger_overall_transfer_coefficient'],
            doc="coefficient global d'échange (kW/m2.K)")
        self.model.Cp = pe.Param(
            initialize=general_parameters['water_cp'],
            doc="capacite thermique de l'eau à 80°C (kJ/kg.K)")
        self.model.C_pump_ratio = pe.Param(
            initialize=general_parameters['pump_energy_ratio_cost'],
            doc="ratio coût de pompage/coût global")
        self.model.mu = pe.Param(
            initialize=general_parameters['water_mu'],
            doc="viscosite de l'eau a 80°C (Pa.s)")
        self.model.rho = pe.Param(
            initialize=general_parameters['water_rho'],
            doc="'masse volumique de l'eau a 20°C (kg/m3)")
        self.model.C_pipe_unit_a = pe.Param(
            initialize=general_parameters['pipe_diameter_unit_cost_slope'],
            doc=('coefficient directeur de la relation linéaire du coût de la canalisation '
                 'selon le diamètre (ensemble tuyau+isolant)(€/m)'))
        self.model.C_pipe_unit_b = pe.Param(
            initialize=general_parameters['pipe_diameter_unit_cost_y_intercept'],
            doc=("ordonnée à l'origine de la relation linéaire du coût de la canalisation "
                 "selon le diamètre (ensemble tuyau+isolant)(€)"))
        self.model.C_hx_unit_a = pe.Param(
            initialize=general_parameters['exchanger_power_cost_slope'],
            doc="coefficient directeur du coût unitaire de l'echangeur (€/kW )")
        self.model.C_hx_unit_b = pe.Param(
            initialize=general_parameters['exchanger_power_cost_y_intercept'],
            doc="ordonnee à l'origine du coût unitaire de l'echangeur (€)")
        self.model.rate_a = pe.Param(
            initialize=general_parameters['discout_rate'],
            doc="taux d'actualisation pour le calcul de l'annuite des investissements initiaux")
        self.model.tk_insul = pe.Param(
            initialize=general_parameters['pipe_insulation_thickness'],
            doc="épaisseur de l'isolant autour de la canalisation (m)")
        self.model.tk_pipe = pe.Param(
            initialize=general_parameters['pipe_thickness'],
            doc="épaisseur de metal dependant du diametre (m)")
        self.model.simultaneity_rate = pe.Param(
            initialize=general_parameters['simultaneity_ratio'],
            doc="taux de foisonnement")
        self.model.heat_loss_rate = pe.Param(
            initialize=general_parameters['heat_loss_rate'],
            doc="taux de pertes thermiques pour le calcul de C_heat ")
        self.model.linear_heat_loss = pe.Param(
            initialize=general_parameters['linear_heat_loss'],
            doc="pertes thermiques linéaires (°C/m) pour les équations Def loss_linePC, CP, CC...")

        # bornes
        self.model.V_min = pe.Param(
            initialize=general_parameters['speed_min'],
            doc="borne vitesse min, 0.1m/s d'après Techniques de l'Ingénieur (m/s)")
        self.model.V_max = pe.Param(
            initialize=general_parameters['speed_max'],
            doc="borne vitesse max, 3m/s d'après Techniques de l'Ingénieur (m/s)")
        self.model.Dint_max = pe.Param(
            initialize=general_parameters['diameter_int_max'],
            doc='diamètre interieur max du tuyau (m)')
        self.model.Dint_min = pe.Param(
            initialize=general_parameters['diameter_int_min'],
            doc='diamètre interieur max du tuyau (m)')

        # Valeur calculée

        H_req_max = sum(self.model.H_req[j] for j in self.model.j)
        # Somme des puissances installées de toutes les sous-stations
        # Correspond à la puissance maximale théorique appelée (cas exeptionnel)
        # et donc sert de borne max pour la puissance à installer au niveau de la production
        self.model.H_inst_max = pe.Param(initialize=1.5 * H_req_max)
        # BigM associé à la puissance maximale à installer à chaque production
        # (valeur commune à toutes les productions potentielles)
        self.model.H_inst_bigM = pe.Param(initialize=1000 * H_req_max)

        def calcul_f_opex(model, k):
            """Facteur multiplicateur des coûts operationnels permettant de tenir compte de la somme
             des dépenses annuelles actualisés et suivant l'inflation de l'energie et ce par
             technologie de production (électricité/gaz/biomasse/UIOM...)
             """
            dep = model.depreciation_period
            return (
                (1 - (1 + model.rate_a)**dep * (1 + model.rate_i[k])**dep) /
                (1 - (1 + model.rate_a) * (1 + model.rate_i[k]))
            )
        self.model.f_opex = pe.Param(self.model.k, initialize=calcul_f_opex)

        def calcul_f_capex(model):
            """Facteur multiplicateur pour le calcul du coût d'investissement

            Permet de tenir compte du taux d'actualisation
            (mais pas d'inflation contraitement aux coûts opex)
            """
            return (1 + model.rate_a)**model.depreciation_period
        self.model.f_capex = pe.Param(initialize=calcul_f_capex)

        def calcul_M_max(model):
            """Débit maximal dans la canalisation, lié à V_max et Dint_max

            S'applique à l'ensemble du réseau (productions, échangeurs en sous-station
            et conduites)
            """
            return model.V_max * model.rho * math.pi * (model.Dint_max**2) / 4
        self.model.M_max = pe.Param(initialize=calcul_M_max)

        self.model.M_min = pe.Param(initialize=0, doc='débit minimal dans la canalisation')

        def calcul_M_bigM(model):
            """BigM associé au débit maximal pour l'optimisation des débits"""
            return 1000 * model.M_max
        self.model.M_bigM = pe.Param(initialize=calcul_M_bigM)

        # BigM associé à la température maximale pour l'optimisation des régimes de température
        # elle vaut 1000 fois la température de départ maximale des technologies disponibles"""
        self.model.T_bigM = pe.Param(initialize=T_prod_out_max)

        # Variables

        # TODO: Improve init values
        V_init = 0.5 * self.model.V_min + 0.5 * self.model.V_max
        Dint_init = 0.25 * self.model.Dint_min + 0.75 * self.model.Dint_max
        M_init = 1 * self.model.M_min + 0 * self.model.M_max

        # Vitesses
        self.model.V_linePC = pe.Var(
            self.model.i, self.model.j,
            initialize=V_init,
            bounds=(self.model.V_min, self.model.V_max),
            doc='vitesses conduites producteurs-consommateurs = ALLER')
        self.model.V_lineCP = pe.Var(
            self.model.j, self.model.i,
            initialize=V_init,
            bounds=(self.model.V_min, self.model.V_max),
            doc='vitesses conduites consommateurs-producteurs = RETOUR')
        self.model.V_lineCC_parallel = pe.Var(
            self.model.j, self.model.o,
            initialize=V_init,
            bounds=(self.model.V_min, self.model.V_max),
            doc='vitesses conduites consommateurs-consommateurs ALLER')
        self.model.V_lineCC_return = pe.Var(
            self.model.o, self.model.j,
            initialize=V_init,
            bounds=(self.model.V_min, self.model.V_max),
            doc='vitesses conduites consommateurs-consommateurs RETOUR')

        # Diamètres
        self.model.Dint_PC = pe.Var(
            self.model.i, self.model.j,
            initialize=Dint_init,
            bounds=(self.model.Dint_min, self.model.Dint_max),
            doc='diamètres intérieurs conduites producteurs-consommateurs = ALLER')
        self.model.Dint_CP = pe.Var(
            self.model.j, self.model.i,
            initialize=Dint_init,
            bounds=(self.model.Dint_min, self.model.Dint_max),
            doc='diamètres intérieurs conduites consommateurs-producteurs = RETOUR')
        self.model.Dint_CC_parallel = pe.Var(
            self.model.j, self.model.o,
            initialize=Dint_init,
            bounds=(self.model.Dint_min, self.model.Dint_max),
            doc='diamètres intérieurs conduites consommateurs-consommateurs ALLER')
        self.model.Dint_CC_return = pe.Var(
            self.model.o, self.model.j,
            initialize=Dint_init,
            bounds=(self.model.Dint_min, self.model.Dint_max),
            doc='diamètres intérieurs conduites consommateurs-consommateurs RETOUR')

        # Débits
        self.model.M_linePC = pe.Var(
            self.model.i, self.model.j,
            initialize=M_init,
            bounds=(self.model.M_min, self.model.M_max),
            doc='debit entre un noeud P(i) et C(j) (kg/s)')
        self.model.M_lineCP = pe.Var(
            self.model.j, self.model.i,
            initialize=M_init,
            bounds=(self.model.M_min, self.model.M_max),
            doc='debit entre un noeud C(j) et P(i) (kg/s)')
        self.model.M_prod = pe.Var(
            self.model.i, self.model.k,
            initialize=M_init,
            bounds=(self.model.M_min, self.model.M_max),
            doc='debit de la techno k(k) dans P(i) (kg/s)')
        self.model.M_prod_tot = pe.Var(
            self.model.i,
            initialize=M_init,
            bounds=(self.model.M_min, self.model.M_max),
            doc='debit dans P(i) = somme des débits des technos k(k) (kg/s)')

        def calcul_M_hx_init(model, j):
            if not has_power_demand(j):
                return 0
            return model.M_min

        def calcul_M_hx_bounds(model, j):
            if not has_power_demand(j):
                return (0, 0)
            return (model.M_min, model.M_max)

        self.model.M_hx = pe.Var(
            self.model.j,
            initialize=calcul_M_hx_init,
            bounds=calcul_M_hx_bounds,
            doc="debit dans l'échangeur de C(j) côté primaire (kg/s)")

        self.model.M_supply = pe.Var(
            self.model.j,
            initialize=self.model.M_min,
            bounds=(0, self.model.M_max),
            doc=("debit avant l'échangeur de C(j); "
                 "différent de M_hx seulement si cascade autorisée (kg/s)"))

        self.model.M_lineCC_parallel = pe.Var(
            self.model.j, self.model.o,
            initialize=self.model.M_min,
            bounds=(self.model.M_min, self.model.M_max),
            doc='debit entre un noeud C(j) et C(o) - ALLER (kg/s)')
        self.model.M_lineCC_return = pe.Var(
            self.model.o, self.model.j,
            initialize=self.model.M_min,
            bounds=(self.model.M_min, self.model.M_max),
            doc='debit entre un noeud C(o) et C(j) - RETOUR (kg/s)')
        self.model.M_return = pe.Var(
            self.model.j,
            initialize=self.model.M_min,
            bounds=(self.model.M_min, self.model.M_max),
            doc=(
                "debit après l'échangeur au noeud C(j); "
                "différent de M_hx seulement si cascade (kg/s)"))

        # Températures
        self.model.T_prod_tot_in = pe.Var(
            self.model.i,
            initialize=T_prod_in_min,
            bounds=(T_prod_in_min, T_prod_out_max),
            doc='température de retour à la production i (°C)')
        self.model.T_prod_out = pe.Var(
            self.model.i, self.model.k,
            initialize=T_prod_in_min,
            bounds=(T_prod_in_min, T_prod_out_max),
            doc='température de départ de la technologie k de la production i (°C)')
        self.model.T_prod_tot_out = pe.Var(
            self.model.i,
            initialize=T_prod_in_min,
            bounds=(T_prod_in_min, T_prod_out_max),
            doc=(
                'température de départ de la production i (°C) '
                '= mélange des k technologies'
            ))
        self.model.T_linePC_in = pe.Var(
            self.model.i, self.model.j,
            initialize=T_prod_in_min,
            bounds=(T_prod_in_min, T_prod_out_max),
            doc='température de départ de la production i (°C)')
        self.model.T_linePC_out = pe.Var(
            self.model.i, self.model.j,
            initialize=T_prod_in_min,
            bounds=(T_prod_in_min, T_prod_out_max),
            doc=("température d'entrée dans le premier noeud "
                 "= température de départ de la production i - pertes (°C)"))
        self.model.T_lineCP_in = pe.Var(
            self.model.j, self.model.i,
            initialize=T_prod_in_min,
            bounds=(T_prod_in_min, T_prod_out_max),
            doc='température de départ du dernier noeud (°C)')
        self.model.T_lineCP_out = pe.Var(
            self.model.j, self.model.i,
            initialize=T_prod_in_min,
            bounds=(T_prod_in_min, T_prod_out_max),
            doc=('température de retour à la production i '
                 '= température de départ du dernier noeud - pertes (°C)'))
        self.model.T_hx_in = pe.Var(
            self.model.j,
            initialize=T_prod_in_min,
            bounds=(T_prod_in_min, T_prod_out_max),
            doc="température d'entrée dans l'échangeur (°C)")
        self.model.T_hx_out = pe.Var(
            self.model.j,
            initialize=T_prod_in_min,
            bounds=(T_prod_in_min, T_prod_out_max),
            doc="température de sortie de l'échangeur (°C)")
        self.model.T_supply = pe.Var(
            self.model.j,
            initialize=T_prod_in_min,
            bounds=(T_prod_in_min, T_prod_out_max),
            doc="température avant l'échangeur de C(j) = T_hx_in (°C)")
        self.model.T_lineCC_parallel_in = pe.Var(
            self.model.j, self.model.o,
            initialize=T_prod_in_min,
            bounds=(T_prod_in_min, T_prod_out_max),
            doc='température de départ au noeud C(j) - ALLER (°C)')
        self.model.T_lineCC_parallel_out = pe.Var(
            self.model.j, self.model.o,
            initialize=T_prod_in_min,
            bounds=(T_prod_in_min, T_prod_out_max),
            doc="température d'arrivée au noeud C(o) - ALLER (°C)")
        self.model.T_lineCC_return_in = pe.Var(
            self.model.o, self.model.j,
            initialize=T_prod_in_min,
            bounds=(T_prod_in_min, T_prod_out_max),
            doc='température de départ au noeud C(o) - RETOUR (°C)')
        self.model.T_lineCC_return_out = pe.Var(
            self.model.o, self.model.j,
            initialize=T_prod_in_min,
            bounds=(T_prod_in_min, T_prod_out_max),
            doc="température d'arrivée au noeud C(j) - RETOUR (°C)")
        self.model.T_return = pe.Var(
            self.model.j,
            initialize=T_prod_in_min,
            bounds=(T_prod_in_min, T_prod_out_max),
            doc="température après l'échangeur de C(j) = T_hx_out (°C)")

        # Echangeur
        def calcul_DTLM_init(model, j):
            if not has_power_demand(j):
                return 0
            return model.T_hx_pinch

        def calcul_DTLM_bounds(model, j):
            if not has_power_demand(j):
                return (0, 0)
            return (model.T_hx_pinch, T_prod_out_max)

        self.model.DTLM = pe.Var(
            self.model.j,
            initialize=calcul_DTLM_init,
            bounds=calcul_DTLM_bounds,
            doc='Différence logarithmique de température à l’échangeur de chaleur (°C)')

        def calcul_DT_init(model, j):
            if not has_power_demand(j):
                return 0
            return model.T_hx_pinch

        def calcul_DT_bounds(model, j):
            if not has_power_demand(j):
                return (0, 0)
            return (model.T_hx_pinch, T_prod_out_max)

        self.model.DT1 = pe.Var(
            self.model.j,
            initialize=calcul_DT_init,
            bounds=calcul_DT_bounds,
            doc='Différence de température côté chaud = T_hx_in - T_req_out (°C)')
        self.model.DT2 = pe.Var(
            self.model.j,
            initialize=calcul_DT_init,
            bounds=calcul_DT_bounds,
            doc='Différence de température côté froid = T_hx_out - T_req_in (°C)')

        def A_hx_borne(model, j):
            # TODO: Multiplying by 10 *after* the division introduces a slight
            # floating-point approx. Without this, we get convergence issues. Why ?
            A_hx = model.H_req[j] / (model.K_hx * T_prod_out_max)
            return (A_hx, 10 * A_hx)

        def A_hx_init(model, j):
            return model.H_req[j] / (model.K_hx * T_prod_out_max)
        self.model.A_hx = pe.Var(
            self.model.j, initialize=A_hx_init, bounds=A_hx_borne,
            doc="Surface de l'échangeur pour chaque consommateur j, bornée par le pincement "
            "T_hx_pinch ==> cf calcul de A_hx_borne")

        # Puissances installées
        self.model.H_inst = pe.Var(
            self.model.i, self.model.k, initialize=0, bounds=(0, self.model.H_inst_max),
            doc='Puissance installée à la production i pour la technologie k (kW)')

        def H_hx_borne(model, j):
            return (0, model.H_req[j])
        self.model.H_hx = pe.Var(
            self.model.j, initialize=0, bounds=H_hx_borne,
            doc="Puissance nominale de l'échangeur du consommateur j")

        # Coûts
        self.model.C_pump = pe.Var(
            initialize=0, bounds=(0, None),
            doc='Coûts de pompage (€)')
        self.model.C_heat = pe.Var(
            initialize=0, bounds=(0, None),
            doc='Coût de la chaleur à produire (€)')
        self.model.C_Hinst = pe.Var(
            initialize=0, bounds=(0, None),
            doc="Coût d'installation de la puissance à la production (€)")
        self.model.C_hx = pe.Var(
            initialize=0, bounds=(0, None),
            doc="Coût d'installation des échangeurs en sous-station (€)")
        self.model.C_line_tot = pe.Var(
            initialize=0, bounds=(0, None),
            doc='Coût total de la canalisation = tranchée + tuyau pré-isolé (€) ')
        self.model.C_pipe = pe.Var(
            initialize=0, bounds=(0, None),
            doc='Coût des tuyau pré-isolés (€)')
        self.model.C_tr = pe.Var(
            initialize=0, bounds=(0, None),
            doc='Coût de tranchée (€)')

        # Longueur du réseau
        self.model.L_tot = pe.Var(
            initialize=0, bounds=(0, None),
            doc=('Longueur totale du réseau = longueur de tuyaux posés '
                 '= 2 fois la longueur de tranchée car tuyau aller-retour'))

        # Constraints

        # Existance des contraintes selon la valeur des variables binaires avec la méthode du bigM
        #  Débits
        def Def_V_linePC_rule_bigM(model, i, j):
            """Inéquation du bigM sur le débit entre producteur et consommateur - ALLER"""
            valeur = (
                model.V_linePC[i, j] * (
                    model.rho * math.pi * model.Dint_PC[i, j] * model.Dint_PC[i, j] / 4) -
                model.M_linePC[i, j]
            )
            return pe.inequality(
                - model.M_bigM * (1 - model.Y_linePC[i, j]),
                valeur,
                model.M_bigM * (1 - model.Y_linePC[i, j])
            )
        self.model.Def_V_linePC_bigM = pe.Constraint(
            self.model.i, self.model.j, rule=Def_V_linePC_rule_bigM)

        def Def_V_lineCP_rule_bigM(model, j, i):
            """Inéquation du bigM sur le débit entre consommateur et producteur - RETOUR"""
            valeur = (
                model.V_lineCP[j, i] * (
                    model.rho * math.pi * model.Dint_CP[j, i] * model.Dint_CP[j, i] / 4) -
                model.M_lineCP[j, i]
            )
            return pe.inequality(
                - model.M_bigM * (1 - model.Y_lineCP[j, i]),
                valeur,
                model.M_bigM * (1 - model.Y_lineCP[j, i])
            )
        self.model.Def_V_lineCP_bigM = pe.Constraint(
            self.model.j, self.model.i, rule=Def_V_lineCP_rule_bigM)

        def Def_V_lineCC_parallel_rule_bigM(model, j, o):
            """Inéquation du bigM sur le débit entre consommateurs - ALLER"""
            valeur = (
                model.V_lineCC_parallel[j, o] * model.rho * math.pi *
                model.Dint_CC_parallel[j, o] * model.Dint_CC_parallel[j, o] / 4 -
                model.M_lineCC_parallel[j, o]
            )
            return pe.inequality(
                - model.M_bigM * (1 - model.Y_lineCC_parallel[j, o]),
                valeur,
                model.M_bigM * (1 - model.Y_lineCC_parallel[j, o])
            )
        self.model.Def_V_lineCC_parallel_bigM = pe.Constraint(
            self.model.j, self.model.o, rule=Def_V_lineCC_parallel_rule_bigM)

        def Def_V_lineCC_return_rule_bigM(model, o, j):
            """Inéquation du bigM sur le débit entre consommateurs - RETOUR"""
            valeur = (
                model.V_lineCC_return[o, j] * model.rho * math. pi *
                model.Dint_CC_return[o, j] * model.Dint_CC_return[o, j] / 4 -
                model.M_lineCC_return[o, j]
            )
            return pe.inequality(
                - model.M_bigM * (1 - model.Y_lineCC_return[o, j]),
                valeur,
                model.M_bigM * (1 - model.Y_lineCC_return[o, j])
            )
        self.model.Def_V_lineCC_return_bigM = pe.Constraint(
            self.model.o, self.model.j, rule=Def_V_lineCC_return_rule_bigM)

        # Vitesses maximales et minimales
        def Ex_V_linePC_max_rule(model, i, j):
            """Permet de definir une vitesse min/max que si la canalisation existe"""
            return model.V_linePC[i, j] <= model.V_max * model.Y_linePC[i, j]
        self.model.Ex_V_linePC_max = pe.Constraint(
            self.model.i, self.model.j, rule=Ex_V_linePC_max_rule)

        def Ex_V_linePC_min_rule(model, i, j):
            """Permet de definir une vitesse min/max que si la canalisation existe"""
            return model.V_linePC[i, j] >= model.V_min * model.Y_linePC[i, j]
        self.model.Ex_V_linePC_min = pe.Constraint(
            self.model.i, self.model.j, rule=Ex_V_linePC_min_rule)

        def Ex_V_lineCP_max_rule(model, j, i):
            """Permet de definir une vitesse min/max que si la canalisation existe"""
            return model.V_lineCP[j, i] <= model.V_max * model.Y_lineCP[j, i]
        self.model.Ex_V_lineCP_max = pe.Constraint(
            self.model.j, self.model.i, rule=Ex_V_lineCP_max_rule)

        def Ex_V_lineCP_min_rule(model, j, i):
            """Permet de definir une vitesse min/max que si la canalisation existe"""
            return model.V_lineCP[j, i] >= model.V_min * model.Y_lineCP[j, i]
        self.model.Ex_V_lineCP_min = pe.Constraint(
            self.model.j, self.model.i, rule=Ex_V_lineCP_min_rule)

        def Ex_V_lineCC_parallel_max_rule(model, j, o):
            """Permet de definir une vitesse min/max que si la canalisation existe"""
            return model.V_lineCC_parallel[j, o] <= model.V_max * model.Y_lineCC_parallel[j, o]
        self.model.Ex_V_lineCC_parallel_max = pe.Constraint(
            self.model.j, self.model.o, rule=Ex_V_lineCC_parallel_max_rule)

        def Ex_V_lineCC_parallel_min_rule(model, j, o):
            """Permet de definir une vitesse min/max que si la canalisation existe"""
            return model.V_lineCC_parallel[j, o] >= model.V_min * model.Y_lineCC_parallel[j, o]
        self.model.Ex_V_lineCC_parallel_min = pe.Constraint(
            self.model.j, self.model.o, rule=Ex_V_lineCC_parallel_min_rule)

        def Ex_V_lineCC_return_max_rule(model, o, j):
            """Permet de definir une vitesse min/max que si la canalisation existe"""
            return model.V_lineCC_return[o, j] <= model.V_max * model.Y_lineCC_return[o, j]
        self.model.Ex_V_lineCC_return_max = pe.Constraint(
            self.model.o, self.model.j, rule=Ex_V_lineCC_return_max_rule)

        def Ex_V_lineCC_return_min_rule(model, o, j):
            """Permet de definir une vitesse min/max que si la canalisation existe"""
            return model.V_lineCC_return[o, j] >= model.V_min * model.Y_lineCC_return[o, j]
        self.model.Ex_V_lineCC_return_min = pe.Constraint(
            self.model.o, self.model.j, rule=Ex_V_lineCC_return_min_rule)

        # Definition de débits maximaux et minimaux si la canalisation existe
        # Si la canalisations n'existe pas le débit est nul
        def Ex_M_prod_max_rule(model, i, k):
            """Débit maximal pour chaque technologies k"""
            return model.M_prod[i, k] <= model.M_max * model.Y_P[i, k]
        self.model.Ex_M_prod_max = pe.Constraint(
            self.model.i, self.model.k, rule=Ex_M_prod_max_rule)

        def Ex_M_prod_min_rule(model, i, k):
            """Débit minimal pour chaque technologies k"""
            return model.M_prod[i, k] >= model.M_min * model.Y_P[i, k]
        self.model.Ex_M_prod_min = pe.Constraint(
            self.model.i, self.model.k, rule=Ex_M_prod_min_rule)

        def Ex_M_linePC_max_rule(model, i, j):
            """Débit maximal dans les canalisations entre producteurs et consommateurs - ALLER"""
            return model.M_linePC[i, j] <= model.M_max * model.Y_linePC[i, j]
        self.model.Ex_M_linePC_max = pe.Constraint(
            self.model.i, self.model.j, rule=Ex_M_linePC_max_rule)

        def Ex_M_lineCP_max_rule(model, j, i):
            """Débit maximal dans les canalisations entre producteurs et consommateurs - RETOUR"""
            return model.M_lineCP[j, i] <= model.M_max * model.Y_lineCP[j, i]
        self.model.Ex_M_lineCP_max = pe.Constraint(
            self.model.j, self.model.i, rule=Ex_M_lineCP_max_rule)

        def Ex_M_lineCC_parallel_max_rule(model, j, o):
            """Débit maximal dans les canalisations entre consommateurs - ALLER"""
            return model.M_lineCC_parallel[j, o] <= model.M_max * model.Y_lineCC_parallel[j, o]
        self.model.Ex_M_lineCC_parallel_max = pe.Constraint(
            self.model.j, self.model.o, rule=Ex_M_lineCC_parallel_max_rule)

        def Ex_M_lineCC_return_max_rule(model, o, j):
            """Débit maximal dans les canalisations entre consommateurs - RETOUR"""
            return model.M_lineCC_return[o, j] <= model.M_max * model.Y_lineCC_return[o, j]
        self.model.Ex_M_lineCC_return_max = pe.Constraint(
            self.model.o, self.model.j, rule=Ex_M_lineCC_return_max_rule)

        # BILAN DE MASSE
        def bilanA_debit_supply_rule(model, j):
            """Bilan de masse au point A d'un noeud consommateur
            Un consommateur (M_supply) peut être alimenté par un producteur (M_linePC)
            ou un autre consommateur (M_lineCC_parallel).
            """
            return model.M_supply[j] == (
                sum(model.M_linePC[i, j] for i in model.i) +
                sum(model.M_lineCC_parallel[o, j] for o in model.o if o != j)
            )
        self.model.bilanA_debit_supply = pe.Constraint(self.model.j, rule=bilanA_debit_supply_rule)

        def bilanB_debit_hx_in_rule(model, j):
            """Bilan de masse au point B d'un noeud consommateur
            Seule une partie du débit (M_supply) alimente le consommateur (M_hx),
            le reste part vers une autre consommateur (M_lineCC_parallel),
            sauf s'il est en fin de réseau et dans ce cas M_supply = M_hx
            """
            return model.M_supply[j] == (
                model.M_hx[j] +
                sum(model.M_lineCC_parallel[j, o] for o in model.o if o != j)
            )
        self.model.bilanB_debit_hx_in = pe.Constraint(self.model.j, rule=bilanB_debit_hx_in_rule)

        def bilanD_debit_hx_out_rule(model, j):
            """Bilan de masse au point D d'un noeud consommateur
            Le débit (M_return) à chaque consommateur est composé
            du débit en sortie de l'échangeur (M_hx) et du débit de retour des
            autres consommateurs (M_lineCC_return),
            sauf s'il est en fin de réseau et dans ce cas M_return = M_hx
            """
            return model.M_return[j] == (
                model.M_hx[j] +
                sum(model.M_lineCC_return[o, j] for o in model.o if o != j)
            )
        self.model.bilanD_debit_hx_out = pe.Constraint(self.model.j, rule=bilanD_debit_hx_out_rule)

        def bilanE_debit_return_rule(model, j):
            """Bilan de masse au point E d'un noeud consommateur
            Après le point D, le débit (M_return) peut soit retourner vers
            la production (M_lineCP) soit vers un autre consommateur (M_lineCC_return)
            """
            return model.M_return[j] == (
                sum(model.M_lineCP[j, i] for i in model.i) +
                sum(model.M_lineCC_return[j, o] for o in model.o if o != j)
            )
        self.model.bilanE_debit_return = pe.Constraint(self.model.j, rule=bilanE_debit_return_rule)

        def bilanF_debit_prod_tot_in_rule(model, i):
            """Bilan de masse au point F d'un noeud producteur
            La débit de retour à la production (M_prod_tot) est égal
            au débit de retour du ou des derniers consommateurs par branche (M_lineCP)
            """
            return model.M_prod_tot[i] == sum(model.M_lineCP[j, i] for j in model.j)
        self.model.bilanF_debit_prod_tot_in = pe.Constraint(
            self.model.i, rule=bilanF_debit_prod_tot_in_rule)

        def bilanI_debit_prod_tot_out_rule(model, i):
            """Bilan de masse au point I d'un noeud producteur
            La débit de départ à la production (M_prod_tot) est égal
            aux débits partants vers les premiers consommateurs par branche (M_linePC)
            """
            return model.M_prod_tot[i] == sum(model.M_linePC[i, j] for j in model.j)
        self.model.bilanI_debit_prod_tot_out = pe.Constraint(
            self.model.i, rule=bilanI_debit_prod_tot_out_rule)

        def bilanGH_debit_prod_out_rule(model, i):
            """Bilan de masse aux points G et H d'un noeud producteur
            Le débit total partant/rentrant de la production i est égal
            à la somme des débit de chaque unité de production k associés
            """
            return model.M_prod_tot[i] == sum(model.M_prod[i, k] for k in model.k)
        self.model.bilanGH_debit_prod_out = pe.Constraint(
            self.model.i, rule=bilanGH_debit_prod_out_rule)

        # BILAN D'ENERGIE ET EGALITE DE TEMPERATURE
        def bilanA_H_supply_rule(model, j):
            """Bilan d'énergie au point A d'un noeud consommateur (point convergent)"""
            return model.M_supply[j] * model.T_supply[j] == (
                sum(model.M_linePC[i, j] * model.T_linePC_out[i, j] for i in model.i) +
                sum(model.M_lineCC_parallel[o, j] * model.T_lineCC_parallel_out[o, j]
                    for o in model.o if o != j)
            )
        self.model.bilanA_H_supply = pe.Constraint(self.model.j, rule=bilanA_H_supply_rule)

        def bilanB_T_hx_in_rule_bigM(model, j, o):
            """Première égalité de température au point B d'un noeud consommateur (point divergent)

            Tsupply = TlineCC_parallel
            Inéquation du bigM
            """
            valeur = model.T_supply[j] - model.T_lineCC_parallel_in[j, o]
            return pe.inequality(
                - model.T_bigM * (1 - model.Y_lineCC_parallel[j, o]),
                valeur,
                model.T_bigM * (1 - model.Y_lineCC_parallel[j, o])
            )
        self.model.bilanB_T_hx_in_bigM = pe.Constraint(
            self.model.j, self.model.o, rule=bilanB_T_hx_in_rule_bigM)

        def bilanB2_T_hx_in_rule(model, j):
            """Deuxième égalité de température au point B d'un noeud consommateur (point divergent)

            Tsupply = Thx
            Pas de bigM car si le consommateur existe l'échangeur est forcément alimenté alors
            que la liaison avec un autre consommateur (TlineCC_parallel) n'existe pas forcément
            """
            return model.T_hx_in[j] == model.T_supply[j]
        self.model.bilanB2_T_hx_in = pe.Constraint(self.model.j, rule=bilanB2_T_hx_in_rule)

        def bilanD_H_hx_out_rule(model, j):
            """Bilan d'énergie au point D d'un noeud consommateur (point convergent)"""
            return model.M_return[j] * model.T_return[j] == (
                model.M_hx[j] * model.T_hx_out[j] +
                sum(model.M_lineCC_return[o, j] * model.T_lineCC_return_out[o, j]
                    for o in model.o if o != j)
            )
        self.model.bilanD_H_hx_out = pe.Constraint(self.model.j, rule=bilanD_H_hx_out_rule)

        def bilanE_T_return_rule_bigM(model, i, j):
            """Première égalité de température au point E d'un noeud consommateur (point divergent)

            Treturn = TlineCP
            Inéquation du bigM
            """
            valeur = model.T_return[j] - model.T_lineCP_in[j, i]
            return pe.inequality(
                - model.T_bigM * (1 - model.Y_lineCP[j, i]),
                valeur,
                model.T_bigM * (1 - model.Y_lineCP[j, i])
            )
        self.model.bilanE_T_return_bigM = pe.Constraint(
            self.model.i, self.model.j, rule=bilanE_T_return_rule_bigM)

        def bilanE2_T_return_rule_bigM(model, o, j):
            """Deuxième égalité de température au point E d'un noeud consommateur (point divergent)

            Treturn = T_lineCC_return
            Inéquation du bigM
            """
            valeur = model.T_return[o] - model.T_lineCC_return_in[o, j]
            return pe.inequality(
                - model.T_bigM * (1 - model.Y_lineCC_return[o, j]),
                valeur,
                model.T_bigM * (1 - model.Y_lineCC_return[o, j])
            )
        self.model.bilanE2_T_return_bigM = pe.Constraint(
            self.model.o, self.model.j, rule=bilanE2_T_return_rule_bigM)

        def bilanF_H_prod_tot_in_rule(model, i):
            """Bilan d'énergie au point F d'un noeud producteur (point convergent)"""
            return model.M_prod_tot[i] * model.T_prod_tot_in[i] == (
                sum(model.M_lineCP[j, i] * model.T_lineCP_out[j, i] for j in model.j)
            )
        self.model.bilanF_H_prod_tot_in = pe.Constraint(
            self.model.i, rule=bilanF_H_prod_tot_in_rule)

        def bilanH_H_prod_out_rule(model, i):
            """Bilan d'énergie au point H d'un noeud producteur (point convergent)

            Mélange des fluides provenant des technologies k à la production i
            """
            return model.M_prod_tot[i] * model.T_prod_tot_out[i] == (
                sum(model.M_prod[i, k] * model.T_prod_out[i, k] for k in model.k)
            )
        self.model.bilanH_H_prod_out = pe.Constraint(
            self.model.i, rule=bilanH_H_prod_out_rule)

        def bilanI_T_prod_tot_out_rule_bigM(model, i, j):
            """Egalité de température au point I d'un noeud producteur (point divergent)

            La production peut alimenter ou non les consommateurs
            Inéquation du bigM
            """
            valeur = model.T_linePC_in[i, j] - model.T_prod_tot_out[i]
            return pe.inequality(
                - model.T_bigM * (1 - model.Y_linePC[i, j]),
                valeur,
                model.T_bigM * (1 - model.Y_linePC[i, j])
            )
        self.model.bilanI_T_prod_tot_out_bigM = pe.Constraint(
            self.model.i, self.model.j, rule=bilanI_T_prod_tot_out_rule_bigM)

        def bilan_H_inst_rule_bigM1(model, i, k):
            """Bilan de chaleur à la production si elle existent
            Puissance à installer * efficacité = Puissance requise
            Inéquation 1 du bigM
            """
            return (
                model.H_inst[i, k] * model.Eff[k] / model.simultaneity_rate <=
                model.M_prod[i, k] * model.Cp * (model.T_prod_out[i, k] - model.T_prod_tot_in[i]) +
                model.H_inst_bigM * (1 - model.Y_P[i, k])
            )
        self.model.bilan_H_inst_bigM1 = pe.Constraint(
            self.model.i, self.model.k, rule=bilan_H_inst_rule_bigM1)

        def bilan_H_inst_rule_bigM2(model, i, k):
            """..... Inéquation 2 du bigM"""
            return (
                model.H_inst[i, k] * model.Eff[k] / model.simultaneity_rate >=
                model.M_prod[i, k] * model.Cp * (model.T_prod_out[i, k] - model.T_prod_tot_in[i]) -
                model.H_inst_bigM * (1 - model.Y_P[i, k])
            )
        self.model.bilan_H_inst_bigM2 = pe.Constraint(
            self.model.i, self.model.k, rule=bilan_H_inst_rule_bigM2)

        def bilan_chaleur_HX_rule(model, j):
            """Bilan de chaleur pour chaque consommateur
            Pas de bigM, un consommateur est forcément alimenté
            Puissance requise = débit * Cp * delta T
            Inéquation 1 du bigM"""
            # TODO: Constraint "T_hx_out == T_hx_in" brings convergence issues. Why ?
            # if not has_power_demand(j):
            #     return model.T_hx_out[j] == model.T_hx_in[j]
            return model.H_hx[j] == (
                model.M_hx[j] * model.Cp * (model.T_hx_in[j] - model.T_hx_out[j]))
        self.model.bilan_chaleur_HX = pe.Constraint(self.model.j, rule=bilan_chaleur_HX_rule)

        def bilan_DT1_rule(model, j):
            """Delta T côté chaud de l'échangeur (DT1)

            = entrée au primaire - sortie au secondaire
            """
            if not has_power_demand(j):
                return pe.Constraint.Feasible
            return model.DT1[j] == model.T_hx_in[j] - model.T_req_out[j]
        self.model.bilan_DT1 = pe.Constraint(self.model.j, rule=bilan_DT1_rule)

        def bilan_DT2_rule(model, j):
            """Delta T côté froid de l'échangeur (DT2)

            = sortie au primaire - entrée au secondaire
            """
            if not has_power_demand(j):
                return pe.Constraint.Feasible
            return model.DT2[j] == model.T_hx_out[j] - model.T_req_in[j]
        self.model.bilan_DT2 = pe.Constraint(self.model.j, rule=bilan_DT2_rule)

        def bilan_DT1_pinch_rule(model, j):
            """DT1 doit être supérieur au pincement minimun par définition"""
            if not has_power_demand(j):
                return pe.Constraint.Feasible
            return model.DT1[j] >= model.T_hx_pinch
        self.model.bilan_DT1_pinch = pe.Constraint(self.model.j, rule=bilan_DT1_pinch_rule)

        def bilan_DT2_pinch_rule(model, j):
            """DT2 doit être supérieur au pincement minimum par définition"""
            if not has_power_demand(j):
                return pe.Constraint.Feasible
            return model.DT2[j] >= model.T_hx_pinch
        self.model.bilan_DT2_pinch = pe.Constraint(self.model.j, rule=bilan_DT2_pinch_rule)

        def diffTemplog_rule(model, j):
            """Calcul de la DTLM

            Différence logarithmique de température à l’échangeur de chaleur (°C)
            """
            if not has_power_demand(j):
                return pe.Constraint.Feasible
            return model.DTLM[j] == (
                model.DT1[j] * model.DT2[j] * 0.5 * (model.DT1[j] + model.DT2[j])
            ) ** (1 / 3)
        self.model.diffTemplog = pe.Constraint(self.model.j, rule=diffTemplog_rule)

        def bilan_chaleur_HX_DTLM_rule(model, j):
            """Bilan de puissance à l'échangeur

            Avec le DTLM qui dépend des températures au primaire et secondaire
            H = coeff_échange * surface * DTLM"""
            if not has_power_demand(j):
                return pe.Constraint.Feasible
            return model.H_hx[j] == model.A_hx[j] * model.K_hx * model.DTLM[j]
        self.model.bilan_chaleur_HX_DTLM = pe.Constraint(
            self.model.j, rule=bilan_chaleur_HX_DTLM_rule)

        # Pertes thermiques (ici négligées car T_in = T_out)
        def loss_linePC_rule(model, i, j):
            """Pertes thermiques sur les conduites entre producteur et consommateur - ALLER"""
            return model.T_linePC_out[i, j] == (
                model.T_linePC_in[i, j] -
                model.linear_heat_loss * model.L_PC[i, j]
            )
        self.model.loss_linePC = pe.Constraint(self.model.i, self.model.j, rule=loss_linePC_rule)

        def loss_lineCP_rule(model, j, i):
            """Pertes thermiques sur les conduites entre producteur et consommateur - RETOUR"""
            return model.T_lineCP_out[j, i] == (
                model.T_lineCP_in[j, i] -
                model.linear_heat_loss * model.L_CP[j, i]
            )
        self.model.loss_lineCP = pe.Constraint(self.model.j, self.model.i, rule=loss_lineCP_rule)

        def loss_lineCC_parallel_rule(model, j, o):
            """Pertes thermiques sur les conduites entre consommateur - ALLER"""
            return model.T_lineCC_parallel_out[j, o] == (
                model.T_lineCC_parallel_in[j, o] -
                model.linear_heat_loss * model.L_CC_parallel[j, o]
            )
        self.model.loss_lineCC_parallel = pe.Constraint(
            self.model.j, self.model.o, rule=loss_lineCC_parallel_rule)

        def loss_lineCC_return_rule(model, o, j):
            """Pertes thermiques sur les conduites entre consommateurs - RETOUR"""
            return model.T_lineCC_return_out[o, j] == (
                model.T_lineCC_return_in[o, j] -
                model.linear_heat_loss * model.L_CC_return[j, o]
            )
        self.model.loss_lineCC_return = pe.Constraint(
            self.model.o, self.model.j, rule=loss_lineCC_return_rule)

        # Contrainte à l'échangeur
        def contrainte_appro_rule(model, j):
            """La puissance à l'échangeur doit être égale à celle entrée par l'utilisateur"""
            return model.H_hx[j] == model.H_req[j]
        self.model.contrainte_appro = pe.Constraint(self.model.j, rule=contrainte_appro_rule)

        # Contrainte sur la couverture
        def contrainte_coverage_rule(model, i, k):
            """Taux de couverture de la production principale"""
            if model.coverage_rate[k] is None:
                return pe.Constraint.Feasible
            return model.H_inst[i, k] == (
                model.coverage_rate[k] * sum(model.H_inst[i, k] for k in model.k))
        self.model.contrainte_coverage = pe.Constraint(
            self.model.i, self.model.k, rule=contrainte_coverage_rule)

        # Objective

        # Termes de la fonction coût
        def cout_pompage_rule(model):
            """Coût de pompage"""
            return model.C_pump == model.C_pump_ratio * (model.C_heat + model.C_pump)
        self.model.cout_pompage = pe.Constraint(rule=cout_pompage_rule)

        def cout_heat_rule(model):
            """Coût de la chaleur livrée"""
            return model.C_heat == (
                1.e-6 * model.period * model.simultaneity_rate * (1 + model.heat_loss_rate) * sum(
                    model.f_opex[k] * model.C_heat_unit[k] * model.H_inst[i, k]
                    for i in model.i for k in model.k)
            )
        self.model.cout_heat = pe.Constraint(rule=cout_heat_rule)

        def cout_puissance_rule(model):
            """Coût de la puissance installée en chaufferie"""
            return model.C_Hinst == (
                1.e-6 * model.f_capex * sum(
                    model.C_Hprod_unit[k] * sum(model.H_inst[i, k] for k in model.k)
                    for i in model.i for k in model.k)
            )
        self.model.cout_puissance = pe.Constraint(rule=cout_puissance_rule)

        def cout_echangeur_rule(model):
            """Coût des échangeurs"""
            return model.C_hx == 1.e-6 * model.f_capex * sum(
                model.C_hx_unit_a * model.H_hx[j] + model.C_hx_unit_b for j in model.j)
        self.model.cout_echangeur = pe.Constraint(rule=cout_echangeur_rule)

        def cout_canalisation_tuyau_rule(model):
            """Coût des tuyaux pré-isolés"""
            return model.C_pipe == 1.e-6 * model.f_capex * (
                sum(model.L_PC[i, j] *
                    (model.C_pipe_unit_a * model.Dint_PC[i, j] + model.C_pipe_unit_b)
                    for i in model.i for j in model.j) +
                sum(model.L_CP[j, i] *
                    (model.C_pipe_unit_a * model.Dint_CP[j, i] + model.C_pipe_unit_b)
                    for j in model.j for i in model.i) +
                sum(model.L_CC_parallel[j, o] *
                    (model.C_pipe_unit_a * model.Dint_CC_parallel[j, o] + model.C_pipe_unit_b)
                    for j in model.j for o in model.o) +
                sum(model.L_CC_return[j, o] *
                    (model.C_pipe_unit_a * model.Dint_CC_return[j, o] + model.C_pipe_unit_b)
                    for j in model.j for o in model.o)
            )
        self.model.cout_canalisation_tuyau = pe.Constraint(rule=cout_canalisation_tuyau_rule)

        def cout_canalisation_tranchee_rule(model):
            """Coût de tranchée"""
            return model.C_tr == 1.e-6 * model.f_capex * model.C_tr_unit / 2 * (
                sum(model.L_PC[i, j] for i in model.i for j in model.j) +
                sum(model.L_CP[j, i] for j in model.j for i in model.i) +
                sum(model.L_CC_parallel[j, o] for j in model.j for o in model.o) +
                sum(model.L_CC_return[j, o] for j in model.j for o in model.o)
            )
        self.model.cout_canalisation_tranchee = pe.Constraint(rule=cout_canalisation_tranchee_rule)

        def cout_canalisation_tot_rule(model):
            """Coût total de canalisation: tuyaux + tranchée"""
            return model.C_line_tot == model.C_pipe + model.C_tr
        self.model.cout_canalisation_tot = pe.Constraint(rule=cout_canalisation_tot_rule)

        # Longueur totale du réseau
        def Ex_L_tot_rule(model):
            """Correspond à la somme de tous les tuyaux posés
            soit 2 fois la longueur de tranchée car tuyau aller-retour
            """
            return model.L_tot == (
                sum(model.L_PC[i, j] for i in model.i for j in model.j) +
                sum(model.L_CP[j, i] for j in model.j for i in model.i) +
                sum(model.L_CC_parallel[j, o] for j in model.j for o in model.o) +
                sum(model.L_CC_return[j, o] for j in model.j for o in model.o)
            )
        self.model.Ex_L_tot = pe.Constraint(rule=Ex_L_tot_rule)

        def objective_rule(model):
            """Sommes des termes coût"""
            return (
                model.C_heat + model.C_Hinst + model.C_hx + model.C_line_tot +
                # XXX: Adding rate flows to costs
                sum(model.M_prod_tot[i] for i in model.i)
            )
        self.model.objective = pe.Objective(rule=objective_rule, sense=pe.minimize)
