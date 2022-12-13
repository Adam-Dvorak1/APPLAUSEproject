
#The purpose of this file is to make a simple model of methanation. There will be two models:
#one with normal sabatier and one with methanogens (bacteria that produce methane)

#author @Adam Dvorak
#Github: Adam-Dvorak1

#With assistance from Lisa Zeyen

import pypsa
from datetime import datetime
import numpy as np
import os
import pathlib
import itertools
import time
from multiprocessing import Pool
from buildnetwork import add_buses, add_generators, add_loads, add_stores, add_links, add_methanogen, add_sabatier, add_hydrogen_store
from helpers import override_component_attrs, annual_cost
from modifynetwork import change_gasload, to_netcdf, remove_grid, remove_solar

#  Lisa: We are going to need multi-links for modelling the CO2 management.
#  Since default setting for links in PyPSA is having only one entry (bus0)
#  and one exit point (bus1) with a given efficieny (efficiency) we have to
#  overwrite some component settings with the following function
def get_relpath(path, home):
        rel_path = os.path.relpath(path, home)
        return rel_path

def new_folder(name):
    '''This makes a directory for where netcdf files will be saved. It takes
    the desired name as input'''

    dir = pathlib.Path().resolve() #This is the current path
    mypath = str(dir) + "/results/NetCDF" #Going into the NetCDF folder
    curDT = datetime.now()
    version = curDT.strftime("%d_%m_%Y")
    mypath = mypath + "/" + version + "_" + name
    

    if os.path.exists(mypath):
        mypath = mypath + "1"

    os.mkdir(mypath)

    return mypath
    

if __name__ == "__main__":
        __spec__ = "ModuleSpec(name='builtins', loader=<class '_frozen_importlib.BuiltinImporter'>)"
        startime = time.time()

        ##---<<Variables>>-----
        methanogens = True #whether methanogen or sabatier
        name = "gasdem_megencost_sweep_w_hstore" #name of the run, added to date
        solar = True
        grid = True
        h_store = True

        # costrange = np.logspace(0, 4, 10)        
        gas_dems = [x for x in np.logspace(0, 4, 10)] #number of kWh 
        methanogen_costs = [x for x in np.logspace(-1, 1, 10)]#multiplier to sabatier price
        # methane_cost = annual_cost('methanation')
        # methanogen_costs = [methane_cost * x for x in methanogen_costs]

        overrides = override_component_attrs("override_component_attrs")

        n = pypsa.Network(override_component_attrs=overrides)


        n = add_buses(n)
        n = add_generators(n)
        n = add_loads(n)
        n = add_stores(n)
        n = add_links(n)

        if methanogens == True:
                n = add_methanogen(n)
                methanation = "methanogen"
        else:
                n = add_sabatier(n)
                methanation = "sabatier"

        if h_store == True:
                n = add_hydrogen_store(n)


        if solar != True:
                n = remove_solar(n)
        

        if grid != True:
                n = remove_grid(n)


        ns = list([n])


 
        allpath = new_folder(name)
        homepath = pathlib.Path().resolve()
        rel_path = get_relpath(allpath, homepath)


        endpath = list([rel_path])

        f = list(itertools.product(ns, gas_dems, methanogen_costs, endpath))


        with Pool(processes=4) as pool:
                pool.starmap(to_netcdf, f)

        endtime = time.time()
        print(endtime-startime)