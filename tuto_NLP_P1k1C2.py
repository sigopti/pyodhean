from math import pi

import pyomo.environ as pe

# Creation d'un cas d'étude
model = pe.ConcreteModel()

#-----------------------------------------------------------------------------------------#
########################################### SET ###########################################
#-----------------------------------------------------------------------------------------#

# Définition des indices
model.i = pe.Set(initialize=['P1'], doc='indice des noeuds producteurs')
model.j = pe.Set(initialize=['C1','C2'], doc='indice des noeuds consommateurs')
model.o = pe.Set(initialize=['C1','C2'], doc='indice des noeuds consommateurs')
model.k = pe.Set(initialize=['k1'], doc='indice technologie de production')

#-----------------------------------------------------------------------------------------#
######################################### PARAMETER #######################################
#-----------------------------------------------------------------------------------------#

# Définition des paramètres dépendant de la taille du problème
model.C_tr_unit = pe.Param(initialize=800, doc='coût unitaire de tranchee aller-retour (€/ml)')
model.period = pe.Param(initialize=5808, doc='durée de fonctionnement annuelle du RCU (h)')
model.annee = pe.Param(initialize=15, doc='duree d\'amortissement (année)')
model.x_P = pe.Param(model.i, initialize={'P1':0}, doc='abscisse d\'un noeud producteur (m)')
model.z_P = pe.Param(model.i, initialize={'P1':0}, doc='ordonnée d\'un noeud producteur (m)')
model.C_Hprod_unit = pe.Param(model.k,initialize={'k1':800}, doc='coût unitaire  de la chaudiere installée (€/kW)')
model.C_heat_unit = pe.Param(model.k,initialize={'k1':0.08}, doc='coût unitaire de la chaleur suivant l\'énergie de la technologie employee et la periode selon inflation (€/kWh)')
model.Eff = pe.Param(model.k,initialize={'k1':0.9}, doc='rendement de la technologie k (%)')
model.rate_i = pe.Param(model.k,initialize={'k1':0.04}, doc='inflation de l\'énergie liée à la technologie k (%)')
model.rate_i_pump = pe.Param(initialize=0.04, doc='inflation du coût de l\'électricite pour le pompage (%)')
model.x_C = pe.Param(model.j, initialize={'C1':60,'C2':0}, doc='abscisse d\'un noeud consommateur (m)')
model.z_C = pe.Param(model.j, initialize={'C1':40,'C2':40}, doc='ordonnée d\'un noeud consommateur (m)')
model.H_req = pe.Param(model.j, initialize={'C1':80,'C2':80}, doc='besoin de chaleur (kW)')
model.T_req_out = pe.Param(model.j, initialize={'C1':60,'C2':60}, doc='température entree reseau secondaire du consommateur (°C)')
model.T_req_in = pe.Param(model.j, initialize={'C1':80,'C2':80}, doc='température retour reseau secondaire du consommateur (°C)')

# Quelle technologie associée à chaque production ?
table_Y_P = {
    ('P1', 'k1'): 1,
    }

model.Y_P = pe.Param(model.i, model.k, initialize=table_Y_P, doc='Existence techno k au lieu de production Pi')


# Initialisation des canalisations entre producteurs et consommateurs
table_Y_linePC = {
    ('P1', 'C1'): 1,
    ('P1', 'C2'): 0,
    }

model.Y_linePC = pe.Param(model.i, model.j, initialize=table_Y_linePC, doc='Existence canalisation PC')


# Initialisation des canalisations entre consommateurs et producteurs
table_Y_lineCP = {
    ('C1', 'P1'): 1,
    ('C2', 'P1'): 0,
    }
model.Y_lineCP = pe.Param(model.j, model.i, initialize=table_Y_lineCP, doc='Existence canalisation CP')


# Initialisation des canalisations entre consommateurs
## Aller
table_Y_lineCC_parallel = {
    ('C1', 'C1'): 0,
    ('C1', 'C2'): 1,
    ('C2', 'C1'): 0,
    ('C2', 'C2'): 0,
    }
model.Y_lineCC_parallel = pe.Param(model.j, model.o, initialize=table_Y_lineCC_parallel, doc='Existence canalisation CC parallel')

## Retour
table_Y_lineCC_return = {
    ('C1', 'C1'): 0,
    ('C1', 'C2'): 0,
    ('C2', 'C1'): 1,
    ('C2', 'C2'): 0,
    }
model.Y_lineCC_return = pe.Param(model.o, model.j, initialize=table_Y_lineCC_return, doc='Existence canalisation CC return')


# Définition des paramètres ne dépendant pas de la taille du problème
## Valeur affectée
model.Eff_pump = pe.Param(initialize=0.7, doc='rendement de la pompe pour le calcul du coût de pompage(%)')
model.T_hx_pinch = pe.Param(initialize=5, doc='température de pincement minimum a l\'échangeur (°C)')
model.K_hx = pe.Param(initialize=20, doc='coefficient global d\'échange (kW/m2.K)')
model.Cp = pe.Param(initialize=4.196, doc='capacite thermique de l\'eau à 80°C (kJ/kg.K)')
model.C_pump_unit = pe.Param(initialize=0.11, doc='coût unitaire de l\'électricite pour le pompage (€/kWh)')
model.mu = pe.Param(initialize=0.000354, doc='viscosite de l\'eau a 80°C (Pa.s)')
model.rho = pe.Param(initialize=974, doc='masse volumique de l\'eau a 20°C (kg/m3)')
model.alpha = pe.Param(initialize=1.75, doc='exposant pour le calcul des pertes de charge et le calcul du coût de pompage')
model.beta = pe.Param(initialize=-1.25, doc='exposant pour le calcul des pertes de charge et le calcul du coût de pompage')
model.C_pipe_unit_a = pe.Param(initialize=0.3722, doc='coefficient directeur de la relation linéaire du coût de la canalisation selon le diamètre (ensemble tuyau+isolant)(€/m)')
model.C_pipe_unit_b = pe.Param(initialize=12.48, doc='ordonnée à l\'origine de la relation linéaire du coût de la canalisationselon le diamètre (ensemble tuyau+isolant)(€)')
model.C_hx_unit_a = pe.Param(initialize=5.3, doc='coefficient directeur du coût unitaire de l\'echangeur (€/kW )')
model.C_hx_unit_b = pe.Param(initialize=5045, doc='ordonnee à l\'origine du coût unitaire de l\'echangeur (€)')
model.rate_a = pe.Param(initialize=0.04, doc='taux d\'actualisation pour le calcul de l\'annuite des investissements initiaux')
model.T_ext = pe.Param(initialize=15, doc='température extérieure pour le calcul des pertes thermiques de la canalisation')
model.lambda_insul = pe.Param(initialize=0.03, doc='conductivite thermique de l\'isolant (W/m.K)')
model.lambda_soil = pe.Param(initialize=1.4, doc='conductivite thermique du sol (W/m.K)')
model.z_pipe = pe.Param(initialize=0.4, doc='hauteur de sol au dessus des canalisations pour le calcul des pertes thermiques (m)')
model.epsilon = pe.Param(initialize=0.000000001, doc='chiffre infinitesimal utile pour éviter les erreurs de division par zero')
model.tk_insul = pe.Param(initialize=0.0276, doc='épaisseur de l\'isolant autour de la canalisation (m)')
model.tk_pipe = pe.Param(initialize=0.025, doc='épaisseur de metal dependant du diametre (m)')
model.DP_hx_unit = pe.Param(initialize=20, doc='perte de charge dans un echangeur (kPa)')

## bornes
model.V_min = pe.Param(initialize=0.1, doc='borne vitesse min, 0.1m/s d\'après Techniques de l\'Ingénieur (m/s)')
model.V_max = pe.Param(initialize=3, doc='borne vitesse max, 3m/s d\'après Techniques de l\'Ingénieur (m/s)')
model.P_min = pe.Param(initialize=120, doc='pression minimale en borne inférieure (kPa)')
model.P_max = pe.Param(initialize=500, doc='pression max en borne supérieure (kPa)')
model.T_prod_out_max = pe.Param(model.k,initialize={'k1':100}, doc='température max autorisée en sortie de chaudiere de la techno k (°C)')
model.T_prod_in_min = pe.Param(model.k,initialize={'k1':30}, doc='température min autorisée en entree de chaudiere de la techno k (°C)')
model.Dint_max = pe.Param(initialize=0.25, doc='diamètre interieur max du tuyau (m)')
model.Dint_min = pe.Param(initialize=0.01, doc='diamètre interieur max du tuyau (m)')
model.Dist_max_autorisee = pe.Param(initialize=1000, doc='distance max pour borner les longueurs de canalisations (m)')

## Valeur calculée
def calcul_H_inst_max(model):
    """somme des puissances installées de toutes les sous-stations, correspond à la puissance maximale théorique appelée (cas exeptionnel)
    et donc sert de borne max pour la puissance à installer au niveau de la production"""
    return 1.5*sum(model.H_req[j] for j in model.j)
model.H_inst_max = pe.Param(initialize=calcul_H_inst_max)

def calcul_H_inst_bigM(model):
    """BigM associé à la puissance maximale à installer à chaque production
    (valeur commune à toutes les productions potentielles)"""
    return 1000*sum(model.H_req[j] for j in model.j)
model.H_inst_bigM = pe.Param(initialize=calcul_H_inst_bigM)

def calcul_gamma(model):
    """coefficient gamma pour le calcul des pertes de charges du réseau (à combattre par la pompe)
    pour en déduire la puissance de pompage et son coût"""
    return 100/70*((100/model.mu)**(-0.25))/(2*(model.rho**(0.75)))
model.gamma = pe.Param(initialize=calcul_gamma)

def calcul_DistPC(model,i,j):
    """calcul des distances Euclidiennes (à vol d'oiseau) entre chaque producteurs et consommateurs,
    revient à écrire une matrice de dimension i x j contenant les distances,
    toutes les distances existent, que les producteurs-consommateurs soient reliés ou non après optimisation"""
    return ((model.x_C[j]-model.x_P[i])**2 + (model.z_C[j]-model.z_P[i])**2 )**(0.5)
model.Dist_PC = pe.Param(model.i,model.j,initialize=calcul_DistPC)

def calcul_DistCC(model,j,o):
    """calcul des distances Euclidiennes (à vol d'oiseau) entre consommateurs,
    revient à écrire une matrice de dimension j x o contenant les distances donc les termes de la
    diagonale valent 0: on ne calcule pas une distance d'un consommateurs à lui même,
    toutes les distances existent, que les producteurs-consommateurs soient reliés ou non après optimisation"""
    if j != o:
        return ((model.x_C[j]-model.x_C[o])**2 + (model.z_C[j]-model.z_C[o])**2 )**(0.5)
    else:
        return 0
model.Dist_CC = pe.Param(model.j,model.o,initialize=calcul_DistCC)

model.Dist_bigM = pe.Param(initialize=model.Dist_max_autorisee)

def calcul_f_opex(model,k):
    """facteur multiplicateur des coûts operationnels permettant de tenir compte de la somme
     des dépenses annuelles actualisé et suivant l\'inflation de l\'energie et ce par technologie
     de production (électricité/gaz/biomasse/UIOM...)"""
    return (1-(1+model.rate_a)**model.annee*(1+model.rate_i[k])**model.annee)/(1-(1+model.rate_a)*(1+model.rate_i[k]))
model.f_opex = pe.Param(model.k,initialize=calcul_f_opex)

def calcul_f_opex_pump(model):
    """idem pour la pompe, alimentée en électricité"""
    return (1-(1+model.rate_a)**model.annee*(1+model.rate_i_pump)**model.annee)/(1-(1+model.rate_a)*(1+model.rate_i_pump))
model.f_opex_pump = pe.Param(initialize=calcul_f_opex_pump)

def calcul_f_capex(model):
    """facteur multiplicateur pour le calcul du coût d'investissement permettant de tenir compte
    du taux d'actualisation (mais pas d'inflation contraitement aux coûts opex)"""
    return (1+model.rate_a)**model.annee
model.f_capex = pe.Param(initialize=calcul_f_capex)

def calcul_M_max(model):
    """débit maximal dans la canalisation, lié à V_max et Dint_max,
    s'applique à l'ensemble du réseau (productions, échangeurs en sous-station et conduites)"""
    return model.V_max*model.rho*pi*(model.Dint_max**2)/4
model.M_max = pe.Param(initialize=calcul_M_max)

model.M_min = pe.Param(initialize=0, doc='débit minimal dans la canalisation')

def calcul_M_bigM(model):
    """BigM associé au débit maximal pour l'optimisation des débits"""
    return 1000*model.M_max
model.M_bigM = pe.Param(initialize=calcul_M_bigM)

def calcul_T_bigM(model):
    """BigM associé à la température maximale pour l'optimisation des régimes de température
    elle vaut 1000 fois la température de départ maximale des technologies disponibles"""
    return max(model.T_prod_out_max[k] for k in model.k)
model.T_bigM = pe.Param(initialize=calcul_T_bigM)

def calcul_Dout_max(model):
    """calcul du diamètre maximum de canalisation"""
    return model.Dint_max+model.tk_insul+model.tk_pipe
model.Dout_max = pe.Param(initialize=calcul_Dout_max)

def calcul_Dout_min(model):
    """calcul du diamètre minimum de canalisation"""
    return model.Dint_min+model.tk_insul+model.tk_pipe
model.Dout_min = pe.Param(initialize=calcul_Dout_min)

def calcul_R_insul_max(model):
    """calcul de la résistance maximale de l'épaisseur d'isolant"""
    return model.Dint_max/(2*model.lambda_insul)*pe.log(model.Dout_max/model.Dint_max)
model.R_insul_max = pe.Param(initialize=calcul_R_insul_max)

def calcul_R_insul_min(model):
    """calcul de la résistance minimale de l'épaisseur d'isolant"""
    return model.Dint_min/(2*model.lambda_insul)*pe.log(model.Dout_min/model.Dint_min)
model.R_insul_min = pe.Param(initialize=calcul_R_insul_min)

def calcul_R_soil_max(model):
    """calcul de la résistance maximale du sol au dessus des canalisations"""
    return model.Dint_max/(2*model.lambda_soil)*pe.log(4*model.z_pipe/model.Dout_max)
model.R_soil_max = pe.Param(initialize=calcul_R_soil_max)

def calcul_R_soil_min(model):
    """calcul de la résistance minimale du sol au dessus des canalisations"""
    return model.Dint_min/(2*model.lambda_soil)*pe.log(4*model.z_pipe/model.Dout_min)
model.R_soil_min = pe.Param(initialize=calcul_R_soil_min)

def calcul_R_tot_max(model):
    """calcul de la résistance totale maximale"""
    return model.R_insul_max+model.R_soil_max
model.R_tot_max = pe.Param(initialize=calcul_R_tot_max)

def calcul_R_tot_min(model):
    """calcul de la résistance totale minimale"""
    return model.R_insul_min+model.R_soil_min
model.R_tot_min = pe.Param(initialize=calcul_R_tot_min)

def calcul_T_init_min(model):
    """température minimale qui sert de borne inférieure pour les températures de départ/entrée (production, consommateur,
    échangeur, conduites, etc.). Il s'agit de la plus petite température parmis les températures minimales de retour des
    technologies de production et minimales de sortie des consommateurs"""
    return min( min(model.T_prod_in_min[k] for k in model.k) , min(model.T_req_in[j] for j in model.j) )
model.T_init_min = pe.Param(initialize=calcul_T_init_min)

def calcul_T_init_max(model):
    """température maximale qui sert de borne supérieure pour les températures de retour/sortie (production, consommateur,
    échangeur, conduites, etc.). Il s'agit de la plus grande température parmis les températures maximales de départ des
    technologies de production et maximales d'entrée des consommateurs"""
    return max( max(model.T_prod_out_max[k] for k in model.k) , max(model.T_req_out[j] for j in model.j) )
model.T_init_max = pe.Param(initialize=calcul_T_init_max)

## Distances
table_L_PC = {
    ('P1', 'C1'): 10,
    ('P1', 'C2'): 0,
    }

model.L_PC = pe.Param(model.i, model.j, initialize=table_L_PC, doc='matrice des longueurs de canalisations')

table_L_CP = {
    ('C1', 'P1'): 10,
    ('C2', 'P1'): 0,
    }

model.L_CP = pe.Param(model.j, model.i, initialize=table_L_CP, doc='matrice des longueurs de canalisations')

table_L_CC_parallel = {
    ('C1', 'C1'): 0,
    ('C1', 'C2'): 100,
    ('C2', 'C1'): 0,
    ('C2', 'C2'): 0,
    }

model.L_CC_parallel = pe.Param(model.j, model.o, initialize=table_L_CC_parallel, doc='matrice des longueurs de canalisations')

table_L_CC_return = {
    ('C1', 'C1'): 0,
    ('C1', 'C2'): 0,
    ('C2', 'C1'): 100,
    ('C2', 'C2'): 0,
    }

model.L_CC_return = pe.Param(model.o, model.j, initialize=table_L_CC_return, doc='matrice des longueurs de canalisations')

#-----------------------------------------------------------------------------------------#
######################################### VARIABLE ########################################
#-----------------------------------------------------------------------------------------#

# Définition des variables
## vitesses
model.V_linePC = pe.Var(model.i, model.j,initialize=(model.V_min+model.V_max)/2,bounds=(0,model.V_max), doc='vitesses conduites producteurs-consommateurs = ALLER')
model.V_lineCP = pe.Var(model.j, model.i,initialize=(model.V_min+model.V_max)/2,bounds=(0,model.V_max), doc='vitesses conduites consommateurs-producteurs = RETOUR')
model.V_lineCC_parallel = pe.Var(model.j, model.o,initialize=(model.V_min+model.V_max)/2,bounds=(0,model.V_max), doc='vitesses conduites consommateurs-consommateurs ALLER')
model.V_lineCC_return = pe.Var(model.o, model.j,initialize=(model.V_min+model.V_max)/2,bounds=(0,model.V_max), doc='vitesses conduites consommateurs-consommateurs RETOUR')

## Diamètres
model.Dint_PC = pe.Var(model.i, model.j,initialize=(model.Dint_min+model.Dint_max)/2,bounds=(model.Dint_min,model.Dint_max), doc='diamètres intérieurs conduites producteurs-consommateurs = ALLER')
model.Dint_CP = pe.Var(model.j, model.i,initialize=(model.Dint_min+model.Dint_max)/2,bounds=(model.Dint_min,model.Dint_max), doc='diamètres intérieurs conduites consommateurs-producteurs = RETOUR')
model.Dint_CC_parallel = pe.Var(model.j, model.o,initialize=(model.Dint_min+model.Dint_max)/2,bounds=(model.Dint_min,model.Dint_max), doc='diamètres intérieurs conduites consommateurs-consommateurs ALLER')
model.Dint_CC_return = pe.Var(model.o, model.j,initialize=(model.Dint_min+model.Dint_max)/2,bounds=(model.Dint_min,model.Dint_max), doc='diamètres intérieurs conduites consommateurs-consommateurs RETOUR')
model.Dout_PC = pe.Var(model.i, model.j,initialize=(model.Dint_min+model.Dint_max)/2,bounds=(model.Dint_min,model.Dint_max), doc='diamètres extérieurs conduites producteurs-consommateurs = ALLER')
model.Dout_CP = pe.Var(model.j, model.i,initialize=(model.Dint_min+model.Dint_max)/2,bounds=(model.Dint_min,model.Dint_max), doc='diamètres extérieurs conduites consommateurs-producteurs = RETOUR')
model.Dout_CC_parallel = pe.Var(model.j, model.o,initialize=(model.Dint_min+model.Dint_max)/2,bounds=(model.Dint_min,model.Dint_max), doc='diamètres extérieurs conduites consommateurs-consommateurs ALLER')
model.Dout_CC_return = pe.Var(model.o, model.j,initialize=(model.Dint_min+model.Dint_max)/2,bounds=(model.Dint_min,model.Dint_max), doc='diamètres extérieurs conduites consommateurs-consommateurs RETOUR')

## Débits
model.M_linePC = pe.Var(model.i,model.j,initialize=model.M_min,bounds=(model.M_min,model.M_max), doc='debit entre un noeud P(i) et C(j) (kg/s)')
model.M_lineCP = pe.Var(model.j,model.i,initialize=model.M_min,bounds=(model.M_min,model.M_max), doc='debit entre un noeud C(j) et P(i) (kg/s)')
model.M_prod = pe.Var(model.i,model.k,initialize=model.M_min,bounds=(model.M_min,model.M_max), doc='debit de la techno k(k) dans P(i) (kg/s)')
model.M_prod_tot = pe.Var(model.i,initialize=model.M_min,bounds=(model.M_min,model.M_max), doc='debit dans P(i) = somme des débits des technos k(k) (kg/s)')
model.M_hx = pe.Var(model.j,initialize=model.M_min,bounds=(model.M_min,model.M_max), doc='debit dans l\'échangeur de C(j) côté primaire (kg/s)')
model.M_supply = pe.Var(model.j,initialize=model.M_min,bounds=(model.M_min,model.M_max), doc='debit avant l\'échangeur de C(j); différent de M_hx seulement si cascade autorisée (kg/s)')
model.M_lineCC_parallel = pe.Var(model.j,model.o,initialize=model.M_min,bounds=(model.M_min,model.M_max), doc='debit entre un noeud C(j) et C(o) - ALLER (kg/s)')
model.M_lineCC_return = pe.Var(model.o,model.j,initialize=model.M_min,bounds=(model.M_min,model.M_max), doc='debit entre un noeud C(o) et C(j) - RETOUR (kg/s)')
model.M_return = pe.Var(model.j,initialize=model.M_min,bounds=(model.M_min,model.M_max), doc='debit après l\'échangeur au noeud C(j); différent de M_hx seulement si cascade (kg/s)')

## Températures
model.T_prod_in = pe.Var(model.i,model.k,initialize=model.T_init_min,bounds=(model.T_init_min,model.T_init_max), doc='température de sortie de la technologie k à la production i (°C)')
model.T_prod_tot_in = pe.Var(model.i,initialize=model.T_init_min,bounds=(model.T_init_min,model.T_init_max), doc='température de sortie de la production i = mélange des k technologies (°C)')
model.T_prod_out = pe.Var(model.i,model.k,initialize=model.T_init_min,bounds=(model.T_init_min,model.T_init_max), doc='température de retour de la technologie k à la production i = température de retour à la production i (°C)')
model.T_prod_tot_out = pe.Var(model.i,initialize=model.T_init_min,bounds=(model.T_init_min,model.T_init_max), doc='température de retour à la production i (°C)')
model.T_linePC_in = pe.Var(model.i, model.j,initialize=model.T_init_min,bounds=(model.T_init_min,model.T_init_max), doc='température de départ de la production i (°C)')
model.T_linePC_out = pe.Var(model.i, model.j,initialize=model.T_init_min,bounds=(model.T_init_min,model.T_init_max), doc='température d\'entrée dans le premier noeud = température de départ de la production i - pertes (°C)')
model.T_lineCP_in = pe.Var(model.j, model.i,initialize=model.T_init_min,bounds=(model.T_init_min,model.T_init_max), doc='température de départ du dernier noeud (°C)')
model.T_lineCP_out = pe.Var(model.j, model.i,initialize=model.T_init_min,bounds=(model.T_init_min,model.T_init_max), doc='température de retour à la production i = température de départ du dernier noeud - pertes (°C)')
model.T_hx_in = pe.Var(model.j,initialize=model.T_init_min,bounds=(model.T_init_min,model.T_init_max), doc='température d\'entrée dans l\'échangeur (°C)')
model.T_hx_out = pe.Var(model.j,initialize=model.T_init_min,bounds=(model.T_init_min,model.T_init_max), doc='température de sortie de l\'échangeur (°C)')
model.T_supply = pe.Var(model.j,initialize=model.T_init_min,bounds=(model.T_init_min,model.T_init_max), doc='température avant l\'échangeur de C(j) = T_hx_in (°C)')
model.T_lineCC_parallel_in = pe.Var(model.j, model.o,initialize=model.T_init_min,bounds=(model.T_init_min,model.T_init_max), doc='température de départ au noeud C(j) - ALLER (°C)')
model.T_lineCC_parallel_out = pe.Var(model.j, model.o,initialize=model.T_init_min,bounds=(model.T_init_min,model.T_init_max), doc='température d\'arrivée au noeud C(o) - ALLER (°C)')
model.T_lineCC_return_in = pe.Var(model.o, model.j,initialize=model.T_init_min,bounds=(model.T_init_min,model.T_init_max), doc='température de départ au noeud C(o) - RETOUR (°C)')
model.T_lineCC_return_out = pe.Var(model.o, model.j,initialize=model.T_init_min,bounds=(model.T_init_min,model.T_init_max), doc='température d\'arrivée au noeud C(j) - RETOUR (°C)')
model.T_return = pe.Var(model.j,initialize=model.T_init_min,bounds=(model.T_init_min,model.T_init_max), doc='température après l\'échangeur de C(j) = T_hx_out (°C)')

## Echangeur
model.DTLM = pe.Var(model.j,initialize=max(model.T_prod_out_max[k] for k in model.k), bounds=(0,max(model.T_prod_out_max[k] for k in model.k)), doc='Différence logarithmique de température à l’échangeur de chaleur (°C)')
model.DT1 = pe.Var(model.j,initialize=model.T_hx_pinch, bounds=(model.T_hx_pinch,model.T_init_max), doc='Différence de température côté chaud = T_hx_in - T_req_out (°C)')
model.DT2 = pe.Var(model.j,initialize=model.T_hx_pinch, bounds=(model.T_hx_pinch,model.T_init_max), doc='Différence de température côté froid = T_hx_out - T_req_in (°C)')

def A_hx_borne(model,j):
    return (model.H_req[j]/(model.K_hx*max(model.T_prod_out_max[k] for k in model.k)), 10*model.H_req[j]/(model.K_hx*max(model.T_prod_out_max[k] for k in model.k)))
def A_hx_init(model,j):
    return  model.H_req[j]/(model.K_hx*max(model.T_prod_out_max[k] for k in model.k))
model.A_hx = pe.Var(model.j,initialize=A_hx_init,bounds=A_hx_borne, doc='surface de l\'échangeur pour chaque consommateur j, bornée par le pincement T_hx_pinch ==> cf calcul de A_hx_borne')

## Pressions pour le coût_pompage
model.P_pump = pe.Var(model.i,initialize=0,bounds=(0,model.P_max), doc='Pressions de pompage (Pa)')

## Puissances installées
model.H_inst = pe.Var(model.i,model.k,initialize=0,bounds=(0,model.H_inst_max), doc='Puissance installée à la production i pour la technologie k (kW)')
# model.H_hx = pe.Var(model.j,bounds=(0,80,), doc='Puissance nominale de l\'échangeur du consommateur j')

def H_hx_borne(model,j):
    return (0,model.H_req[j])
model.H_hx = pe.Var(model.j,initialize=0,bounds=H_hx_borne, doc='Puissance nominale de l\'échangeur du consommateur j')

## Coûts
model.C_pump = pe.Var(initialize=0,bounds=(0,None), doc='Coûts de pompage (€)')
model.C_heat = pe.Var(initialize=0,bounds=(0,None), doc='Coût de la chaleur à produire (€)')
model.C_Hinst = pe.Var(initialize=0,bounds=(0,None), doc='Coût d\'installation de la puissance à la production (€)')
model.C_hx = pe.Var(initialize=0,bounds=(0,None), doc='Coût d\'installation des échangeurs en sous-station (€)')
model.C_line_tot = pe.Var(initialize=0,bounds=(0,None), doc='Coût total de la canalisation = tranchée + tuyau pré-isolé (€) ')
model.C_pipe = pe.Var(initialize=0,bounds=(0,None), doc='Coût des tuyau pré-isolés (€)')
model.C_tr = pe.Var(initialize=0,bounds=(0,None), doc='Coût de tranchée (€)')

## Longueur du réseau
model.L_tot = pe.Var(initialize=0,bounds=(0,None), doc='Longueur totale du réseau = longueur de tuyaux posés = 2 fois la longueur de tranchée car tuyau aller-retour')

#-----------------------------------------------------------------------------------------#
####################################### CONSTRAINT ########################################
#-----------------------------------------------------------------------------------------#

# Définition des diametres exterieurs = diametre interieur + epaisseur du tuyau et epaisseur isolant
def Def_Dout_PC_rule(model,i,j):
    """Diamètre des canalisations producteurs-consommateurs - ALLER"""
    return model.Dout_PC[i,j] == model.Dint_PC[i,j]+model.tk_pipe+model.tk_insul
model.Def_Dout_PC = pe.Constraint(model.i,model.j,rule=Def_Dout_PC_rule)

def Def_Dout_CP_rule(model,j,i):
    """Diamètre de la canalisation producteurs-consommateurs - RETOUR"""
    return model.Dout_CP[j,i] == model.Dint_CP[j,i]+model.tk_pipe+model.tk_insul
model.Def_Dout_CP = pe.Constraint(model.j,model.i,rule=Def_Dout_CP_rule)

def Def_Dout_CC_parallel_rule(model,j,o):
    """Diamètre des canalisations entre consommateurs - ALLER"""
    return model.Dout_CC_parallel[j,o] == model.Dint_CC_parallel[j,o]+model.tk_pipe+model.tk_insul
model.Def_Dout_CC_parallel = pe.Constraint(model.j,model.o,rule=Def_Dout_CC_parallel_rule)

def Def_Dout_CC_return_rule(model,o,j):
    """Diamètre des canalisations entre consommateurs - RETOUR"""
    return model.Dout_CC_return[o,j] == model.Dint_CC_return[o,j]+model.tk_pipe+model.tk_insul
model.Def_Dout_CC_return = pe.Constraint(model.o,model.j,rule=Def_Dout_CC_return_rule)


# Existance des contraintes selon la valeur des variables binaires avec la méthode du bigM
## Débits
def Def_V_linePC_rule_bigM(model,i,j):
    """Inéquation du bigM sur le débit entre producteur et consommateur - ALLER"""
    valeur = model.V_linePC[i,j]*(model.rho*pi*model.Dint_PC[i,j]*model.Dint_PC[i,j]/4) - model.M_linePC[i,j]
    return - model.M_bigM*(1-model.Y_linePC[i,j]) <= valeur  <= model.M_bigM*(1-model.Y_linePC[i,j])
model.Def_V_linePC_bigM = pe.Constraint(model.i,model.j,rule=Def_V_linePC_rule_bigM)

def Def_V_lineCP_rule_bigM(model,j,i):
    """Inéquation du bigM sur le débit entre consommateur et producteur - RETOUR"""
    valeur = model.V_lineCP[j,i]*(model.rho*pi*model.Dint_CP[j,i]*model.Dint_CP[j,i]/4) - model.M_lineCP[j,i]
    return - model.M_bigM*(1-model.Y_lineCP[j,i]) <= valeur <= model.M_bigM*(1-model.Y_lineCP[j,i])
model.Def_V_lineCP_bigM = pe.Constraint(model.j,model.i,rule=Def_V_lineCP_rule_bigM)

def Def_V_lineCC_parallel_rule_bigM(model,j,o):
    """Inéquation du bigM sur le débit entre consommateurs - ALLER"""
    valeur = model.V_lineCC_parallel[j,o]*(model.rho*pi*model.Dint_CC_parallel[j,o]*model.Dint_CC_parallel[j,o]/4) - model.M_lineCC_parallel[j,o]
    return - model.M_bigM*(1-model.Y_lineCC_parallel[j,o]) <= valeur <= model.M_bigM*(1-model.Y_lineCC_parallel[j,o])
model.Def_V_lineCC_parallel_bigM = pe.Constraint(model.j,model.o,rule=Def_V_lineCC_parallel_rule_bigM)

def Def_V_lineCC_return_rule_bigM(model,o,j):
    """Inéquation du bigM sur le débit entre consommateurs - RETOUR"""
    valeur = model.V_lineCC_return[o,j]*(model.rho*pi*model.Dint_CC_return[o,j]*model.Dint_CC_return[o,j]/4) - model.M_lineCC_return[o,j]
    return - model.M_bigM*(1-model.Y_lineCC_return[o,j]) <= valeur <= model.M_bigM*(1-model.Y_lineCC_return[o,j])
model.Def_V_lineCC_return_bigM = pe.Constraint(model.o,model.j,rule=Def_V_lineCC_return_rule_bigM)

## Vitesses maximals et minimals
def Ex_V_linePC_max_rule(model,i,j):
    """Permet de definir une vitesse min/max que si la canalisation existe"""
    return model.V_linePC[i,j] <= model.V_max*model.Y_linePC[i,j]
model.Ex_V_linePC_max = pe.Constraint(model.i,model.j,rule=Ex_V_linePC_max_rule)

def Ex_V_linePC_min_rule(model,i,j):
    """Permet de definir une vitesse min/max que si la canalisation existe"""
    return model.V_linePC[i,j] >= model.V_min*model.Y_linePC[i,j]
model.Ex_V_linePC_min = pe.Constraint(model.i,model.j,rule=Ex_V_linePC_min_rule)

def Ex_V_lineCP_max_rule(model,j,i):
    """Permet de definir une vitesse min/max que si la canalisation existe"""
    return model.V_lineCP[j,i] <= model.V_max*model.Y_lineCP[j,i]
model.Ex_V_lineCP_max = pe.Constraint(model.j,model.i,rule=Ex_V_lineCP_max_rule)

def Ex_V_lineCP_min_rule(model,j,i):
    """Permet de definir une vitesse min/max que si la canalisation existe"""
    return model.V_lineCP[j,i] >= model.V_min*model.Y_lineCP[j,i]
model.Ex_V_lineCP_min = pe.Constraint(model.j,model.i,rule=Ex_V_lineCP_min_rule)

def Ex_V_lineCC_parallel_max_rule(model,j,o):
    """Permet de definir une vitesse min/max que si la canalisation existe"""
    return model.V_lineCC_parallel[j,o] <= model.V_max*model.Y_lineCC_parallel[j,o]
model.Ex_V_lineCC_parallel_max = pe.Constraint(model.j,model.o,rule=Ex_V_lineCC_parallel_max_rule)

def Ex_V_lineCC_parallel_min_rule(model,j,o):
    """Permet de definir une vitesse min/max que si la canalisation existe"""
    return model.V_lineCC_parallel[j,o] >= model.V_min*model.Y_lineCC_parallel[j,o]
model.Ex_V_lineCC_parallel_min = pe.Constraint(model.j,model.o,rule=Ex_V_lineCC_parallel_min_rule)

def Ex_V_lineCC_return_max_rule(model,o,j):
    """Permet de definir une vitesse min/max que si la canalisation existe"""
    return model.V_lineCC_return[o,j] <= model.V_max*model.Y_lineCC_return[o,j]
model.Ex_V_lineCC_return_max = pe.Constraint(model.o,model.j,rule=Ex_V_lineCC_return_max_rule)

def Ex_V_lineCC_return_min_rule(model,o,j):
    """Permet de definir une vitesse min/max que si la canalisation existe"""
    return model.V_lineCC_return[o,j] >= model.V_min*model.Y_lineCC_return[o,j]
model.Ex_V_lineCC_return_min = pe.Constraint(model.o,model.j,rule=Ex_V_lineCC_return_min_rule)

# Definition de débits maximals et minimals si la canalisation existe, si la canalisations n'existe pas le débit est nul
def Ex_M_prod_max_rule(model,i,k):
    """Débit maximal pour chaque technologies k"""
    return model.M_prod[i,k] <= model.M_max*model.Y_P[i,k]
model.Ex_M_prod_max = pe.Constraint(model.i,model.k,rule=Ex_M_prod_max_rule)

def Ex_M_prod_min_rule(model,i,k):
    """Débit minimal pour chaque technologies k"""
    return model.M_prod[i,k] >= model.M_min*model.Y_P[i,k]
model.Ex_M_prod_min = pe.Constraint(model.i,model.k,rule=Ex_M_prod_min_rule)

def Ex_M_linePC_max_rule(model,i,j):
    """Débit maximal dans les canalisations entre producteurs et consommateurs - ALLER"""
    return model.M_linePC[i,j] <= model.M_max*model.Y_linePC[i,j]
model.Ex_M_linePC_max = pe.Constraint(model.i,model.j,rule=Ex_M_linePC_max_rule)

def Ex_M_lineCP_max_rule(model,j,i):
    """Débit maximal dans les canalisations entre producteurs et consommateurs - RETOUR"""
    return model.M_lineCP[j,i] <= model.M_max*model.Y_lineCP[j,i]
model.Ex_M_lineCP_max = pe.Constraint(model.j,model.i,rule=Ex_M_lineCP_max_rule)

def Ex_M_lineCC_parallel_max_rule(model,j,o):
    """Débit maximal dans les canalisations entre consommateurs - ALLER"""
    return model.M_lineCC_parallel[j,o] <= model.M_max*model.Y_lineCC_parallel[j,o]
model.Ex_M_lineCC_parallel_max = pe.Constraint(model.j,model.o,rule=Ex_M_lineCC_parallel_max_rule)

def Ex_M_lineCC_return_max_rule(model,o,j):
    """Débit maximal dans les canalisations entre consommateurs - RETOUR"""
    return model.M_lineCC_return[o,j] <= model.M_max*model.Y_lineCC_return[o,j]
model.Ex_M_lineCC_return_max = pe.Constraint(model.o,model.j,rule=Ex_M_lineCC_return_max_rule)


# BILAN DE MASSE
def bilanA_debit_supply_rule(model,j):
    """Bilan de masse au point A d'un noeud consommateur
    Un consommateur (M_supply) peut être alimenté par un producteur (M_linePC) ou un autre consommateur (M_lineCC_parallel)"""
    return sum(model.M_linePC[i,j] for i in model.i) + sum(model.M_lineCC_parallel[o,j] for o in model.o if o != j) == model.M_supply[j]
model.bilanA_debit_supply = pe.Constraint(model.j,rule=bilanA_debit_supply_rule)

def bilanB_debit_hx_in_rule(model,j):
    """Bilan de masse au point B d'un noeud consommateur
    Seule une partie du débit (M_supply) alimente le consommateur (M_hx), le reste part vers une autre consommateur (M_lineCC_parallel),
    sauf s'il est en fin de réseau et dans ce cas M_supply = M_hx"""
    return model.M_supply[j] == model.M_hx[j] + sum(model.M_lineCC_parallel[j,o] for o in model.o if o != j)
model.bilanB_debit_hx_in = pe.Constraint(model.j,rule=bilanB_debit_hx_in_rule)

def bilanD_debit_hx_out_rule(model,j):
    """Bilan de masse au point D d'un noeud consommateur
    Le débit (M_return) à chaque consommateur est composé du débit en sortie de l'échangeur (M_hx) et du débit de retour des autres
    consommateurs (M_lineCC_return), sauf s'il est en fin de réseau et dans ce cas M_return = M_hx"""
    return model.M_hx[j] + sum(model.M_lineCC_return[o,j] for o in model.o if o != j) == model.M_return[j]
model.bilanD_debit_hx_out = pe.Constraint(model.j,rule=bilanD_debit_hx_out_rule)

def bilanE_debit_return_rule(model,j):
    """Bilan de masse au point E d'un noeud consommateur
    Après le point D, le débit (M_return) peut soit retourner vers la production (M_lineCP) soit vers un autre consommateur (M_lineCC_return)"""
    return model.M_return[j] == sum(model.M_lineCP[j,i] for i in model.i) + sum(model.M_lineCC_return[j,o] for o in model.o if o != j)
model.bilanE_debit_return = pe.Constraint(model.j,rule=bilanE_debit_return_rule)

def bilanF_debit_prod_tot_in_rule(model,i):
    """Bilan de masse au point F d'un noeud producteur
    La débit de retour à la production (M_prod_tot) est égal au débit de retour du ou des derniers consommateurs par branche (M_lineCP)"""
    return sum(model.M_lineCP[j,i] for j in model.j) == model.M_prod_tot[i]
model.bilanF_debit_prod_tot_in = pe.Constraint(model.i,rule=bilanF_debit_prod_tot_in_rule)

def bilanI_debit_prod_tot_out_rule(model,i):
    """Bilan de masse au point I d'un noeud producteur
    La débit de départ à la production (M_prod_tot) est égal aux débits partants vers les premiers consommateurs par branche (M_linePC)"""
    return model.M_prod_tot[i] == sum(model.M_linePC[i,j] for j in model.j)
model.bilanI_debit_prod_tot_out = pe.Constraint(model.i,rule=bilanI_debit_prod_tot_out_rule)

def bilanGH_debit_prod_out_rule(model,i):
    """Bilan de masse aux points G et H d'un noeud producteur
    Le débit total partant/rentrant de la production i est égal à la somme des débit de chaque unité de production k associés"""
    return model.M_prod_tot[i] == sum(model.M_prod[i,k] for k in model.k)
model.bilanGH_debit_prod_out = pe.Constraint(model.i,rule=bilanGH_debit_prod_out_rule)


# BILAN D'ENERGIE ET EGALITE DE TEMPERATURE
def bilanA_H_supply_rule(model,j):
    """Bilan d'énergie au point A d'un noeud consommateur car point convergeant"""
    return model.M_supply[j]*model.T_supply[j] == (
    sum(model.M_linePC[i,j]*model.T_linePC_out[i,j] for i in model.i)
    + sum(model.M_lineCC_parallel[o,j]*model.T_lineCC_parallel_out[o,j] for o in model.o if o != j)
    )
model.bilanA_H_supply = pe.Constraint(model.j,rule=bilanA_H_supply_rule)

def bilanB_T_hx_in_rule_bigM(model,j,o):
    """Première égalité de température au point B d'un noeud consommateur car point divergeant
    Tsupply = TlineCC_parallel
    Inéquation du bigM"""
    valeur = model.T_supply[j] - model.T_lineCC_parallel_in[j,o]
    return - model.T_bigM*(1-model.Y_lineCC_parallel[j,o]) <= valeur <= model.T_bigM*(1-model.Y_lineCC_parallel[j,o])
model.bilanB_T_hx_in_bigM = pe.Constraint(model.j,model.o,rule=bilanB_T_hx_in_rule_bigM)

def bilanB2_T_hx_in_rule(model,j):
    """Deuxième égalité de température au point B d'un noeud consommateur car point divergeant
    Tsupply = Thx
    Pas de bigM car si le consommateur existe l'échangeur est forcément alimenté alors que la liaison avec
    un autre consommateur (TlineCC_parallel) n'existe pas forcément"""
    return model.T_hx_in[j] == model.T_supply[j]
model.bilanB2_T_hx_in = pe.Constraint(model.j,rule=bilanB2_T_hx_in_rule)

def bilanD_H_hx_out_rule(model,j):
    """Bilan d'énergie au point D d'un noeud consommateur car point convergeant"""
    return model.M_hx[j]*model.T_hx_out[j]+sum(model.M_lineCC_return[o,j]*model.T_lineCC_return_out[o,j] for o in model.o if o != j) == model.M_return[j]*model.T_return[j]
model.bilanD_H_hx_out = pe.Constraint(model.j,rule=bilanD_H_hx_out_rule)

def bilanE_T_return_rule_bigM(model,i,j):
    """Première égalité de température au point E d'un noeud consommateur car point divergeant
    Treturn = TlineCP
    Inéquation du bigM"""
    valeur = model.T_return[j] - model.T_lineCP_in[j,i]
    return - model.T_bigM*(1-model.Y_lineCP[j,i]) <= valeur <= model.T_bigM*(1-model.Y_lineCP[j,i])
model.bilanE_T_return_bigM = pe.Constraint(model.i,model.j,rule=bilanE_T_return_rule_bigM)

def bilanE2_T_return_rule_bigM(model,o,j):
    """Deuxième égalité de température au point E d'un noeud consommateur car point divergeant
    Treturn = T_lineCC_return
    Inéquation du bigM"""
    valeur = model.T_return[o] - model.T_lineCC_return_in[o,j]
    return - model.T_bigM*(1-model.Y_lineCC_return[o,j]) <= valeur <= model.T_bigM*(1-model.Y_lineCC_return[o,j])
model.bilanE2_T_return_bigM = pe.Constraint(model.o,model.j,rule=bilanE2_T_return_rule_bigM)

def bilanF_H_prod_tot_in_rule(model,i):
    """Bilan d'énergie au point F d'un noeud producteur car point convergeant"""
    return sum(model.M_lineCP[j,i]*model.T_lineCP_out[j,i] for j in model.j) == model.M_prod_tot[i]*model.T_prod_tot_in[i]
model.bilanF_H_prod_tot_in = pe.Constraint(model.i,rule=bilanF_H_prod_tot_in_rule)

def bilanG_T_prod_in_rule_bigM(model,i,k):
    """Egalité de température au point G d'un noeud producteur car point convergeant
    Tprod_tot = Tprod : la température de retour est la même pour toutes les technologies
    Inéquation du bigM"""
    valeur = model.T_prod_tot_in[i] - model.T_prod_in[i,k]
    return - model.T_bigM*(1-model.Y_P[i,k]) <= valeur <= model.T_bigM*(1-model.Y_P[i,k])
model.bilanG_T_prod_in_bigM = pe.Constraint(model.i,model.k,rule=bilanG_T_prod_in_rule_bigM)

def bilanH_H_prod_out_rule(model,i):
    """Bilan d'énergie au point H d'un noeud producteur car point convergeant
    Mélange des fluides provenant des technologies k à la production i"""
    return sum(model.M_prod[i,k]*model.T_prod_out[i,k] for k in model.k) == model.M_prod_tot[i]*model.T_prod_tot_out[i]
model.bilanH_H_prod_out = pe.Constraint(model.i,rule=bilanH_H_prod_out_rule)

def bilanI_T_prod_tot_out_rule_bigM(model,i,j):
    """Egalité de température au point I d'un noeud producteur car point divergeant
    La production peut alimenter ou non les consommateurs
    Inéquation du bigM"""
    valeur = model.T_linePC_in[i,j] - model.T_prod_tot_out[i]
    return - model.T_bigM*(1-model.Y_linePC[i,j]) <= valeur <= model.T_bigM*(1-model.Y_linePC[i,j])
model.bilanI_T_prod_tot_out_bigM = pe.Constraint(model.i,model.j,rule=bilanI_T_prod_tot_out_rule_bigM)

def bilan_H_inst_rule_bigM1(model,i,k):
    """Bilan de chaleur à la production si elle existent
    Puissance à installer * efficacité = Puissance requise
    Inéquation 1 du bigM"""
    return model.H_inst[i,k]*model.Eff[k] <= model.M_prod[i,k] * model.Cp * (model.T_prod_out[i,k] - model.T_prod_in[i,k]) + model.H_inst_bigM*(1-model.Y_P[i,k])
model.bilan_H_inst_bigM1 = pe.Constraint(model.i,model.k,rule=bilan_H_inst_rule_bigM1)

def bilan_H_inst_rule_bigM2(model,i,k):
    """..... Inéquation 2 du bigM"""
    return model.H_inst[i,k]*model.Eff[k] >= model.M_prod[i,k] * model.Cp * (model.T_prod_out[i,k] - model.T_prod_in[i,k]) - model.H_inst_bigM*(1-model.Y_P[i,k])
model.bilan_H_inst_bigM2 = pe.Constraint(model.i,model.k,rule=bilan_H_inst_rule_bigM2)

def bilan_chaleur_HX_rule(model,j):
    """Bilan de chaleur pour chaque consommateur, pas de bigM, un consommateur est forcément alimenté
    Puissance requise = débit * Cp * delta T
    Inéquation 1 du bigM"""
    return model.H_hx[j] == model.M_hx[j] * model.Cp * (model.T_hx_in[j]-model.T_hx_out[j])
model.bilan_chaleur_HX = pe.Constraint(model.j,rule=bilan_chaleur_HX_rule)

def bilan_DT1_rule(model,j):
    """Delta T côté chaud de l'échangeur (DT1) = entrée au primaire - sortie au secondaire"""
    return model.DT1[j] == model.T_hx_in[j] - model.T_req_out[j]
model.bilan_DT1 = pe.Constraint(model.j,rule=bilan_DT1_rule)
def bilan_DT2_rule(model,j):
    """Delta T côté froid de l'échangeur (DT2) = sortie au primaire - entrée au secondaire"""
    return model.DT2[j] == model.T_hx_out[j] - model.T_req_in[j]
model.bilan_DT2 = pe.Constraint(model.j,rule=bilan_DT2_rule)

def bilan_DT1_pinch_rule(model,j):
    """DT1 doit être supérieur au pincement minimun par définition"""
    return model.DT1[j] >= model.T_hx_pinch
model.bilan_DT1_pinch = pe.Constraint(model.j,rule=bilan_DT1_pinch_rule)

def bilan_DT2_pinch_rule(model,j):
    """DT2 doit être supérieur au pincement minimum par définition"""
    return model.DT2[j] >= model.T_hx_pinch
model.bilan_DT2_pinch = pe.Constraint(model.j,rule=bilan_DT2_pinch_rule)

def diffTemplog_rule(model,j):
    """Calcul de la DTLM: Différence logarithmique de température à l’échangeur de chaleur (°C)"""
    return model.DTLM[j] == (model.DT1[j] * model.DT2[j] * 0.5 * (model.DT1[j] + model.DT2[j])) ** (1/3)
model.diffTemplog = pe.Constraint(model.j, rule=diffTemplog_rule)

def bilan_chaleur_HX_DTLM_rule(model,j):
    """Bilan de puissance à l'échangeur avec le DTLM qui dépend des températures au primaire et secondaire
    H = coeff_échange * surface * DTLM"""
    return model.H_hx[j] == model.A_hx[j] * model.K_hx * model.DTLM[j]
model.bilan_chaleur_HX_DTLM = pe.Constraint(model.j,rule=bilan_chaleur_HX_DTLM_rule)

# Pertes thermiques (ici négligées car T_in = T_out)
def loss_linePC_rule(model,i,j):
    """Pertes thermiques sur les conduites entre producteur et consommateur - ALLER"""
    return model.T_linePC_out[i,j] == model.T_linePC_in[i,j]
model.loss_linePC = pe.Constraint(model.i, model.j,rule=loss_linePC_rule)

def loss_lineCP_rule(model,j,i):
    """Pertes thermiques sur les conduites entre producteur et consommateur - RETOUR"""
    return model.T_lineCP_out[j,i] == model.T_lineCP_in[j,i]
model.loss_lineCP = pe.Constraint(model.j, model.i,rule=loss_lineCP_rule)

def loss_lineCC_parallel_rule(model,j,o):
    """Pertes thermiques sur les conduites entre consommateur - ALLER"""
    return model.T_lineCC_parallel_out[j,o] == model.T_lineCC_parallel_in[j,o]
model.loss_lineCC_parallel = pe.Constraint(model.j, model.o,rule=loss_lineCC_parallel_rule)

def loss_lineCC_return_rule(model,o,j):
    """Pertes thermiques sur les conduites entre consommateurs - RETOUR"""
    return model.T_lineCC_return_out[o,j] == model.T_lineCC_return_in[o,j]
model.loss_lineCC_return = pe.Constraint(model.o, model.j,rule=loss_lineCC_return_rule)

# Contrainte à l'échangeur
def contrainte_appro_rule(model,j):
    """La puissance calculée à l'échangeur doit être égale à celle requise rentrée par l'utilisateur"""
    return model.H_hx[j] == model.H_req[j]
model.contrainte_appro = pe.Constraint(model.j, rule=contrainte_appro_rule)


# Termes de la fonction coût
def cout_pompage_rule(model):
    """Coût de pompage"""
    return model.C_pump == 1.e-6*model.f_opex_pump*model.C_pump_unit*model.period*sum(model.P_pump[i]*model.M_prod_tot[i] for i in model.i)*model.Eff_pump/model.rho
model.cout_pompage = pe.Constraint(rule=cout_pompage_rule)

def cout_heat_rule(model):
    """Coût de la chaleur livrée"""
    return model.C_heat == 1.e-6 * model.period * sum(model.f_opex[k] * model.C_heat_unit[k] * model.H_inst[i,k] for i in model.i for k in model.k)
model.cout_heat = pe.Constraint(rule=cout_heat_rule)

def cout_puissance_rule(model):
    """Coût de la puissance installée en chaufferie"""
    return model.C_Hinst == 1.e-6 * model.f_capex * sum(model.C_Hprod_unit[k] * model.H_inst[i,k] for i in model.i for k in model.k)
model.cout_puissance = pe.Constraint(rule=cout_puissance_rule)

def cout_echangeur_rule(model):
    """Coût des échangeurs"""
    return model.C_hx == 1.e-6*model.f_capex*sum(model.C_hx_unit_a*model.H_hx[j]+model.C_hx_unit_b for j in model.j)
model.cout_echangeur = pe.Constraint(rule=cout_echangeur_rule)

def cout_canalisation_tuyau_rule(model):
    """Coût des tuyaux pré-isolés"""
    return model.C_pipe == 1.e-6* model.f_capex*(
    sum(model.L_PC[i,j]*(model.C_pipe_unit_a*model.Dint_PC[i,j]+model.C_pipe_unit_b) for i in model.i for j in model.j)
    + sum(model.L_CP[j,i]*(model.C_pipe_unit_a*model.Dint_CP[j,i]+model.C_pipe_unit_b) for j in model.j for i in model.i)
    + sum(model.L_CC_parallel[j,o]*(model.C_pipe_unit_a*model.Dint_CC_parallel[j,o]+model.C_pipe_unit_b) for j in model.j for o in model.o)
    + sum(model.L_CC_return[j,o]*(model.C_pipe_unit_a*model.Dint_CC_return[j,o]+model.C_pipe_unit_b) for j in model.j for o in model.o)
    )
model.cout_canalisation_tuyau = pe.Constraint(rule=cout_canalisation_tuyau_rule)

def cout_canalisation_tranchee_rule(model):
    """Coût de tranchée"""
    return model.C_tr == 1.e-6* model.f_capex*(
    sum(model.C_tr_unit/2 * model.L_PC[i,j] for i in model.i for j in model.j)
    + sum(model.C_tr_unit/2 * model.L_CP[j,i] for j in model.j for i in model.i)
    + sum(model.C_tr_unit/2 * model.L_CC_parallel[j,o] for j in model.j for o in model.o)
    + sum(model.C_tr_unit/2 * model.L_CC_return[j,o] for j in model.j for o in model.o)
    )
model.cout_canalisation_tranchee = pe.Constraint(rule=cout_canalisation_tranchee_rule)

def cout_canalisation_tot_rule(model):
    """Coût total de canalisation: tuyaux + tranchée"""
    return model.C_line_tot == model.C_pipe + model.C_tr
model.cout_canalisation_tot = pe.Constraint(rule=cout_canalisation_tot_rule)

# Longueur totale du réseau
def Ex_L_tot_rule(model):
    """Correspond à la somme de tous les tuyaux posés = 2 fois la longueur de tranchée car tuyau aller-retour"""
    return model.L_tot == sum(model.L_PC[i,j] for i in model.i for j in model.j) +(
                        sum(model.L_CP[j,i] for j in model.j for i in model.i)
                        + sum(model.L_CC_parallel[j,o]  for j in model.j for o in model.o)
                        + sum(model.L_CC_return[j,o]  for j in model.j for o in model.o)
                        )
model.Ex_L_tot = pe.Constraint(rule=Ex_L_tot_rule)

#-----------------------------------------------------------------------------------------#
####################################### OBJECTIVE #########################################
#-----------------------------------------------------------------------------------------#

# Definition de la fonction objectif à minimiser
def objective_rule(model):
    """Sommes des termes coût"""
    return model.C_pump + model.C_heat + model.C_Hinst + model.C_hx + model.C_line_tot
model.objective = pe.Objective(rule=objective_rule, sense=pe.minimize)

#-----------------------------------------------------------------------------------------#
####################################### SOLVING ###########################################
#-----------------------------------------------------------------------------------------#

# Résolution du problème
if __name__ == '__main__': # ne pas lancer si appel depuis l'extérieur

    # Crée et affiche l'instance du modèle (récapitulatif des indices, paramètres, variables, objectifs, contraintes)
    print('-'*60 + "\nPROBLEME/MODELE\n" + '-'*60)

    instance = model.create_instance() # crée
    instance.pprint() # affiche

    print('-'*60 + "\nRESOLUTION\n" + '-'*60)

    from pyomo.opt import SolverFactory

    # choix du solveur
    opt = SolverFactory('ipopt')

    # options [cf https://www.coin-or.org/Ipopt/documentation/node42.html]
    opt.options['tol'] = 1e-3           # defaut: 1e-8
    opt.options['max_iter']           # defaut: 3000
    opt.options['max_cpu_time']           # defaut: 1e+6
    opt.options['dual_inf_tol']           # defaut = 1
    opt.options['constr_viol_tol']           # defaut = 0.0001
    opt.options['compl_inf_tol']           # defaut = 0.0001
    opt.options['acceptable_tol']           # defaut = 1e-6
    opt.options['acceptable_iter']           # defaut = 15
    opt.options['acceptable_constr_viol_tol']           # defaut = 0.01
    opt.options['acceptable_dual_inf_tol']           # defaut = 1e+10
    opt.options['acceptable_compl_inf_tol']           # defaut = 0.01
    opt.options['acceptable_obj_change_tol']           # defaut = 1e+20
    opt.options['diverging_iterates_tol']           # defaut = 1e+20

    # optimisation
    results = opt.solve(model,tee=True, keepfiles=False) # [tee] affichage itération [keepfiles] création des fichier .nl/.sol/.log


#-----------------------------------------------------------------------------------------#
###################################### SOLUTION ########################################
#-----------------------------------------------------------------------------------------#

    ## Ecriture et affichage de la solution
    print('\n' + '-'*60 + "\nSOLUTION\n" + '-'*60)
    def pyomo_postprocess(options=None, instance=None, results=None):
        instance.solutions.load_from(results)
        # ecriture
        with open('./Solution.txt', 'w') as f:
            f.write('{} {}\n'.format("///Objective///\n", round(pe.value(instance.objective), 2)))
            f.write('///Variables///\n')
            for v in instance.component_objects(pe.Var, active=True):
                varobject = getattr(instance, str(v))
                for index in varobject:
                    f.write('{} {} {}\n'.format(v, [index], round(varobject[index].value, 3)))

    pyomo_postprocess(None, model, results)

    print('Ecriture du fichier solution.txt: ok')

        # affichage
    print('Affichage de la solution:')

    pe.display(model)
