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

from multiplotterfunc import  compare_cost_bars, plot_grid_restriction, plot_cost_any, four_cost_plot, find_net_income_multiyear, find_net_income, plot_anysize_all, plot_anysize, compare_dcurves,  plot_costper, plot_gridtoelec_dcurv, plot_methlink_dcurv, plot_gasstore_dcurv

#generators_dcurve, battery_dcurve, storage_dcurve, methane_link_dcurve, plot_linksize, plot_objective,

if __name__ == "__main__":

    #path = 'results/csvs/costs/06_12_2022_gasdem_megencost_sweep.csv'


    #fig, ax = plt.subplots()
    #gridsolar = 'results/csvs/costs/05_04_2023_electrolyzer_megen_gridsolar_dispatch_zero_double_sweep.csv'

    four_cost_plot()
    #compare_cost_bars()

    # plot_battsize()

