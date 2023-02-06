import pandas as pd
from helpers import annual_cost
import numpy as np


def change_gasload(network, multiplier):
    '''There are two loads, one for gas demand, and one ginormous grid demand.
    The grid demand is assumed to be constant and huge. The gas load is assumed to be
    taken at the end of the year. The default for the "all_in_one_demand" for the 
    applegas csv is 3kWh per hour, taken at the last hour of the year. It works because
    there is a free storage that can take all of the gas until the end of the year--this way
    we answer the question "we want this amount of gas per year, what is the optimal config"'''
    gasdf = pd.read_csv('data/AppleGas.csv', index_col = 0)
    gasdf.index = pd.to_datetime(gasdf.index)

    network.remove("Load", "Gas Load")

    network.add("Load", #Why are there two loads here? Which is the name?
        "Gas Load", 
        bus="gas", 
        p_set=gasdf["All_in_one_demand"]/3 * multiplier) #Now

    return network


def change_loads_costs(network, sweep, sweep_mult, megen_mult):
    '''This function used to change the gasload, in addition to the methanogen cost. 
    Now, it still changes the methanogen cost, but it also '''



    network.links.loc['methanogens', 'capital_cost'] = annual_cost("methanation") * megen_mult


    return network


'''These two functions are for an experiment on 21 November, to see what happens to the grid
and the solar if the other is removed. That being said, the solar will need to be expanded'''

def remove_solar(network):


    network.remove("Generator", "Solar PV")


    return network

def remove_grid(network):

    network.remove("Load", "Grid Load")
    network.remove("Generator", "Grid")

    #We also need to change the p_nom_max, as now solar needs to supply everything for the methane
    network.generators.loc["Solar PV", "p_nom_max"] = np.inf

    return network



def solve_network(network, sweep, sweep_mult, megen_mult):

    n = change_loads_costs(network, sweep, sweep_mult, megen_mult)

        
    n.lopf(n.snapshots, 
             pyomo=False,
             solver_name='gurobi')


    return n

def to_netcdf(network, sweep, sweep_mult, megen_mult, path):
    n = solve_network(network, sweep, sweep_mult, megen_mult)

   # With all the talk of multipliers, in reality gas_mult is the average gas demand in kW, 
   #the megen_mult becomes modified
    

    megen_mult = megen_mult * annual_cost("methanation") #This is the same calculated in change_loads_costs(). Redundant maybe, but I think it is pretty quick.

    megen_mult = round(megen_mult) #The real cost is not rounded--this is just for documentation and plotting

    if sweep == "electrolyser":
        sweep_mult = sweep_mult * annual_cost('electrolysis')
        sweep_mult = round (sweep_mult)

    path = path + "/" + sweep + f"_{sweep_mult}_megen_cost_{megen_mult}.nc"
    
    n.export_to_netcdf(path)

