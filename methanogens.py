
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
import importlib
import time
from multiprocessing import Pool
import buildnetwork
importlib.reload(buildnetwork)
from buildnetwork import add_buses, add_generators, add_loads, add_stores, add_links, add_methanogen, add_sabatier
from helpers import override_component_attrs, annual_cost
from modifynetwork import change_gasload, to_netcdf, remove_grid, remove_solar


sweep_dict = {'electrolyzer': [x for x in np.logspace (-1, 1, 10)], "year": ['2017', '2018', '2019', '2020', '2021']}


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

        ##---<<Experimental Variables>>-----
        methanogens = True #whether methanogen or sabatier
        name = "gasdem_year_sweep_gridsolar_w_hstore" #name of the run, added to date
        solar = True #whether using solar generator or not
        grid = True #whether using grid generator or not
        
        ##---<<Secondary sweeping variables>>-----
        # Modify the sweeping range in the sweeping dict in modifynetwork.py
        electrolyzer = False
        year = True

        #The sweeps is a list that contain the name of the sweeping variable. The sweeper is a list that 
        # contains the range being swept over
        
        
        '''In addition to a megen cost sweep, the sweep can be electrolyzer, year, or gas_load'''
        if electrolyzer == True:
               sweeps = "electrolyzer"
               sweeper = [x for x in np.logspace (-1, 1, 10)]
        elif year == True:
               sweeps = "year"
               sweeper = ['2017', '2018', '2019', '2020']

       

        # We are doing huge sweeps to see the extremes--under what conditions is it worth it to produce methane from our methanogenesis? 
        # It may be that it is basically never worth it. In fact, our first results show that it is actually better to just use
        # The solar generator to produce electricity rather than produce methane

        methanogen_costs = [x for x in np.logspace(-1, 1, 10)]#multiplier to sabatier price, varying from 1/10 sabatier price to 10 x sabatier price



        ##---<<Network creation>>-----
        overrides = override_component_attrs("override_component_attrs")

        n = pypsa.Network(override_component_attrs=overrides)

        #Here, we are building the network, one type of component at a time. 
        n = add_buses(n)
        n = add_generators(n)
        n = add_loads(n)
        n = add_stores(n)
        n = add_links(n)



        ##---<<Network experiment choices>>------
        if methanogens == True:
                n = add_methanogen(n)
                methanation = "methanogen"
        else:
                n = add_sabatier(n)
                methanation = "sabatier"
               

        #I have previously given myself the option of removing the solar generator and forcing the methanogen to only use
        # electricity from the generator
        if solar != True:
                n = remove_solar(n)
        
        # In contrast, I also gave myself the option of removing the grid and forcing the system to rely on the solar generator.
        # Obviously, it makes no sense to remove both generators.
        if grid != True:
                n = remove_grid(n)


        ##---<<Running the experiment>>-------
        
        ns = [n]
        sweeps = [sweeps]

        allpath = new_folder(name)
        homepath = pathlib.Path().resolve()
        rel_path = get_relpath(allpath, homepath)

        endpath = list([rel_path])

        f = list(itertools.product(ns, sweeps, sweeper, methanogen_costs, endpath))


        with Pool(processes=4) as pool:
                pool.starmap(to_netcdf, f) #This also solves the network



        endtime = time.time()
        print(endtime-startime)