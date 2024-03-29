
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
import helpers
importlib.reload(buildnetwork)
importlib.reload(modifynetwork)
importlib.reload(helpers)

from buildnetwork import add_buses, add_generators, add_loads, add_stores, add_links, add_methanogen, add_sabatier
from helpers import mindf_csv, extract_capacity_factor, extract_summary, extract_data, override_component_attrs, annual_cost, costs_to_csv
from modifynetwork import add_generators_sol_spain, add_wind_cost, add_sol_cost, zeroload, change_gasload, to_netcdf, remove_grid, remove_solar, add_wind


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
        methanogens = True #whether methanogen or sabatier. Don't change it.
        name = "DR0.9_gridsolar_mindf" #name of the run, added to date. Use gridsolar, nosolar, or nogrid at the end
        #only solar or wind can be chosen at one time
        
        solar = True#whether using solar generator or not
        wind = False
        grid = True#whether using grid generator or not
        

        mindf = True#When the mindf is true, then use a True Electrolyzer, and then change methanation and electrolyzer lists of these vars to [1]
        

        
        ##---<<Secondary sweeping variables>>-----
        # Modify the sweeping range in the sweeping dict in modifynetwork.py
        # Only do one of these at a time. You must do one.
        # 5 April: Cost of grid connection added
        # 15 June: Cost of battery added
        electrolyzer = True
        battery = False
        h2store = False
        gridsolaryear = False
        gridinverter = False #This has to do with restricting the size of the grid inverter
        GIcost = False#GI stands for grid inverter
        Spain = False#Then we use a different time series
        
        # solarcost = True # solarcost is not a real experiment because it is dispatch. If we really want to see the impact on the costs, then we just need to go into the costs csvs

        

        ##---<<EUR-USD conversion rate>>-------
        # eur_usd = 1.07, change in helpers.py, in the function annual_cost()
        

        #The sweeps is a list that contain the name of the sweeping variable. The sweeper is a list that 
        # contains the range being swept over
        
        
        '''In addition to a megen cost sweep, the sweep can be electrolyzer, year, or gas_load'''
        if electrolyzer == True:
               sweeps = "electrolyzer"
               sweeper = [1]
        #        if mindf == False:
        #               if solar == True or wind == True:
        #                      if grid == True:
        #                             sweeper = [0. , 0.2, 0.4, 0.6, 0.8, 1. , 1.2, 1.4, 1.6, 1.8, 2]
               #It is important that we always use an odd number of sweeping numbers for the function compare_cost_bars() in multiplotterfunc.py so it can easily find the median (ie default) value
        elif battery == True:
               sweeps = 'battery'
               sweeper = [0. , 0.2, 0.4, 0.6, 0.8, 1. , 1.2, 1.4, 1.6, 1.8, 2]
        elif h2store == True:
               sweeps = 'H2 store'
               sweeper = [0. , 0.2, 0.4, 0.6, 0.8, 1. , 1.2, 1.4, 1.6, 1.8, 2]
        elif gridsolaryear == True:
               sweeps = 'grid-sol-year'
               yearlist = ['2017', '2018', '2019', '2020']
               sweeper = [x for x in itertools.product(yearlist, yearlist)]
        elif gridinverter == True:
               sweeps = 'grid_inverter'
               sweeper = [2, 3, 4, 10] #These will be multiplied by the average electricity demand required per hour, which is 14667 kW
               #As in, the grid inverter size will be limited by x times the mean
        elif GIcost == True:
                sweeps = "gi_cost"
                sweeper = [0. , 0.2, 0.4, 0.6, 0.8, 1. , 1.2, 1.4, 1.6, 1.8, 2]
        elif Spain == True:
               sweeps = 'spain_electrolyzer'
               sweeper = [1]
               if mindf == False:
                      if solar == True and grid == True:
                             sweeper = [0. , 0.2, 0.4, 0.6, 0.8, 1. , 1.2, 1.4, 1.6, 1.8, 2]
         

                
       

        # We are doing huge sweeps to see the extremes--under what conditions is it worth it to produce methane from our methanogenesis? 
        # It may be that it is basically never worth it. In fact, our first results show that it is actually better to just use
        # The solar generator to produce electricity rather than produce methane
        if mindf: #Spain, wind, solar mindfs
                methanogen_costs = [1]
        elif electrolyzer == False: #We don't care about sweeps in methanogen cost if we are varying other variables
                methanogen_costs = [1]
        else:
                methanogen_costs = [0. , 0.2, 0.4, 0.6, 0.8, 1, 1.2, 1.4, 1.6, 1.8, 2]#multiplier to sabatier price, varying from 1/10 sabatier price to 10 x sabatier price
                methanogen_costs = [1]


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
        if wind == True:
                n = add_wind(n)
        
        # In contrast, I also gave myself the option of removing the grid and forcing the system to rely on the solar generator.
        # Obviously, it makes no sense to remove both generators.
        if grid != True:
                n = remove_grid(n)
                if solar == True: # If this is a just sol scenario, then we do not want dispatch
                       n = add_sol_cost(n)
                if wind == True:
                       n = add_wind_cost(n)
                # if Spain == True:
                #        n = add_spain_cost(n)
                

        if Spain == True: 
               n = add_generators_sol_spain(n)

         


        if mindf == True:
                n = zeroload(n)




        ##---<<Running the experiment>>-------
        
        ns = [n]
        sweeps = [sweeps]

        allpath = new_folder(name)
        homepath = pathlib.Path().resolve()
        rel_path = get_relpath(allpath, homepath)

        endpath = list([rel_path])

        f = list(itertools.product(ns, sweeps, sweeper, methanogen_costs, endpath))
        # print(f)

        with Pool(processes=4) as pool:
                pool.starmap(to_netcdf, f) #This also solves the network


        #11 April 2023: Adding this from helpers.py to speed up, get csv right away
        
               
        csvpath = costs_to_csv(rel_path, grid, sweeps[0]) #rel_path is the netcdf folder, grid presence is True or False, The sweeps[0] corresponds to the 'twovar', or the secondary sweeping variable. If it is gi_cost, then it changes the way that the helper csv is used
        
        if mindf == True: #26 May we have modified the costs_to_csv function to return the path, so we can then read the csv and use the same path
               mindf_csv(csvpath)

        if solar == True and grid == True and mindf == False and electrolyzer == True:
               
                allcsvpath = extract_data(rel_path) #This extracts time series data and other important data
                # extract_summary(allcsvpath) #This extracts the non-time series data from the previous csv. We use this to make heatmaps of capacity
                extract_capacity_factor(allcsvpath, twovar = sweeps[0])

        endtime = time.time()
        print(endtime-startime)