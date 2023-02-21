'''The purpose of this script is to house generally helpful helper functions'''
import os
from pypsa.components import components, component_attrs
from pypsa.descriptors import Dict
import pandas as pd
import glob
import pathlib
from datetime import datetime
import pypsa


#  Lisa: We are going to need multi-links for modelling the CO2 management.
#  Since default setting for links in PyPSA is having only one entry (bus0)
#  and one exit point (bus1) with a given efficieny (efficiency) we have to
#  overwrite some component settings with the following function

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
    #The conversion rate between euro and usd is 1.07 on February 16 2023

    eur_usd = 1.07
    discount_rate = 0.07
    data = pd.read_csv("data/costs_2025_NRELsolwind.csv")
    tech_data = data.loc[data['technology'] == tech]
    cap_cost =tech_data.query("parameter == 'investment'")['value'].values[0] #in eur/kW
    lifetime = tech_data.query("parameter == 'lifetime'")['value'].values[0]
    fomset= tech_data.query("parameter == 'FOM'")
    if fomset.empty:
        fom = 0
    else:
        fom = fomset['value'].values[0]
    annu_val = annuity(lifetime,discount_rate)*cap_cost*(1+fom) * eur_usd #in usd/kW
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

        
        tempdf['load'] = n.loads_t.p["Gas Load"].max()/len(n.snapshots) #This is an independent variable
        tempdf['megen cost'] = n.links.loc['methanogens', 'capital_cost'] #This is an independent varaible. Hm, but this is not the same as the 
        tempdf['megen size'] = n.links.loc['methanogens', 'p_nom_opt'] 
        tempdf['electrolyzer size'] = n.links.loc["H2 Electrolysis", "p_nom_opt"]
        if "Solar PV" in n.generators.index:
            tempdf['solar size'] = n.generators.p_nom_opt["Solar PV"]
            tempdf['battery size'] = n.stores.e_nom_opt['battery']
        if "H2 store" in n.stores.index:
            tempdf["H2 store size"] = n.stores.e_nom_opt['H2 store']
            tempdf['H2 store ts'] = n.stores_t.e.loc[:, "H2 store"]


        tempdf['objective'] = n.objective 

        tempdf['electrolyzer ts'] = n.links_t.p0.loc[:, "H2 Electrolysis"]
        tempdf['grid to electricity link ts'] = n.links_t.p0.loc[:, "High to low voltage"]
        tempdf['methanogen link ts'] = n.links_t.p0.loc[:, "methanogens"]
        tempdf['gas store ts'] = n.stores_t.e.loc[:, "gas store"]
        tempdf["battery store ts"] = n.stores_t.e.loc[:, "battery"]#Note--we have experiments where we remove the solar, but not the battery. In this case, the battery just has 0s
        tempdf['biogas generator ts'] = n.generators_t.p.loc[:, 'Biogas'] #We actually don't care about the solar generator because we know it is completely maxed




        df = pd.concat([df, tempdf])

    name = folder.split("/")
    name = name [-1]

    
    df.to_csv('results/csvs/alldata/' + name + ".csv")

def extract_summary(csvpath):
    '''This only deals with the time independent variables of each run'''
    df = pd.read_csv(csvpath)
    df2 = df[[column for column in df.columns if "ts" not in column]]
    df2 = df2[[column for column in df2.columns if "snapshot" not in column]]
    df3 = df2.drop_duplicates(["load", "megen cost"])#This yields every unique combination of load and megen cost
    
    name = csvpath.split("/")
    name = name[-1]

    df3.to_csv('results/csvs/sumdata/summary_' + name )#no csv needed at the end because the name is from the other csv


#n.links_t.p0['High to low voltage']

def get_gridcost(n):
    '''Note: this assumes a constant grid load'''
    gridgen = n.generators_t.p["Grid"] - n.loads_t.p["Grid Load"].mean() #subtracting the average load of the grid. This is the EXACT SAME as n.links_t.p0["High to low voltage"]
    
    gridgen = gridgen.to_frame() #this is a series so turn into frame

    marginal_cost = n.generators_t.marginal_cost #timeseries of marginal costs

    costgrid = gridgen * marginal_cost #timeseries of real costs
    total_costs = costgrid.query('`Grid` > 0').sum().values[0]# total cost. Positive ecause we are looking at p
    total_income = costgrid.query('`Grid` < 0').sum().values[0]

    return total_costs, total_income


def get_costs(n, grid):

    '''This takes a network and tries to find all of the relevant costs
    If grid = True, then the total electricity '''



        
    links = n.links.loc[:, "p_nom_opt"] * n.links.loc[:, "capital_cost"]
    generators = n.generators.loc[:, "p_nom_opt"] * n.generators.loc[:, "capital_cost"]
    stores = n.stores.loc[:, "e_nom_opt"] * n.stores.loc[:, "capital_cost"]
   

    year = n.snapshots[0].year
    year = pd.Series(year)
    year.index = ['year']
    
    gasload = n.loads_t.p["Gas Load"].max()/8760 #Note, we divide by 8760 because the max value is the total value, so we thus want the average val
    gasload = pd.Series( gasload)
    gasload.index = ["Gas Load"]

    megen_cap_cost =  n.links.loc["methanogens", "capital_cost"]
    megen_cap_cost = pd.Series(megen_cap_cost)
    megen_cap_cost.index = ["methanogen capital cost"]

    electrolyzer_cap_cost = n.links.loc['H2 Electrolysis', 'capital_cost']
    electrolyzer_cap_cost = pd.Series(electrolyzer_cap_cost)
    electrolyzer_cap_cost.index = ['electrolyzer capital cost']

    

    cost_series = pd.concat([year, gasload, megen_cap_cost, electrolyzer_cap_cost, links, generators, stores])

    if grid == True:
        grid_cost, grid_income = get_gridcost(n)
        grid_cost = pd.Series(grid_cost)
        grid_cost.index = ['grid elec total cost']


        grid_income= pd.Series(grid_income)
        grid_income.index = ['grid elec total income']

        cost_series = pd.concat([cost_series, grid_cost, grid_income])
        

    cost_df = pd.DataFrame([cost_series])
    
    return cost_df




def costs_to_csv(path, isgrid):
    searchpath = path + "/*"
    df = pd.DataFrame()

    for file in glob.glob(searchpath):
        n = pypsa.Network()
        n.import_from_netcdf(file)
        cost_df = get_costs(n, isgrid) #True because we are looking for the marginal price of the grid sum, so we add a bit


        df = pd.concat([df, cost_df])


    name = path.split("/")
    name = name[-1]
    
    df.to_csv('results/csvs/costs/' + name + ".csv")


def make_pres_folders(prestitle):

    '''The purpose of this function is to make nice organized folders. It first checks whether the 
    subfolders gridsolar, nogrid, and nosolar have been made. If not, it makes them. Then, it checks
    whether the sub sub folders w_hstore and wo_hstore have been made. If not, it makes them. Etc. '''

    path = "Presentations/" + prestitle 
    pathlib.Path(path).mkdir(parents = True, exist_ok = True)

    pathlib.Path(path+ "/gridsolar").mkdir(parents=True, exist_ok=True)
    pathlib.Path(path + "/justsolar").mkdir(parents=True, exist_ok=True)
    pathlib.Path(path + "/justgrid").mkdir(parents=True, exist_ok=True)


    newpath = "Presentations/" + prestitle + "/*" #an example folder will be "Presentations/January31pres/nosolar"
    for folder in glob.glob(newpath):
        if os.path.isdir(folder):
            pathlib.Path(folder + "/costsper").mkdir(parents=True, exist_ok=True)
            pathlib.Path(folder + "/sizes").mkdir(parents=True, exist_ok=True)
            
    deeperpath = "Presentations/" + prestitle + "/*/costsper"

    for folder in glob.glob(deeperpath):
        pathlib.Path(deeperpath + "/electrolysis").mkdir(parents=True, exist_ok=True)





            

#%%


#%%



if __name__ == "__main__":

    '''It may be a bit confusing, but I can currently make up to 3 different csvs in helpers.py
    
    One of them is a general csv which has everything. This is the extract_data() function and delivers the entire timeseries
    of data for each network. It takes in the network folder as input. This gets stored under results/csvs/alldata.
    This is useful if you want to plot duration curves.
    
    Another one is a summary csv which only records non-time dependent attributes. This is the extract_summary() function.
    It reads the csv generated from extract_data() and delivers a csv stored under results/csvs/sumdata with "summary_" attached to 
    the front of it. This is useful if you want to plot stuff like the objective, or optimal
    sizes
     
    Finally, we get a costs csv which allows us to assess how expensive the network is per kW supplied. This is made through 
    a series of functions: costs_to_csv(path, isgrid), which takes the folder of the netcdfs as well as whether or not there
    is a grid. Next, it calls get_costs(n, isgrid) which reads in each network of the folder and passes the isgrid variable. 
    Finally, if isgrid is True, then get_costs() calls get_gridcost, which returns the relevant costs of the grid. This 
    generates a csv that is stored in results/csvs/costs. This is useful if you want to plot
    info involving LCOE or income. '''

    # path = "results/NetCDF/25_01_2023_gasdem_megencost_sweep_wo_hstore"
    # extract_data(path)
    # path = "results/NetCDF/25_01_2023_gasdem_megencost_sweep_w_hstore"
    # extract_data(path)
    # path = "results/NetCDF/25_01_2023_gasdem_megencost_sweep_nosolar_w_hstore"
    # extract_data(path)
    # path = "results/NetCDF/25_01_2023_gasdem_megencost_sweep_nosolar_wo_hstore"
    # extract_data(path)
    # path = "results/NetCDF/25_01_2023_gasdem_megencost_sweep_nogrid_w_hstore"
    # extract_data(path)
    # path = "results/NetCDF/08_02_2023_gasdem_year_sweep_gridsolar_w_hstore"
    # costs_to_csv(path, True)

    # extract_data(path)

    presdate = "February10pres"
    # make_pres_folders(presdate)


    # extract_summary(csvpath) 




