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

general_parameters = {
    # coût unitaire de tranchee aller-retour (€/ml)
    'C_tr_unit': 800,
    # durée de fonctionnement annuelle du RCU (h)
    'period': 5808,
    # duree d'amortissement (année)
    'depreciation_period': 15,
    # inflation du coût de l'électricite pour le pompage (%)
    'rate_i_pump': 0.04,
    # rendement de la pompe pour le calcul du coût de pompage(%)
    'Eff_pump': 0.7,
    # température de pincement minimum a l\'échangeur (°C)
    'T_hx_pinch': 5,
    # coefficient global d\'échange (kW/m2.K)
    'K_hx': 20,
    # capacite thermique de l\'eau à 80°C (kJ/kg.K)
    'Cp': 4.196,
    # coût unitaire de l\'électricite pour le pompage (€/kWh)
    'C_pump_unit': 0.11,
    # viscosite de l\'eau a 80°C (Pa.s)
    'mu': 0.000354,
    # masse volumique de l\'eau a 20°C (kg/m3)
    'rho': 974,
    # exposant pour le calcul des pertes de charge et le calcul du coût de pompage
    'alpha': 1.75,
    # exposant pour le calcul des pertes de charge et le calcul du coût de pompage
    'beta': -1.25,
    # coefficient directeur de la relation linéaire du coût de la canalisation selon le diamètre (ensemble tuyau+isolant)(€/m)
    'C_pipe_unit_a': 0.3722,
    # ordonnée à l\'origine de la relation linéaire du coût de la canalisationselon le diamètre (ensemble tuyau+isolant)(€)
    'C_pipe_unit_b': 12.48,
    # coefficient directeur du coût unitaire de l\'echangeur (€/kW )
    'C_hx_unit_a': 5.3,
    # ordonnee à l\'origine du coût unitaire de l\'echangeur (€)
    'C_hx_unit_b': 5045,
    # taux d\'actualisation pour le calcul de l\'annuite des investissements initiaux
    'rate_a': 0.04,
    # température extérieure pour le calcul des pertes thermiques de la canalisation
    'T_ext': 15,
    # conductivite thermique de l\'isolant (W/m.K)
    'lambda_insul': 0.03,
    # conductivite thermique du sol (W/m.K)
    'lambda_soil': 1.4,
    # hauteur de sol au dessus des canalisations pour le calcul des pertes thermiques (m)
    'z_pipe': 0.4,
    # chiffre infinitesimal utile pour éviter les erreurs de division par zero
    'epsilon': 0.000000001,
    # épaisseur de l\'isolant autour de la canalisation (m)
    'tk_insul': 0.0276,
    # épaisseur de metal dependant du diametre (m)
    'tk_pipe': 0.025,
    # perte de charge dans un echangeur (kPa)
    'DP_hx_unit': 20,
    # borne vitesse min, 0.1m/s d\'après Techniques de l\'Ingénieur (m/s)
    'V_min': 0.1,
    # borne vitesse max, 3m/s d\'après Techniques de l\'Ingénieur (m/s)
    'V_max': 3,
    # pression minimale en borne inférieure (kPa)
    'P_min': 120,
    # pression max en borne supérieure (kPa)
    'P_max': 500,
    # diamètre interieur max du tuyau (m)
    'Dint_max': 0.25,
    # diamètre interieur max du tuyau (m)
    'Dint_min': 0.01,
    # distance max pour borner les longueurs de canalisations (m)
    'Dist_max_autorisee': 1000,
}

technologies = {
    'k1': {
        'C_Hprod_unit': 800,
        'C_heat_unit': 0.08,
        'Eff': 0.9,
        'rate_i': 0.04,
        'T_prod_out_max': 100,
        'T_prod_in_min': 30,
    },
}

production = {
    'P1': {'x': 0, 'y': 0},
}

consumption = {
    'C1': {
        'x': 60, 'y': 40,
        'H_req': 80,
        'T_req_out': 60,
        'T_req_in': 80,
    },
    'C2': {
        'x': 0, 'y': 40,
        'H_req': 80,
        'T_req_out': 60,
        'T_req_in': 80,
    },
}

model = Model(
    general_parameters=general_parameters,
    technologies=technologies,
    production=production,
    consumption=consumption,
)

print('### Solve ###\n')
model.solve(options)
print('')

print('### Display ###\n')
model.display()

model.write_solution('./solution.txt')
