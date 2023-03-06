import pypsa
import numpy as np
import pandas as pd
from datetime import datetime
'''The purpose of this function is to import the functions from multiplotterfunc.py and then execute the function (ie, plot them)'''
import matplotlib.pyplot as plt
import matplotlib as mpl

import importlib
import multiplotterfunc
importlib.reload(multiplotterfunc)

from multiplotterfunc import  plot_cost_any, four_cost_plot, find_net_income_multiyear, find_net_income, plot_anysize_all, plot_anysize, compare_dcurves,  plot_costper, plot_costs, plot_costpergas, plot_gridtoelec_dcurv, plot_methlink_dcurv, plot_gasstore_dcurv

#generators_dcurve, battery_dcurve, storage_dcurve, methane_link_dcurve, plot_linksize, plot_objective,

if __name__ == "__main__":

    #path = 'results/csvs/costs/06_12_2022_gasdem_megencost_sweep.csv'



    costpath = 'results/csvs/costs/08_02_2023_gasdem_year_sweep_gridsolar_w_hstore.csv'

    # plot_battsize()

    allpath = "results/csvs/alldata/25_01_2023_gasdem_megencost_sweep_nogrid_wo_hstore.csv"
    

    find_net_income( 'results/csvs/costs/archive/25_01_2023_gasdem_megencost_sweep_w_hstore.csv')
    #plot_cost_any('results/csvs/costs/21_02_2023_year_megen_sweep_justwind.csv')

