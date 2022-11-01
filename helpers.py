
# %%
import pypsa
import numpy as np
import pandas as pd
from pypsa.descriptors import Dict
from datetime import datetime
from pypsa.components import components, component_attrs
import matplotlib.pyplot as plt
import matplotlib as mpl
import os

#%%
#For my links, I always set the following relationship. methanogens does not have electricity
methanation_link_dict = {"p0": "Hydrogen in", "p1": "Gas out", "p2": "CO2 out", "p3" : "CO2 in", "p4" : "electricity"}

biogas_dict = {"p0": "Biogas in", "p1": "CO2 compressed out", "p2": "gas out" }

electrolysis_dict = {"p0": "electricity in", "p1": "H2 out"}
#%%
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


#---------<<battery plots>>------------------

def battery_plot(path):
    '''As of 24 October, this plots battery charging and discharging'''
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

def battery_dcurve(path):
    '''As of 24 October, this plots battery charging and discharging'''
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
    charging = n.links_t.p0[['battery charger']]
    print(charging.columns)
    charging = charging.sort_values(by = 'battery charger')
    charging.index = range(8760)
    

    discharging = n.links_t.p0[['battery discharger']]
    discharging = discharging.sort_values(by = 'battery discharger')
    discharging.index = range(8760)

    ax.plot(charging, label = "charger")
    ax.plot(discharging, label = "discharger")
    ax.set_ylabel("")
    ax.legend()
    curDT = datetime.now()
    date = curDT.strftime("_%d_%m_%Y")
    fileday = oo[-3]
    filemonth = oo[-2]
    version = "_run_" + fileday + "_" + filemonth +  "_created_" + date
    if methanogen == True:
        ax.set_title("Methanogen--Battery Charge and Discharge")
        plt.savefig("results/Images/methanogen_battery_dcurve" + version + ".pdf")
    else:
        ax.set_title("Sabatier--Battery Charge and Discharge")
        plt.savefig("results/Images/sabatier_battery_dcurve" + version + ".pdf")
    plt.show()


#---------<<Biogas link plots>>------------------
def biogas_link_plot(path):
    '''As of 24 October, this plots the methane link'''
    n = pypsa.Network()
    n.import_from_netcdf(path)
    o = path.split("/")
    oo = [item.split("_") for item in o]
    oo = [item for sublist in oo for item in sublist]

    if "methanogen" in oo:
        methanogen = True
    else:
        methanogen = False


    methanation = "Biogas upgrading"


    #We are interested in the n.links_t dataframes that are dealing with the p in or out of the link
    keydict = [f for f in n.links_t.keys() if "p" in f and f[1:].isdigit() and int(f[1:]) < 3]

    netlinks = pd.DataFrame()

    # We want to plot each of the p# time series present. To do so we add a pd column
    # We want to name the p# values for what they are, and what they represent, using a dict. 
    for key in keydict:
        netlinks[biogas_dict[key]] = n.links_t[key][methanation]

    netlinks = netlinks.rolling(24).mean()
    netlinks = netlinks[::24]

    fig, ax = plt.subplots()
    ax.plot(netlinks, label = netlinks.columns)
    ax.set_ylabel("")
    ax.legend()
    curDT = datetime.now()
    version = curDT.strftime("_%d_%m_%Y")
    if methanogen == True:
        ax.set_title("Biogas upgrading link with methanogenesis")
        plt.savefig("results/Images/methanogenesis_biogas_link" + version + ".pdf")
    else:
        ax.set_title("Biogas upgrading link with sabatier")
        plt.savefig("results/Images/sabatier_biogas_link" + version + ".pdf")
    plt.show()

def biogas_dcurve(path):
    '''As of 24 October, this plots the methane link'''
    n = pypsa.Network()
    n.import_from_netcdf(path)
    o = path.split("/")
    oo = [item.split("_") for item in o]
    oo = [item for sublist in oo for item in sublist]

    if "methanogen" in oo:
        methanogen = True
    else:
        methanogen = False


    methanation = "Biogas upgrading"


    #We are interested in the n.links_t dataframes that are dealing with the p in or out of the link
    keydict = [f for f in n.links_t.keys() if "p" in f and f[1:].isdigit() and int(f[1:]) < 3]

    netlinks = pd.DataFrame()
    fig, ax = plt.subplots()

    # We want to plot each of the p# time series present. To do so we add a pd column
    # We want to name the p# values for what they are, and what they represent, using a dict. 
    for key in keydict:
        netlinks[biogas_dict[key]] = n.links_t[key][methanation]

    netlinks.index = range(8760)
    for column in netlinks.columns:
        netlinks = netlinks.sort_values(by = column)
        netlinks.index = range(8760)
        ax.plot(netlinks[column], label = column)

    # ax.plot(netlinks, label = netlinks.columns)
    ax.set_ylabel("")
    ax.legend()
    curDT = datetime.now()
    date = curDT.strftime("_%d_%m_%Y")
    fileday = oo[-3]
    filemonth = oo[-2]
    version = "_run_" + fileday + "_" + filemonth +  "_created_" + date
    if methanogen == True:
        ax.set_title("Biogas upgrading link with methanogenesis")
        plt.savefig("results/Images/methanogenesis_biogas_dcurve" + version + ".pdf")
    else:
        ax.set_title("Biogas upgrading link with sabatier")
        plt.savefig("results/Images/sabatier_biogas_dcurve" + version + ".pdf")
    plt.show()



#---------<<Electrolysislink plots>>------------------
def electrolysis_link_plot(path):
    '''As of 24 October, this plots the methane link'''
    n = pypsa.Network()
    n.import_from_netcdf(path)
    o = path.split("/")
    oo = [item.split("_") for item in o]
    oo = [item for sublist in oo for item in sublist]

    if "methanogen" in oo:
        methanogen = True
    else:
        methanogen = False


    methanation = "H2 Electrolysis"


    #We are interested in the n.links_t dataframes that are dealing with the p in or out of the link
    keydict = [f for f in n.links_t.keys() if "p" in f and f[1:].isdigit() and int(f[1:]) < 2]

    netlinks = pd.DataFrame()

    # We want to plot each of the p# time series present. To do so we add a pd column
    # We want to name the p# values for what they are, and what they represent, using a dict. 
    for key in keydict:
        netlinks[electrolysis_dict[key]] = n.links_t[key][methanation]

    netlinks = netlinks.rolling(24).mean()
    netlinks = netlinks[::24]

    fig, ax = plt.subplots()
    ax.plot(netlinks, label = netlinks.columns)
    ax.set_ylabel("")
    ax.legend()
    curDT = datetime.now()
    version = curDT.strftime("_%d_%m_%Y")
    if methanogen == True:
        ax.set_title("Electrolysis link with methanogenesis")
        plt.savefig("results/Images/methanogenesis_electrolysis_link" + version + ".pdf")
    else:
        ax.set_title("Electrolysis link with sabatier")
        plt.savefig("results/Images/sabatier_electrolysis_link" + version + ".pdf")
    plt.show()

def electrolysis_dcurve(path):
    '''As of 24 October, this plots the methane link'''
    n = pypsa.Network()
    n.import_from_netcdf(path)
    o = path.split("/")
    oo = [item.split("_") for item in o]
    oo = [item for sublist in oo for item in sublist]

    if "methanogen" in oo:
        methanogen = True
    else:
        methanogen = False


    methanation = "H2 Electrolysis"


    #We are interested in the n.links_t dataframes that are dealing with the p in or out of the link
    keydict = [f for f in n.links_t.keys() if "p" in f and f[1:].isdigit() and int(f[1:]) < 2]

    netlinks = pd.DataFrame()

    # We want to plot each of the p# time series present. To do so we add a pd column
    # We want to name the p# values for what they are, and what they represent, using a dict. 
    for key in keydict:
        netlinks[electrolysis_dict[key]] = n.links_t[key][methanation]



    fig, ax = plt.subplots()


    netlinks.index = range(8760)
    for column in netlinks.columns:
        netlinks = netlinks.sort_values(by = column)
        netlinks.index = range(8760)
        ax.plot(netlinks[column], label = column)

    ax.set_ylabel("")
    ax.legend()
    curDT = datetime.now()
    date = curDT.strftime("_%d_%m_%Y")
    fileday = oo[-3]
    filemonth = oo[-2]
    version = "_run_" + fileday + "_" + filemonth +  "_created_" + date
    if methanogen == True:
        ax.set_title("Electrolysis link with methanogenesis")
        plt.savefig("results/Images/methanogenesis_electrolysis_dcurve" + version + ".pdf")
    else:
        ax.set_title("Electrolysis link with sabatier")
        plt.savefig("results/Images/sabatier_electrolysis_dcurve" + version + ".pdf")
    plt.show()



#---------<<Storage plots>>------------------
def storage_plots(path):
    '''As of 24 October, this plots the methane link'''
    n = pypsa.Network()
    n.import_from_netcdf(path)
    o = path.split("/")
    oo = [item.split("_") for item in o]
    oo = [item for sublist in oo for item in sublist]

    if "methanogen" in oo:
        methanogen = True
    else:
        methanogen = False


    netlinks = pd.DataFrame()

    columns = [column for column in n.stores_t['e'].columns]
    for column in columns:
        netlinks[column] = n.stores_t['e'][column]

    netlinks = netlinks.rolling(24).mean()
    netlinks = netlinks[::24]
    

    fig, ax = plt.subplots()
    ax.plot(netlinks, label = netlinks.columns)
    ax.set_ylabel("")
    ax.legend()
    ax.set_yscale("log")
    curDT = datetime.now()
    date = curDT.strftime("_%d_%m_%Y")
    fileday = oo[-3]
    filemonth = oo[-2]
    version =  "_run_" + fileday + "_" + filemonth +  "_created_" + date
    if methanogen == True:
        ax.set_title("Store units with methanogenesis")
        plt.savefig("results/Images/methanogenesis_stores" + version + ".pdf")
    else:
        ax.set_title("Store units sabatier")
        plt.savefig("results/Images/sabatier_stores" + version + ".pdf")
    plt.show()

def storage_dcurve(path, yscale):
    '''As of 24 October, this plots the methane link'''
    n = pypsa.Network()
    n.import_from_netcdf(path)
    o = path.split("/")
    oo = [item.split("_") for item in o]
    oo = [item for sublist in oo for item in sublist]

    if "methanogen" in oo:
        methanogen = True
    else:
        methanogen = False


    netlinks = pd.DataFrame()

    columns = [column for column in n.stores_t['e'].columns]
    for column in columns:
        netlinks[column] = n.stores_t['e'][column]


    fig, ax = plt.subplots()
    netlinks.index = range(8760)
    for column in netlinks.columns:
        netlinks = netlinks.sort_values(by = column)
        netlinks.index = range(8760)
        ax.plot(netlinks[column], label = column)
    



    ax.set_ylabel("")
    ax.legend()

    log = ""
    if yscale == "log":
        ax.set_yscale("log")
        log = "log"

    curDT = datetime.now()
    date = curDT.strftime("_%d_%m_%Y")
    fileday = oo[-3]
    filemonth = oo[-2]
    version =  log + "_run_" + fileday + "_" + filemonth +  "_created_" + date
    
    if methanogen == True:
        ax.set_title("Store units with methanogenesis")
        plt.savefig("results/Images/methanogenesis_stores_dcurve" + version + ".pdf")
    else:
        ax.set_title("Store units sabatier")
        plt.savefig("results/Images/sabatier_stores_dcurve" + version + ".pdf")
    plt.show()



#---------<<Methanation link plots>>------------------
def methane_link_plot(path):
    '''As of 24 October, this plots the methane link'''
    n = pypsa.Network()
    n.import_from_netcdf(path)
    o = path.split("/")
    oo = [item.split("_") for item in o]
    oo = [item for sublist in oo for item in sublist]

    if "methanogen" in oo:
        methanogen = True
        methanation = "methanogens"
    else:
        methanogen = False
        methanation = "sabatier"

    #We are interested in the n.links_t dataframes that are dealing with the p in or out of the link
    keydict = [f for f in n.links_t.keys() if "p" in f and f[1:].isdigit()]

    netlinks = pd.DataFrame()

    # We want to plot each of the p# time series present. To do so we add a pd column
    # We want to name the p# values for what they are, and what they represent, using a dict. 
    for key in keydict:
        netlinks[methanation_link_dict[key]] = n.links_t[key][methanation]

    fig, ax = plt.subplots()
    ax.plot(netlinks, label = netlinks.columns)
    ax.set_ylabel("")
    ax.legend()
    curDT = datetime.now()
    version = curDT.strftime("_%d_%m_%Y")
    if methanogen == True:
        ax.set_title("Methanogenesis link")
        plt.savefig("results/Images/methanogenesis_link" + version + ".pdf")
    else:
        ax.set_title("Sabatier link")
        plt.savefig("results/Images/sabatier_link" + version + ".pdf")
    plt.show()

def methane_link_dcurve(path):
    '''As of 24 October, this plots the methane link'''
    n = pypsa.Network()
    n.import_from_netcdf(path)
    o = path.split("/")
    oo = [item.split("_") for item in o]
    oo = [item for sublist in oo for item in sublist]

    if "methanogen" in oo:
        methanogen = True
        methanation = "methanogens"
    else:
        methanogen = False
        methanation = "sabatier"

    #We are interested in the n.links_t dataframes that are dealing with the p in or out of the link
    keydict = [f for f in n.links_t.keys() if "p" in f and f[1:].isdigit()]

    netlinks = pd.DataFrame()

    # We want to plot each of the p# time series present. To do so we add a pd column
    # We want to name the p# values for what they are, and what they represent, using a dict. 
    for key in keydict:
        netlinks[methanation_link_dict[key]] = n.links_t[key][methanation]





    fig, ax = plt.subplots()

    netlinks.index = range(8760)
    for column in netlinks.columns:
        netlinks = netlinks.sort_values(by = column)
        netlinks.index = range(8760)
        ax.plot(netlinks[column], label = column)
    ax.set_ylabel("")
    ax.legend()
    curDT = datetime.now()
    date = curDT.strftime("_%d_%m_%Y")
    fileday = oo[-3]
    filemonth = oo[-2]
    version = "_run_" + fileday + "_" + filemonth +  "_created_" + date

    if methanogen == True:
        ax.set_title("Methanogenesis link--gas out")
        plt.savefig("results/Images/methanogenesis_dcurve" + version + ".pdf")
    else:
        ax.set_title("Sabatier link--gas out")
        plt.savefig("results/Images/sabatier_dcurve" + version + ".pdf")
    plt.show()


methanogen = "results/NetCDF/methanogen_31_10_2022.nc"
sabatier = "results/NetCDF/sabatier_31_10_2022.nc"



# %%    
if __name__ == "__main__":
    storage_dcurve(methanogen, "lin")
    storage_dcurve(sabatier, "lin")
# %%    
if __name__ == "__main__":
    electrolysis_dcurve(methanogen)
    electrolysis_dcurve(sabatier)

# %%    
if __name__ == "__main__":
    biogas_dcurve(methanogen)
    biogas_dcurve(sabatier)


# %%    
if __name__ == "__main__":
    battery_dcurve(methanogen)
    battery_dcurve(sabatier)

# %%    
if __name__ == "__main__":
    methane_link_dcurve(methanogen)
    methane_link_dcurve(sabatier)

# %%    
if __name__ == "__main__":
    make_plot(methanogen)

    make_plot(sabatier)

# %%
if __name__ == "__main__":
    methane_link_plot(methanogen)
    methane_link_plot(sabatier)

# %%
if __name__ == "__main__":
    biogas_link_plot(methanogen)
    biogas_link_plot(sabatier)

# %%
if __name__ == "__main__":
    electrolysis_link_plot(methanogen)
    electrolysis_link_plot(sabatier)

# %%
if __name__ == "__main__":
    storage_plots(methanogen)
    storage_plots(sabatier)
