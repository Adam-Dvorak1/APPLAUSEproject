import pypsa
import numpy as np
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib as mpl

import importlib
import multiplotterfunc
importlib.reload(multiplotterfunc)

from multiplotterfunc import generators_dcurve, battery_dcurve, storage_dcurve, methane_link_dcurve

#

if __name__ == "__main__":
    path = "results/NetCDF/03_11_2022_log_cost_sweep/methanogen1.0.nc"
    path1 = "results/NetCDF/03_11_2022_log_cost_sweep/methanogen10000.0.nc"
    
    generators_dcurve(path1, "log") #log makes the most sense
    # battery_dcurve(path1, "log")
    # # storage_dcurve(path1, "log")
    # methane_link_dcurve(path1)