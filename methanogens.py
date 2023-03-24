
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
import modifynetwork
importlib.reload(buildnetwork)
importlib.reload(modifynetwork)
from buildnetwork import add_buses, add_generators, add_loads, add_stores, add_links, add_methanogen, add_sabatier
from helpers import override_component_attrs, annual_cost
from modifynetwork import change_gasload, to_netcdf, remove_grid, remove_solar, add_wind


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
        name = "year_2020_test" #name of the run, added to date. Use gridsolar, nosolar, or nogrid at the end
        #only solar or wind can be chosen at one time
        solar = True #whether using solar generator or not
        wind = False
        grid = True#whether using grid generator or not
        

        
        ##---<<Secondary sweeping variables>>-----
        # Modify the sweeping range in the sweeping dict in modifynetwork.py
        # Only do one of these at a time
        electrolyzer = False
        year = True #Note, if you are doing a year run, both solar and grid must be True
        gridinverter = False


        ##---<<EUR-USD conversion rate>>-------
        # eur_usd = 1.07, change in helpers.py, in the function annual_cost()
        

        #The sweeps is a list that contain the name of the sweeping variable. The sweeper is a list that 
        # contains the range being swept over
        
        
        '''In addition to a megen cost sweep, the sweep can be electrolyzer, year, or gas_load'''
        if electrolyzer == True:
               sweeps = "electrolyzer"
               sweeper = [1/4, 1/2, 2/3, 5/6, 1, 1.2, 1.5, 2, 4] #It is important that we always use an odd number of sweeping numbers for the function compare_cost_bars() in multiplotterfunc.py so it can easily find the median (ie default) value
        elif year == True:
               sweeps = "year"
               sweeper = ['2020']
               #sweeper = ['2017', '2018', '2019', '2020']
        elif gridinverter == True:
               sweeps = 'grid_inverter'
               sweeper = [0.1, 0.5, 0.75, 1, 1.25, 1.5, 2] #These will be multiplied by the average electricity demand required per hour, which is 14667 kW
               #As in, the grid inverter size will be limited by x times the mean

       

        # We are doing huge sweeps to see the extremes--under what conditions is it worth it to produce methane from our methanogenesis? 
        # It may be that it is basically never worth it. In fact, our first results show that it is actually better to just use
        # The solar generator to produce electricity rather than produce methane

        #megen_costs_list = [20, 50, 80, 100, 120, 150, 200, 300, 500] #Now, 9 costs
        megen_costs_list = [20]
        methanogen_costs = [x/annual_cost('methanation') for x in megen_costs_list]#multiplier to sabatier price, varying from 1/10 sabatier price to 10 x sabatier price



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



        #We are interested in the behavior of the system if we use wind instead. These will be cases without any solar, however

        
        # In contrast, I also gave myself the option of removing the grid and forcing the system to rely on the solar generator.
        # Obviously, it makes no sense to remove both generators.
        if grid != True:
                n = remove_grid(n)


        if wind == True:
                n = add_wind(n)




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