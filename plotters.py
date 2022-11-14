
# %%
import pypsa
import numpy as np
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib as mpl


#%%
#For my links, I always set the following relationship. methanogens does not have electricity

methanation_link_dict = {"p0": "Hydrogen in", "p1": "Gas out", "p2": "CO2 out", "p3" : "CO2 in", "p4" : "electricity"}

biogas_dict = {"p0": "Biogas in", "p1": "CO2 compressed out", "p2": "gas out" }

electrolysis_dict = {"p0": "electricity in", "p1": "H2 out"}
#%%


#---------<<generatorplots>>------------------
def generators_dcurve(path, yscale):
    n = pypsa.Network()
    n.import_from_netcdf(path)
    o = path.split("/")
    oo = [item.split("_") for item in o]
    oo = [item for sublist in oo for item in sublist]

    if "methanogen" in oo:
        methanogen = True
    else:
        methanogen = False


    netlinks = n.generators_t.p

    fig, ax = plt.subplots()


    netlinks.index = range(8760)
    for column in netlinks.columns:
        netlinks = netlinks.sort_values(by = column)
        netlinks.index = range(8760)
        ax.plot(netlinks[column], label = column)

    log = ""
    if yscale == "log":
        ax.set_yscale("log")
        log = "log"

    ax.set_ylabel("")
    ax.legend()
    curDT = datetime.now()
    date = curDT.strftime("_%d_%m_%Y")
    fileday = oo[-3]
    filemonth = oo[-2]
    version = log + "_run_" + fileday + "_" + filemonth +  "_created_" + date
    if methanogen == True:
        ax.set_title("Generators with methanogenesis")
        plt.savefig("results/Images/methanogenesis_generator_dcurve" + version + ".pdf")
    else:
        ax.set_title("Generators with sabatier")
        plt.savefig("results/Images/sabatier_generators_dcurve" + version + ".pdf")
    plt.show()




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

methanogen = "results/NetCDF/methanogen_02_11_2022.nc"
sabatier = "results/NetCDF/sabatier_01_11_2022.nc"

#%%


if __name__ == "__main__":
    generators_dcurve(methanogen, "log")



# %%    
if __name__ == "__main__":
    storage_dcurve(methanogen, "lin")
    # storage_dcurve(sabatier, "lin")
# %%    
if __name__ == "__main__":
    electrolysis_dcurve(methanogen)
    # electrolysis_dcurve(sabatier)

# %%    
if __name__ == "__main__":
    biogas_dcurve(methanogen)
    # biogas_dcurve(sabatier)


# %%    
if __name__ == "__main__":
    battery_dcurve(methanogen)
    # battery_dcurve(sabatier)

# %%    
if __name__ == "__main__":
    methane_link_dcurve(methanogen)
    # methane_link_dcurve(sabatier)
