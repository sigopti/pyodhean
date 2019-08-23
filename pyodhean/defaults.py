"""Default values"""


DEFAULT_PARAMETERS = {
    # capacite thermique de l'eau à 80°C (kJ/kg.K)
    'water_cp': 4.196,
    # viscosite de l'eau a 80°C (Pa.s)
    'water_mu': 0.000354,
    # masse volumique de l'eau a 20°C (kg/m3)
    'water_rho': 974,
    # pression max en borne supérieure (kPa)
    'pressure_max': 500,
    # borne vitesse min, 0.1m/s d'après Techniques de l'Ingénieur (m/s)
    'speed_min': 0.1,
    # borne vitesse max, 3m/s d'après Techniques de l'Ingénieur (m/s)
    'speed_max': 3,
    # diamètre interieur max du tuyau (m)
    'diameter_int_min': 0.01,
    # diamètre interieur max du tuyau (m)
    'diameter_int_max': 0.25,
    # épaisseur de metal dependant du diametre (m)
    'pipe_thickness': 0.025,
    # épaisseur de l'isolant autour de la canalisation (m)
    'pipe_insulation_thickness': 0.0276,
    # coefficient global d'échange (kW/m2.K)
    'exchanger_overall_transfer_coefficient': 20,
    # température de pincement minimum a l'échangeur (°C)
    'exchanger_t_pinch_min': 5,
    # rendement de la pompe pour le calcul du coût de pompage(%)
    'pump_efficiency': 0.7,
    # durée de fonctionnement annuelle du RCU (h)
    'operation_time': 5808,
    # duree d'amortissement (année)
    'depreciation_period': 15,
    # taux d'actualisation pour le calcul de l'annuite des investissements initiaux
    'discout_rate': 0.04,
    # coût unitaire de tranchee aller-retour (€/ml)
    'trench_unit_cost': 800,
    # coefficient directeur de la relation linéaire du coût de la canalisation
    # selon le diamètre (ensemble tuyau+isolant)(€/m)
    'pipe_diameter_unit_cost_slope': 0.3722,
    # ordonnée à l'origine de la relation linéaire du coût de la canalisation
    # selon le diamètre (ensemble tuyau+isolant)(€)
    'pipe_diameter_unit_cost_y_intercept': 12.48,
    # coefficient directeur du coût unitaire de l'echangeur (€/kW )
    'exchanger_power_cost_slope': 5.3,
    # ordonnee à l'origine du coût unitaire de l'echangeur (€)
    'exchanger_power_cost_y_intercept': 5045,
    # coût unitaire de l'électricite pour le pompage (€/kWh)
    'pump_energy_unit_cost': 0.11,
    # inflation du coût de l'électricite pour le pompage (%)
    'pump_energy_cost_inflation_rate': 0.04,
}
