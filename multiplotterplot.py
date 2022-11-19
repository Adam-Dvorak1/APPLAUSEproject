import pypsa
import numpy as np
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib as mpl

import importlib
import multiplotterfunc
importlib.reload(multiplotterfunc)

from multiplotterfunc import  plot_costpergas, plot_gridtoelec_dcurv, plot_methlink_dcurv, plot_gasstore_dcurv

#generators_dcurve, battery_dcurve, storage_dcurve, methane_link_dcurve, plot_linksize, plot_objective,

if __name__ == "__main__":
    
    #plot_linksize()
    #plot_objective()
    # plot_costpergas()

    #plot_gridtoelec_dcurv()
    #plot_methlink_dcurv()
    plot_gasstore_dcurv()

    # path = "results/NetCDF/03_11_2022_log_cost_sweep/methanogen1.0.nc"
    # path1 = "results/NetCDF/03_11_2022_log_cost_sweep/methanogen10000.0.nc"
    
    # generators_dcurve(path1, "log") #log makes the most sense
    # # battery_dcurve(path1, "log")
    # # storage_dcurve(path1, "log")
    # methane_link_dcurve(path1)