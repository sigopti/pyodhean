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


model = Model(
    technologies=technologies,
    production=production,
)

print('### Solve ###\n')
model.solve(options)
print('')

print('### Display ###\n')
model.display()

model.write_solution('./solution.txt')