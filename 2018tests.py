import pypsa
from datetime import datetime
import numpy as np
import os
import pathlib
import itertools
import importlib
import time
from multiprocessing import Pool
import buildnetwork
import modifynetwork
importlib.reload(buildnetwork)
importlib.reload(modifynetwork)
from buildnetwork import add_buses, add_generators, add_loads, add_stores, add_links, add_methanogen, add_sabatier
from helpers import override_component_attrs, annual_cost
from modifynetwork import change_gasload, to_netcdf, remove_grid, remove_solar, add_wind

overrides = override_component_attrs("override_component_attrs")

n = pypsa.Network(override_component_attrs=overrides)

#Here, we are building the network, one type of component at a time. 
n = add_buses(n)
n = add_generators(n)
n = add_loads(n)
n = add_stores(n)
n = add_links(n)

n = add_methanogen(n)



to_netcdf(n, 'year', '2018', 1, 'results/NetCDF/23_03_2023_year_2018_test')
