import os
from pypsa.components import components, component_attrs
from pypsa.descriptors import Dict
import pandas as pd
import glob
import pathlib
from datetime import datetime
import pypsa

def override_component_attrs(directory):
    """Lisa: Tell PyPSA that links can have multiple outputs by
    overriding the component_attrs. This can be done for
    as many buses as you need with format busi for i = 2,3,4,5,....
    See https://pypsa.org/doc/components.html#link-with-multiple-outputs-or-inputs
    Parameters
    ----------
    directory : string
        Folder where component attributes to override are stored
        analogous to ``pypsa/component_attrs``, e.g. `links.csv`.
    Returns
    -------
    Dictionary of overriden component attributes.


    Adam: I can see that the buses now can have up to 4 output ports. I presume now
    we can use them
    """

    attrs = Dict({k : v.copy() for k,v in component_attrs.items()})

    for component, list_name in components.list_name.items():
        fn = f"{directory}/{list_name}.csv"
        if os.path.isfile(fn):
            overrides = pd.read_csv(fn, index_col=0, na_values="n/a")
            attrs[component] = overrides.combine_first(attrs[component])

    return attrs


def annuity(n,r):
    """Calculate the annuity factor for an asset with lifetime n years and
    discount rate of r, e.g. annuity(20,0.05)*20 = 1.6"""

    if r > 0:
        return r/(1. - 1./(1.+r)**n)
    else:
        return 1/n


def annual_cost(tech):
    '''Taking a string as input for the type of technology, this function
    calculates the annualized cost of a technology'''
    discount_rate = 0.07
    data = pd.read_csv("data/costs_2025.csv")
    tech_data = data.loc[data['technology'] == tech]
    cap_cost =tech_data.query("parameter == 'investment'")['value'].values[0] #in eur/kW
    lifetime = tech_data.query("parameter == 'lifetime'")['value'].values[0]
    fomset= tech_data.query("parameter == 'FOM'")
    if fomset.empty:
        fom = 0
    else:
        fom = fomset['value'].values[0]
    annu_val = annuity(lifetime,discount_rate)*cap_cost*(1+fom) #in eur/kW
    return annu_val



def extract_data(folder):
    '''This is a function that makes a pd Data Frame, and adds a row with relevant data for each
    Time series are ts. Single variables are repeated. This makes it easy to stack
    The resulting df will be 8760 hours * number of files long'''
    path = folder + "/*"


    df = pd.DataFrame()

    megen_cost = annual_cost("methanation")

    for file in glob.glob(path):
        n = pypsa.Network()
        n.import_from_netcdf(file)
        tempdf = pd.DataFrame(index = n.snapshots)


        tempdf['load'] = n.loads_t.p["Gas Load"].max()/8760 #This is an independent variable
        tempdf['megen cost'] = n.links.loc['methanogens', 'capital_cost'] #This is an independent varaible. Hm, but this is not the same as the 
        tempdf['megen size'] = n.links.loc['methanogens', 'p_nom_opt'] 
        tempdf['objective'] = n.objective 
        tempdf['grid to electricity link ts'] = n.links_t.p0.loc[:, "High to low voltage"]
        tempdf['methanogen link ts'] = n.links_t.p0.loc[:, "methanogens"]
        tempdf['gas store ts'] = n.stores_t.e.loc[:, "gas store"]
        tempdf['biogas generator ts'] = n.generators_t.p.loc[:, 'Biogas'] #We actually don't care about the solar generator because we know it is completely maxed




        df = pd.concat([df, tempdf])

    name = folder.split("/")
    name = name[-1]
    
    df.to_csv('results/csvs/' + name + ".csv")

def extract_summary(csvpath):
    '''This only deals with the time independent variables of each run'''
    df = pd.read_csv(csvpath)
    df2 = df[[column for column in df.columns if "ts" not in column]]
    df2 = df2[[column for column in df2.columns if "snapshot" not in column]]
    df3 = df2.drop_duplicates(["load", "megen cost"])#This yields every unique combination of load and megen cost
    
    name = csvpath.split("/")
    name = name[-1]

    df3.to_csv('results/csvs/summary_' + name )#no csv needed at the end because the name is from the other csv




def get_gridcost(n):
    '''Note: this assumes a constant grid load'''
    gridgen = n.generators_t.p["Grid"] - n.loads_t.p["Grid Load"].mean() #subtracting the average load of the grid
    
    gridgen = gridgen.to_frame() #this is a series so turn into frame

    marginal_cost = n.generators_t.marginal_cost #timeseries of marginal costs

    costgrid = gridgen * marginal_cost #timeseries of real costs
    total_cost = costgrid.sum().values[0] # total cost

    return (total_cost)


def get_costs(n, grid):

    '''This takes a network and tries to find all of the relevant costs
    If grid = True, then the total electricity '''



        
    links = n.links.loc[:, "p_nom_opt"] * n.links.loc[:, "capital_cost"]
    generators = n.generators.loc[:, "p_nom_opt"] * n.generators.loc[:, "capital_cost"]
    stores = n.stores.loc[:, "e_nom_opt"] * n.stores.loc[:, "capital_cost"]
   
    gasload = n.loads_t.p["Gas Load"].max()/8760
    gasload = pd.Series( gasload)
    gasload.index = ["Gas Load"]

    link_cap_cost =  n.links.loc["methanogens", "capital_cost"]
    link_cap_cost = pd.Series(link_cap_cost)
    link_cap_cost.index = ["methanogen capital cost"]

    

    cost_series = pd.concat([gasload, link_cap_cost, links, generators, stores])

    if grid == True:
        grid_cost = get_gridcost(n)
        grid_cost = pd.Series(grid_cost)
        grid_cost.index = ['grid elec total cost']
        cost_series = pd.concat([cost_series, grid_cost])
        

    cost_df = pd.DataFrame([cost_series])
    
    return cost_df




def costs_to_csv(path):
    searchpath = path + "/*"
    df = pd.DataFrame()

    for file in glob.glob(searchpath):
        n = pypsa.Network()
        n.import_from_netcdf(file)
        cost_df = get_costs(n, True) #True because we are looking for the marginal price of the grid sum, so we add a bit


        df = pd.concat([df, cost_df])


    name = path.split("/")
    name = name[-1]
    
    df.to_csv('results/csvs/costs/' + name + ".csv")





if __name__ == "__main__":
    # path = "results/NetCDF/21_11_2022_gasdem_megencost_sweep_nogrid"
    # results/NetCDF/21_11_2022_gasdem_megencost_sweep_nosolar
    path = "results/NetCDF/21_11_2022_gasdem_megencost_sweep_nosolar"
    costs_to_csv(path)



    # extract_data(path)

    # csvpath = "results/csvs/15_11_2022_gasdem_megencost_sweep.csv"

    # extract_summary(csvpath) 