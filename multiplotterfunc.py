
# %%
import pypsa
import numpy as np
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.colors import LogNorm
import re
import math
import glob
import itertools

from helpers import annual_cost



#%%
#For my links, I always set the following relationship. methanogens does not have electricity

methanation_link_dict = {"p0": "Hydrogen in", "p1": "Gas out", "p2": "CO2 out", "p3" : "CO2 in", "p4" : "electricity"}

biogas_dict = {"p0": "Biogas in", "p1": "CO2 compressed out", "p2": "gas out" }

electrolysis_dict = {"p0": "electricity in", "p1": "H2 out"}

annualcosts = [str(round(x)) for x in np.logspace(-1, 1, 10) * annual_cost("methanation")] #This is the list of all of the costs

linkcost_mults = [round(x, 1) for x in np.logspace(-1, 1, 10)]

costmult_dict = dict(zip(annualcosts, linkcost_mults))

#---------<<generatorplots>>------------------
def generators_dcurve(path, yscale):
    n = pypsa.Network()
    n.import_from_netcdf(path)
    o = path.split("/")
    oo = o[-1]
    num = re.findall('\d*\.?\d+',oo)[0]

    methanogen = True

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
    ax.set_ylim(0.5, 10**7)
    curDT = datetime.now()

    version = "_" + num + log
    if methanogen == True:
        ax.set_title("Generators with methanogenesis")
        plt.savefig("results/Images/03_11_2022_log_cost_sweep/methanogenesis_generator_dcurve" + version + ".pdf")
    else:
        ax.set_title("Generators with sabatier")
        plt.savefig("results/Images/03_11_2022_log_cost_sweep/methanogenesis_generator_dcurve" + version + ".pdf")
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

def battery_dcurve(path, yscale):
    '''As of 24 October, this plots battery charging and discharging'''
    n = pypsa.Network()
    n.import_from_netcdf(path)
    o = path.split("/")
    oo = o[-1]
    num = re.findall('\d*\.?\d+',oo)[0]



    fig, ax = plt.subplots()
    charging = n.links_t.p0[['battery charger']]

    charging = charging.sort_values(by = 'battery charger')
    charging.index = range(8760)
    

    discharging = n.links_t.p0[['battery discharger']]
    discharging = discharging.sort_values(by = 'battery discharger')
    discharging.index = range(8760)

    ax.plot(charging, label = "charger")
    ax.plot(discharging, label = "discharger")
    ax.set_ylabel("")
    ax.legend()

 

    log = ""
    if yscale == "log":
        ax.set_yscale("log")
        log = "log"

    methanation = True


    version = "_" + num + log
    if methanation == True:

        ax.set_title("Methanogen--Battery Charge and Discharge")
        plt.savefig("results/Images/03_11_2022_log_cost_sweep/methanogen_battery_dcurve" + version + ".pdf")
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
    name = o[-2]
    oo = o[-1]
    num = re.findall('\d*\.?\d+',oo)[0]

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
    methanogen = True
    version = "_" + num + log
    

    if methanogen == True:
        ax.set_title("Store units with methanogenesis " + num + " kW")
        plt.savefig("results/Images/" + name + "/methanogenesis_stores_dcurve" + version + ".pdf")
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
    name = o[-2]
    oo = o[-1]
    num = re.findall('\d*\.?\d+',oo)[0]

    #We are interested in the n.links_t dataframes that are dealing with the p in or out of the link
    keydict = [f for f in n.links_t.keys() if "p" in f and f[1:].isdigit()]

    netlinks = pd.DataFrame()

    # We want to plot each of the p# time series present. To do so we add a pd column
    # We want to name the p# values for what they are, and what they represent, using a dict. 
    for key in keydict:
        netlinks[methanation_link_dict[key]] = n.links_t[key]['methanogens']





    fig, ax = plt.subplots()

    netlinks.index = range(8760)
    for column in netlinks.columns:
        netlinks = netlinks.sort_values(by = column)
        netlinks.index = range(8760)
        ax.plot(netlinks[column], label = column)
    ax.set_ylabel("")
    ax.legend()


    version = "_" + num

    methanogen = True
    if methanogen == True:
        ax.set_title("Methanogenesis link " + num + " kW")
        plt.savefig("results/Images/" + name + "/methanogenesis_dcurve" + version + ".pdf")
    else:
        ax.set_title("Sabatier link--gas out")
        plt.savefig("results/Images/sabatier_dcurve" + version + ".pdf")
    plt.show()


def dcurve_gridlink():
    path = "results/NetCDF/03_11_2022_log_cost_sweep"
    fig, ax = plt.subplots()

    for file in glob.glob(path):
        n = pypsa.Network()
        n.import_from_netcdf(file)
        o = file.split("/")
        o = o[-1]
        oo = o.split(".")
        oo 
        

        gridlink = n.links_t.p1.loc[:, "High to low voltage"]
        gridlink = gridlink.apply(lambda row: 0 if row['High to low voltage'] < 0 else row ['High to low voltage'], axis = 1)
        gridlink = gridlink.abs()
        gridlink = gridlink.sort_values(ascending = False)
        gridlink.index = range(8760)
        ax.plot(gridlink)
        


#%%
def extract_pathinfo(path):
    o = path.split("/")
    o = o[-1]
    oo = re.findall(r"\d+", o)
    #oo[0] = avg kW, oo[1] = annualcost
    return oo


def plot_linksize():

    #This needs:

        #To change the label back to
    sumdata = pd.read_csv("results/csvs/summary_15_11_2022_gasdem_megencost_sweep.csv")
    fig, ax = plt.subplots()
    cmap = plt.get_cmap('summer_r')
    
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Annualized cost of methanogenesis (Eur/kW)")
    ax.set_ylabel("Size of methanation link (kW)")
    ax.set_title("Size of methanogenesis")

    norm = LogNorm()# The log norm is necessary to show the logarithmic spacing of the "third axis"
    myax = ax.scatter(sumdata['megen cost'], sumdata['megen size'], c = sumdata['load']/sumdata['load'].max(), cmap = cmap, norm = norm)
    ax.axvline(annual_cost('methanation'), color='black',ls='--') #This is the benchmark cost
    ax.text(annual_cost('methanation')* 0.9, 4, "Base cost of sabatier methanation", horizontalalignment = "center", rotation = "vertical")

    cbar = fig.colorbar(myax, label = "Average gas load (kWh)")
    #     spacing='proportional',  format='%1i')
    tls = cbar.ax.get_yticks()
    tls = [tl * 10000 for tl in tls ]
    cbar.set_ticklabels(tls)

    plt.savefig("Presentations/November18pres/opt_methanogenesis_size.pdf")
    plt.savefig("Presentations/November18pres/opt_methanogenesis_size.png", dpi = 500)
    plt.show()

        

def plot_objective():
    sumdata = pd.read_csv("results/csvs/summary_15_11_2022_gasdem_megencost_sweep.csv")
    fig, ax = plt.subplots()
    cmap = plt.get_cmap('summer_r')
    
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Annualized cost of methanogenesis (Eur/kW)")
    ax.set_ylabel("Extra cost to system")
    ax.set_title("Objective of the system minus smallest case")

    norm = LogNorm()# The log norm is necessary to show the logarithmic spacing of the "third axis"
    myax = ax.scatter(sumdata['megen cost'], sumdata['obj diff to min'], c = sumdata['load']/sumdata['load'].max(), cmap = cmap, norm = norm)
    ax.axvline(annual_cost('methanation'), color='black',ls='--') #This is the benchmark cost
    ax.text(annual_cost('methanation')* 0.9, 100, "Base cost of sabatier methanation", horizontalalignment = "center", rotation = "vertical")

    cbar = fig.colorbar(myax, label = "Average gas load (kWh)")
    #     spacing='proportional',  format='%1i')
    tls = cbar.ax.get_yticks()
    tls = [tl * 10000 for tl in tls ]
    cbar.set_ticklabels(tls)

    plt.savefig("Presentations/November18pres/objective.pdf")
    plt.savefig("Presentations/November18pres/objective.png", dpi = 500)
    plt.show()  
        
        

def plot_costpergas():
    sumdata = pd.read_csv("results/csvs/summary_15_11_2022_gasdem_megencost_sweep.csv")
    sumdata = sumdata[sumdata['load'] != 1]

    fig, ax = plt.subplots()
    cmap = plt.get_cmap('summer_r')
    
    ax.set_xscale("log")
    # ax.set_yscale("log")

    ax.set_xlabel("Annualized cost of methanogenesis (Eur/kW)")
    ax.set_ylabel("Price per kWh gas")
    ax.set_title("Price per kWh gas, over the first kWh")

    norm = LogNorm()# The log norm is necessary to show the logarithmic spacing of the "third axis"
    myax = ax.scatter(sumdata['megen cost'], sumdata['obj per kWh gas'], c = sumdata['load']/sumdata['load'].max(), cmap = cmap, norm = norm)
    ax.axvline(annual_cost('methanation'), color='black',ls='--') #This is the benchmark cost
    ax.text(annual_cost('methanation')* 0.9, 100, "Base cost of sabatier methanation", horizontalalignment = "center", rotation = "vertical")

    cbar = fig.colorbar(myax, label = "Average gas load (kWh)")
    #     spacing='proportional',  format='%1i')
    tls = cbar.ax.get_yticks()
    tls = [tl * 10000 for tl in tls ]
    cbar.set_ticklabels(tls)

    # plt.savefig("Presentations/November18pres/objectiveper2log.pdf")
    # plt.savefig("Presentations/November18pres/objectiveper2log.png", dpi = 500)
    plt.show()     




def plot_gridtoelec_dcurv():
    
    df = pd.read_csv("results/csvs/15_11_2022_gasdem_megencost_sweep.csv")
    loads = df['load'].unique()
    megen_costs = df['megen cost'].unique()

    pairs =  list(itertools.product(loads, megen_costs))
    fig, ax = plt.subplots()

    for pair in pairs:
        a_load = pair[0]
        a_cost = pair[1]
        tempdf = df[(df["load"] == a_load) & (df["megen cost"] == a_cost)]
        tempdf = tempdf.sort_values(by = ["grid to electricity link ts"], ascending = False)
        tempdf.index = range(8760)
        ax.plot(tempdf['grid to electricity link ts'])
    #Here, select one individual time series
