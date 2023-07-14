import pypsa
import numpy as np
import pandas as pd
from datetime import datetime
'''The purpose of this function is to import the functions from multiplotterfunc.py and then execute the function (ie, plot them)'''
import matplotlib.pyplot as plt
import matplotlib as mpl

import importlib
import multiplotterfunc
import helpers
importlib.reload(multiplotterfunc)
importlib.reload(helpers)


from multiplotterfunc import  compare_dcurves_secondary, plot_gridprice_dc_wspain, plot_bp_gas, find_all_netincome, plot_gridprice_dc, plot_all_gridprice, find_net_income_year_el_solar, cf_compare, four_cost_plot_pres, capacity, cf_sensitivity, find_net_income_pass_Spain, four_cost_plot_Spain,  find_net_income_pass, plot_elec_ts, compare_cost_bars, plot_cost_any, plot_anysize_all, plot_anysize, compare_dcurves,  plot_gridtoelec_dcurv, plot_methlink_dcurv, plot_gasstore_dcurv

#generators_dcurve, battery_dcurve, storage_dcurve, methane_link_dcurve, plot_linksize, plot_objective,

if __name__ == "__main__":

    gridsolar = 'results/csvs/costs/10_07_2023_demvar_gridsolar.csv'
    # cf_sensitivity()
    plot_bp_gas()
    # find_net_income_pass('results/csvs/costs/10_07_2023_demvar_gridsolar.csv')
    # compare_dcurves_secondary()
    # plot_bp_gas()
    # plot_gridprice_dc()
    # plot_gridprice_dc_wspain()
    # compare_dcurves()
# asdf