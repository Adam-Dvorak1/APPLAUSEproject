import pandas as pd
from helpers import annual_cost


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


def change_loads_costs(network, gas_mult, megen_mult):
    '''Like change_gasload, this changes the gas load, but it also changes the 
    price of the methanogenesis by a multiplier. he megen_cost is the annualized
    cost of the methanogenesis. We are sweeping over both of these, with a logarithmic
    range'''
    gasdf = pd.read_csv('data/AppleGas.csv', index_col = 0)
    gasdf.index = pd.to_datetime(gasdf.index)

    network.remove("Load", "Gas Load")
    network.add("Load", 
        "Gas Load", 
        bus="gas", 
        p_set=gasdf["All_in_one_demand"]/3 * gas_mult) #This is so it multiplies by 1

    network.links.loc['methanogens', 'capital_cost'] = annual_cost("methanation") * megen_mult


    return network


def solve_network(network, gas_mult, megen_mult):

    n = change_loads_costs(network, gas_mult, megen_mult)

        
    n.lopf(n.snapshots, 
             pyomo=False,
             solver_name='gurobi')

            




    return n

def to_netcdf(network, gas_mult, megen_mult, path):
    n = solve_network(network, gas_mult, megen_mult)

   # With all the talk of multipliers, in reality gas_mult is the average gas demand in kW, 
   #the megen_mult becomes modified
    gas_mult = round(gas_mult)

    megen_mult = megen_mult * annual_cost("methanation") #This should be a variable passed. I think it takes a significant time x 100 to do this. Maybe  maybe not

    megen_mult = round(megen_mult) 

    path = path + f"/gas_dem_{gas_mult}_megen_cost_{megen_mult}.nc"
    
    n.export_to_netcdf(path)

