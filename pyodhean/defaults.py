"""Default values"""


DEFAULT_PARAMETERS = {
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
    # coefficient directeur de la relation linéaire du coût de la canalisation
    # selon le diamètre (ensemble tuyau+isolant)(€/m)
    'C_pipe_unit_a': 0.3722,
    # ordonnée à l\'origine de la relation linéaire du coût de la canalisation
    # selon le diamètre (ensemble tuyau+isolant)(€)
    'C_pipe_unit_b': 12.48,
    # coefficient directeur du coût unitaire de l\'echangeur (€/kW )
    'C_hx_unit_a': 5.3,
    # ordonnee à l\'origine du coût unitaire de l\'echangeur (€)
    'C_hx_unit_b': 5045,
    # taux d\'actualisation pour le calcul de l\'annuite des investissements initiaux
    'rate_a': 0.04,
    # épaisseur de l\'isolant autour de la canalisation (m)
    'tk_insul': 0.0276,
    # épaisseur de metal dependant du diametre (m)
    'tk_pipe': 0.025,
    # borne vitesse min, 0.1m/s d\'après Techniques de l\'Ingénieur (m/s)
    'V_min': 0.1,
    # borne vitesse max, 3m/s d\'après Techniques de l\'Ingénieur (m/s)
    'V_max': 3,
    # pression max en borne supérieure (kPa)
    'P_max': 500,
    # diamètre interieur max du tuyau (m)
    'Dint_max': 0.25,
    # diamètre interieur max du tuyau (m)
    'Dint_min': 0.01,
}
