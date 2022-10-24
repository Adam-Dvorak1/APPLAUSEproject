
# %%
import pypsa
import numpy as np
import pandas as pd
from pypsa.descriptors import Dict
from datetime import datetime
from pypsa.components import components, component_attrs
import matplotlib.pyplot as plt
import os

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

#%% 
def make_plot(path):
    '''As of 24 October, this '''
    n = pypsa.Network()
    n.import_from_netcdf(path)
    o = path.split("/")
    oo = [item.split("_") for item in o]
    oo = [item for sublist in oo for item in sublist]

    if "methanogen" in oo:
        methanogen = True
    else:
        methanogen = False
    print (methanogen)

    #battery plot
    fig, ax = plt.subplots()
    ax.plot(n.links_t.p0[['battery charger', 'battery discharger']], label = ["charger", "discharger"])
    ax.set_ylabel("")
    ax.legend()
    curDT = datetime.now()
    version = curDT.strftime("_%d_%m_%Y")
    if methanogen == True:
        ax.set_title("Methanogen--Battery Charge and Discharge")
        plt.savefig("results/Images/methanogen_battery_links" + version + ".pdf")
    else:
        ax.set_title("Sabatier--Battery Charge and Discharge")
        plt.savefig("results/Images/sabatier_battery_links" + version + ".pdf")
    plt.show()

# %%    
if __name__ == "__main__":
    make_plot("results/NetCDF/methanogen_20_10_2022.nc")
    
# %%
if __name__ == "__main__":
    make_plot("results/NetCDF/sabatier_20_10_2022.nc")


#%%
