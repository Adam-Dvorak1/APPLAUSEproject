'''The purpose of this file is to house the functions that I use to plot my results'''
# %%
import pypsa
import numpy as np
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.colors import LogNorm
from pathlib import Path
import re
import math
import glob
import itertools
import seaborn as sns

from helpers import annual_cost



#%%
#For my links, I always set the following relationship. methanogens does not have electricity

methanation_link_dict = {"p0": "Hydrogen in", "p1": "Gas out", "p2": "CO2 out", "p3" : "CO2 in", "p4" : "electricity"}

biogas_dict = {"p0": "Biogas in", "p1": "CO2 compressed out", "p2": "gas out" }

electrolysis_dict = {"p0": "electricity in", "p1": "H2 out"}

sizename_dict = {'megen': 'methanogen link', 'electrolyzer': 'electrolyzer', 'solar': 'solar generator', 'battery': 'battery', 'H2 store':'H2 store'}

unit_dict = {'megen': 'kW', 'electrolyzer': 'kW', 'solar': 'kW', 'battery': 'kWh', 'H2 store': 'kWh'}

annualcosts = [str(round(x)) for x in np.logspace(-1, 1, 10) * annual_cost("methanation")] #This is the list of all of the costs

linkcost_mults = [round(x, 1) for x in np.logspace(-1, 1, 10)]

costmult_dict = dict(zip(annualcosts, linkcost_mults))

#---------<<Other  dicts>------------------

color_dict = {"battery": '#9467bd', "battery charger":'#1f77b4', "methanogens": '#2ca02c', "Solar PV": '#ff7f0e',
"H2 Electrolysis": '#d62728', "grid elec total cost": '#7f7f7f', "grid elec total income": '#e377c2', "H2 store": '#c251ae'}



#%%
def extract_pathinfo(path):
    o = path.split("/")
    o = o[-1]
    oo = re.findall(r"\d+", o)
    #oo[0] = avg kW, oo[1] = annualcost
    return oo


def plot_linksize(path):

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
        




def plot_anysize(path, vartype):
    '''The purpose of this function is to be able to plot any of the variables where we are keeping track of size.
    This includes the methanogen (megen), electrolyzer, solar generator (solar), battery, and hydrogen store (H2)'''
    data = pd.read_csv(path)


    presentationdate = "January31pres"

    o = path.split("_")
    if "nosolar" in o:
        model = "nosolar"
    elif 'nogrid' in o:
        model = 'nogrid'
    else:
        model = "gridsolar"



    varsize = vartype + " size"

    sumdata = data.drop_duplicates(['megen cost', 'load'])
    fig, ax = plt.subplots()
    cmap = plt.get_cmap('summer_r')
    
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Annualized cost of methanogenesis (Eur/kW)")
    ax.set_ylabel(vartype + " capacity (" + unit_dict[vartype] + ")")
    ax.set_title("Size of the " + sizename_dict[vartype] + " " + model )

    norm = LogNorm()# The log norm is necessary to show the logarithmic spacing of the "third axis"
    myax = ax.scatter(sumdata['megen cost'], sumdata[varsize], c = sumdata['load']/sumdata['load'].max(), cmap = cmap, norm = norm)
    ax.axvline(annual_cost('methanation'), color='black',ls='--') #This is the benchmark cost
    ax.text(0.48, 0.2, "Base cost of sabatier methanation", horizontalalignment = "center", rotation = "vertical", transform = ax.transAxes)



    ##############    color bar    ##############
    cbar = fig.colorbar(myax, label = "Average gas load (kWh)")
    tls = cbar.ax.get_yticks()
    tls = [tl * 10000 for tl in tls ]
    cbar.set_ticklabels(tls)

    prespath = "Presentations/" + presentationdate + "/"  + model + "/sizes/" + vartype + "_size"

    plt.savefig(prespath + '.pdf')
    plt.savefig(prespath + '.png', dpi = 500)
    plt.close('all') 



def plot_anysize_all():
    rel_paths = ["results/csvs/alldata/25_01_2023_gasdem_megencost_sweep_nogrid_wo_hstore.csv",
                "results/csvs/alldata/25_01_2023_gasdem_megencost_sweep_nogrid_w_hstore.csv",
                "results/csvs/alldata/25_01_2023_gasdem_megencost_sweep_nosolar_w_hstore.csv",
                "results/csvs/alldata/25_01_2023_gasdem_megencost_sweep_nosolar_wo_hstore.csv",
                "results/csvs/alldata/25_01_2023_gasdem_megencost_sweep_w_hstore.csv",
                "results/csvs/alldata/25_01_2023_gasdem_megencost_sweep_wo_hstore.csv"
                ]


 
            
    
    for path in rel_paths:
        o = path.split("_")
        if "w" in o:
            plot_anysize(path, "H2 store")
        if "nosolar" not in o:
            plot_anysize(path, "solar")
            plot_anysize(path, "battery")
        
        plot_anysize(path, 'electrolyzer')
        plot_anysize(path, 'megen')



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









def extract_colors():
    cmap = plt.get_cmap('summer_r')
    loads = np.logspace(0, 4, 10)
    loadfracs = [x/10000 for x in loads]
    norm = LogNorm(vmin = min(loadfracs), vmax = max(loadfracs))

    testclr = [cmap(norm(x)) for x in range(len(loadfracs))]

    


    df = pd.read_csv("results/csvs/15_11_2022_gasdem_megencost_sweep.csv")








#%%
def plot_costs(path):
    
    costdf = pd.read_csv(path)

    costdf = costdf.loc[:,  (costdf != 0).any(axis=0)]

    fulldf = costdf

    for val in fulldf['Gas Load'].unique():
        costdf = fulldf.loc[fulldf["Gas Load"] == val, :]
        costdf = costdf.sort_values(by ="methanogen capital cost")
        costdf.index = costdf["methanogen capital cost"].round(1)

        ax = costdf[costdf.columns[2:]].plot( kind = "bar", stacked = True)
        ax.set_ylabel("Euros")
        ax.set_xlabel("Methanogen cost")
        ax.set_title("Cost breakdown by no-grid element for a gas load of " + str(val), y = 1.04)

        box = ax.get_position()
        ax.set_position([box.x0, box.y0 + box.height * 0.1,
                    box.width, box.height * 0.9])

        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles[::-1], labels[::-1], loc='upper center', bbox_to_anchor=(0.5, -0.25), ncol =3)




        plt.subplots_adjust(bottom = 0.2)
        savepath = "Presentations/December2pres/costs/nogrid_barplot_" + str(val) + "_gas_dem"
        plt.tight_layout()
        plt.savefig(savepath + ".pdf")
        plt.savefig(savepath + ".png", dpi = 500)
        plt.close()


def plot_costper(path): 
    #December 5
    '''We are interested in the price of gas per MWh. The november 1 price is about 125 Euro/MWh. so this is included
    Takes a costs csv as input, made from get_costs() in helpers.py, which should be stored in results/csvs/costs
    
    We modified this 7.2 because now we are also looking at the electrolyzer capital cost'''

    costdf = pd.read_csv(path, index_col = 0)

    presentation = 'February10pres'

    o = path.split("_")
    if 'nogrid' in o:
        experiment = "nogrid"
    elif "nosolar" in o:
        experiment = "nosolar"
    else:
        experiment = "gridsolar"


    if 'year' in o:
        sweep = "grid_year"
    elif "electrolyzer" in o:
        sweep = "electrolyzer_cost"
    else:
        sweep = "megen_cost"

    costdf = costdf.loc[:,  (costdf != 0).any(axis=0)]#If any of the values of the column are not 0, keep them. Gets rid of generators/links etc with no cost

    #only positive--so no "income"
    if experiment != "gridsolar":
        costdf = costdf.loc[:,  (costdf > 0).any(axis=0)]#If any of the values of the column are not negative, keep them. Gets rid of the "income"

    fulldf = costdf


    folderpath = "Presentations/"+ presentation + "/" +  experiment + "/costsper" 


    for val in fulldf['methanogen capital cost'].unique():
        costdf = fulldf.loc[fulldf['methanogen capital cost'] == val, :]
        costdf = costdf.sort_values(by ="electrolyzer capital cost")
        costdf.index = costdf["electrolyzer capital cost"].round(1)
        costdf = costdf/val/8760*1000 #price per MWh

        colors = [color_dict[colname] for colname in costdf.columns.get_level_values(0)[3:]]

        ax = costdf[costdf.columns[3:]].plot( kind = "bar", stacked = True, color = colors)


        ax.set_ylabel("LCOE (Euros/MWh_energy)")
        ax.set_xlabel("Electrolyzer cost (Eur/kWh)")
        
        val = round(val, 1)
        ax.set_title("Cost(+) per MWh breakdown " + experiment + " " + sweep +  " model for megen cost of " + str(val) + "kWh")

        ax.axhline(135, label = "2-Dec-22 price")
        ax.axhline (36, label = "1-Jul-21 price", color = "#ff7f0e")
        ax.axhline (10, label = "1-Jul-19 price", color = "#2ca02c")



        box = ax.get_position()
        ax.set_position([box.x0, box.y0 + box.height * 0.1,
                    box.width, box.height * 0.9])

        # ax.text(0.2, 0.4, "Europe price per MWh as of November 1", transform= ax.transAxes)
        
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles[::-1], labels[::-1], loc='upper center', bbox_to_anchor=(0.5, -0.25), ncol =3)





        plt.subplots_adjust(bottom = 0.2)

        plt.tight_layout()

        savepath = folderpath + "/"+ experiment + "_barplot_" + sweep + "_megen_cost_" + str(val)
        plt.savefig(savepath + ".pdf")
        plt.savefig(savepath + ".png", dpi = 500)
        plt.close()





def find_net_income(path):
    '''This function will be able to tell you the amount of money made in the system. It takes the costs csv as income, 
    and it requires the full system model.
    
    We need a base system to compare to, so we take a very low (1 kW demand) system, to determine the system behavior
    if there was "no" gas demand. This is put into mindf.
    
    Note: whenever we add or subtract columns, we may need to adjust the columns here. If we want to plot csvs older than
    6 February, we may need to adjust columsn here.'''

    costdf = pd.read_csv(path, index_col = 0)

    mindf = pd.read_csv("results/csvs/costs/25_01_2023_gasdem_megencost_sweep_w_hstore.csv", index_col=0)

    gasload = 10000

    o = path.split("_")
    if 'year' in o:
        experiment = "grid_year"
    elif "electrolyzer" in o:
        experiment = "electrolyzer_cost"
    else:
        experiment = "megen_cost"

    presentation = 'February10pres'

    # If any of the values of the column are not 0, keep them. 
    # Gets rid of generators/links etc with no cost
    costdf = costdf.loc[:,  (costdf != 0).any(axis=0)]



    # To find the net income, add up all of the total income and expenses. Costs are positive
    # and income is negative. Then, multiply by -1 to get the positive balance if you made money 
    # This skips over Gas Load, methanogen capital cost, and electrolyzer capital cost. If 'year'
    # is in the columns, it also skips over that
    if 'year' not in costdf.columns:
        costdf['Net income'] = costdf[costdf.columns[3:]].sum(axis = 1) * -1
    else:
        costdf['Net income'] = costdf[costdf.columns[4:]].sum(axis = 1) * -1

    mindf['Net income'] = mindf[mindf.columns[2:]].sum(axis = 1) * -1 #Before we did not care about the electrolyzer capital cost. If we change the mindf, we will need to change this as well.

    # How much can you expect to make with basically 0 gas load--ie, the solar system and the
    # battery is financing itself for the grid
    sys_income = mindf.loc[(mindf['Gas Load'] == 1) & (mindf['methanogen capital cost'] == mindf['methanogen capital cost'].min())]['Net income'].values[0]

    # Making it orderly for my view
    costdf = costdf.sort_values(['Gas Load', 'methanogen capital cost'])

    # Now the 'cost diff' column is how much money is being lost--it is the cost of the case
    # with the methanogen, minus the revenue of the case with no gas demand. This only makes
    # sense for the case with high gas load
    costdf['cost diff']= costdf['Net income'] - sys_income 
   
    #Finding cost diff per MW per hour
    costdf['cost diff'] = costdf['cost diff']/8760*1000/gasload * -1 #10000 kW or 10 MW

    costdf = costdf.loc[costdf['Gas Load'] == gasload]




    if experiment == "megen_cost":
        costdf.index = costdf["methanogen capital cost"].round(1)
    elif experiment == "electrolyzer_cost":
        costdf = costdf.loc[costdf['methanogen capital cost'] == 86.72922452359094]
        costdf = costdf.sort_values(['Gas Load', 'electrolyzer capital cost'])
        costdf.index = costdf['electrolyzer capital cost'].round(1)

    ax = costdf['cost diff'].plot(kind = "bar")
    ax.set_ylabel ("Required gas cost (Eur/MWh)")
    ax.set_xlabel("Methanogen cost (Eur/kWh)")


    ax.set_title("Minimum gas cost sweeping " + experiment)
    
    ax.axhline(340, label = '26-Aug-22 price (high)', color = "C0")
    ax.axhline(144, label = "1-Jul-22 price", color = "C1")
    ax.axhline (36, label = "1-Jul-21 price", color = "C2")
    ax.axhline (10, label = "1-Jul-19 price", color = "C3")



    # box = ax.get_position()
    # ax.set_position([box.x0, box.y0 + box.height * 0.1,
    #             box.width, box.height * 0.9])

    
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles[::-1], labels[::-1], loc='upper center', bbox_to_anchor=(0.5, -0.3), ncol = 2)



    plt.subplots_adjust(bottom = 0.2)

    plt.tight_layout()
    
    folderpath = "Presentations/"+ presentation + "/gas_cost_req_by_" + experiment

    # plt.show()
    savepath = folderpath 
    plt.savefig(savepath + ".pdf")
    plt.savefig(savepath + ".png", dpi = 500)
    plt.close()

def find_net_income_pass(path, ax):
    '''This function is the same as find_net_income() except it passes an ax on to another function'''

    costdf = pd.read_csv(path, index_col = 0)

    mindf = pd.read_csv("results/csvs/costs/25_01_2023_gasdem_megencost_sweep_w_hstore.csv", index_col=0)

    gasload = 10000

    o = path.split("_")
    if 'year' in o:
        experiment = "grid_year"
    elif "electrolyzer" in o:
        experiment = "electrolyzer_cost"
    else:
        experiment = "megen_cost"

    presentation = 'February10pres'

    # If any of the values of the column are not 0, keep them. 
    # Gets rid of generators/links etc with no cost
    costdf = costdf.loc[:,  (costdf != 0).any(axis=0)]



    # To find the net income, add up all of the total income and expenses. Costs are positive
    # and income is negative. Then, multiply by -1 to get the positive balance if you made money 
    # This skips over Gas Load, methanogen capital cost, and electrolyzer capital cost. If 'year'
    # is in the columns, it also skips over that
    if 'year' not in costdf.columns:
        costdf['Net income'] = costdf[costdf.columns[3:]].sum(axis = 1) * -1
    else:
        costdf['Net income'] = costdf[costdf.columns[4:]].sum(axis = 1) * -1

    mindf['Net income'] = mindf[mindf.columns[2:]].sum(axis = 1) * -1 #Before we did not care about the electrolyzer capital cost. If we change the mindf, we will need to change this as well.

    # How much can you expect to make with basically 0 gas load--ie, the solar system and the
    # battery is financing itself for the grid
    sys_income = mindf.loc[(mindf['Gas Load'] == 1) & (mindf['methanogen capital cost'] == mindf['methanogen capital cost'].min())]['Net income'].values[0]

    # Making it orderly for my view
    costdf = costdf.sort_values(['Gas Load', 'methanogen capital cost'])

    # Now the 'cost diff' column is how much money is being lost--it is the cost of the case
    # with the methanogen, minus the revenue of the case with no gas demand. This only makes
    # sense for the case with high gas load
    costdf['cost diff']= costdf['Net income'] - sys_income 
   
    #Finding cost diff per MW per hour
    costdf['cost diff'] = costdf['cost diff']/8760*1000/gasload * -1 #10000 kW or 10 MW

    costdf = costdf.loc[costdf['Gas Load'] == gasload]




    if experiment == "megen_cost":
        costdf.index = costdf["methanogen capital cost"].round(1)
    elif experiment == "electrolyzer_cost":
        costdf = costdf.loc[costdf['methanogen capital cost'] == 86.72922452359094]
        costdf = costdf.sort_values(['Gas Load', 'electrolyzer capital cost'])
        costdf.index = costdf['electrolyzer capital cost'].round(1)

    costdf['cost diff'].plot(kind = "bar", ax = ax)
    # ax.set_ylabel ("Required gas cost (Eur/MWh)")
    ax.set_xlabel("")
    



    ax.set_title("Income Req", fontsize = 20)
    
    ax.axhline(340, label = '26-Aug-22 price (high)', color = "C0")
    ax.axhline(144, label = "1-Jul-22 price", color = "C1")
    ax.axhline (36, label = "1-Jul-21 price", color = "C2")
    ax.axhline (10, label = "1-Jul-19 price", color = "C3")






def find_net_income_multiyear(path):
    '''
    9 Feb 2023
    This function will; '''

    costdf = pd.read_csv(path, index_col = 0)

    mindf = pd.read_csv("results/csvs/costs/25_01_2023_gasdem_megencost_sweep_w_hstore.csv", index_col=0)

    gasload = 10000

    o = path.split("_")
    if 'year' in o:
        experiment = "year_sweep"
    elif "electrolyzer" in o:
        experiment = "electrolyzer_cost"
    else:
        experiment = "megen_cost"

    presentation = 'February10pres'

    # If any of the values of the column are not 0, keep them. 
    # Gets rid of generators/links etc with no cost
    costdf = costdf.loc[:,  (costdf != 0).any(axis=0)]

    print(costdf)

    # To find the net income, add up all of the total income and expenses. Costs are positive
    # and income is negative. Then, multiply by -1 to get the positive balance if you made money 
    # This skips over year, Gas Load, methanogen capital cost, and electrolyzer capital cost. If 
    # 'year' is in the columns, it also skips over that
    
    if 'year' not in costdf.columns:
        costdf['Net income'] = costdf[costdf.columns[3:]].sum(axis = 1) * -1
    else:
        costdf['Net income'] = costdf[costdf.columns[4:]].sum(axis = 1) * -1

    mindf['Net income'] = mindf[mindf.columns[2:]].sum(axis = 1) * -1 #Before we did not care about the electrolyzer capital cost. If we change the mindf, we will need to change this as well.

    # How much can you expect to make with basically 0 gas load--ie, the solar system and the
    # battery is financing itself for the grid
    sys_income = mindf.loc[(mindf['Gas Load'] == 1) & (mindf['methanogen capital cost'] == mindf['methanogen capital cost'].min())]['Net income'].values[0]

    # Making it orderly for my view
    costdf = costdf.sort_values(['Gas Load', 'methanogen capital cost'])

    # Now the 'cost diff' column is how much money is being lost--it is the cost of the case
    # with the methanogen, minus the revenue of the case with no gas demand. This only makes
    # sense for the case with high gas load
    costdf['cost diff']= costdf['Net income'] - sys_income 
   
    #Finding cost diff per MW per hour
    costdf['cost diff'] = costdf['cost diff']/8760*1000/gasload * -1 #10000 kW or 10 MW

    costdf = costdf.loc[costdf['Gas Load'] == gasload]

    print(costdf)


    if experiment == "megen_cost":
        costdf.index = costdf["methanogen capital cost"].round(1)
    elif experiment == "electrolyzer_cost":
        costdf = costdf.loc[costdf['methanogen capital cost'] == 86.72922452359094]
        costdf = costdf.sort_values(['Gas Load', 'electrolyzer capital cost'])
        costdf.index = costdf['electrolyzer capital cost'].round(1)

    if experiment != 'year_sweep':
        ax = costdf['cost diff'].plot(kind = "bar")
    else:
        
        costdf['methanogen capital cost'] = costdf["methanogen capital cost"].round(1)
        ax = sns.barplot(x = 'methanogen capital cost', y = 'cost diff', hue = 'year', data = costdf)

    ax.set_ylabel ("Required gas cost (Eur/MWh)")
    ax.set_xlabel("Methanogen cost (Eur/kWh)")


    ax.set_title("Minimum gas cost sweeping " + experiment)
    
    ax.axhline(340, label = '26-Aug-22 price (high)', color = "C0")
    ax.axhline(144, label = "1-Jul-22 price", color = "C1")
    ax.axhline (36, label = "1-Jul-21 price", color = "C2")
    ax.axhline (10, label = "1-Jul-19 price", color = "C3")



    # box = ax.get_position()
    # ax.set_position([box.x0, box.y0 + box.height * 0.1,
    #             box.width, box.height * 0.9])

    
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles[::-1], labels[::-1], loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol = 3)



    plt.subplots_adjust(bottom = 0.2)

    plt.tight_layout()
    
    folderpath = "Presentations/"+ presentation + "/gas_cost_req_by_" + experiment

    savepath = folderpath 
    plt.savefig(savepath + ".pdf")
    plt.savefig(savepath + ".png", dpi = 500)
    plt.close()


def plot_cost_any(path, ax): 
    #December 5
    '''
    9 Feb 2023
    The purpose of this function is to be able to plot cost_any plots side by side
    '''
    costdf = pd.read_csv(path, index_col = 0)

    val = 10000

    o = path.split("_")
    if 'nogrid' in o:
        experiment = "No Grid"
    elif "nosolar" in o:
        experiment = "No Solar"
    else:
        experiment = "Full system"



    costdf = costdf.loc[:,  (costdf != 0).any(axis=0)]#If any of the values of the column are not 0, keep them. Gets rid of generators/links etc with no cost

    #only positive--so no "income"
    if experiment != "Full system":
        costdf = costdf.loc[:,  (costdf > 0).any(axis=0)]#If any of the values of the column are not negative, keep them. Gets rid of the "income"

    
    costdf = costdf.loc[costdf["Gas Load"] == val]
    costdf = costdf.sort_values(by ="methanogen capital cost")
    costdf.index = costdf["methanogen capital cost"].round(1)
    costdf = costdf/val/8760*1000 #price per MWh

    colors = [color_dict[colname] for colname in costdf.columns.get_level_values(0)[2:]]

    costdf[costdf.columns[2:]].plot( kind = "bar", stacked = True, color = colors, ax = ax)


    # ax.set_ylabel("LCOE (Euros/MWh_energy)")
    # ax.set_xlabel("Methanogen cost (Eur/kWh)")
    
    ax.set_xlabel("")
    ax.set_title( experiment, fontsize = 20)
    ax.axhline(340, label = '26-Aug-22 price (high)', color = "C0")
    ax.axhline(144, label = "1-Jul-22 price", color = "C1")
    ax.axhline (36, label = "1-Jul-21 price", color = "C2")
    ax.axhline (10, label = "1-Jul-19 price", color = "C3")
    ax.get_legend().remove()







def four_cost_plot():
    
    presentation = 'February10pres'
    fig, ax = plt.subplots(2,2,figsize=(10,9), sharex=True)
    axs = ax.flatten()

    

    nogrid = 'results/csvs/costs/25_01_2023_gasdem_megencost_sweep_nogrid_w_hstore.csv'
    nosolar = 'results/csvs/costs/25_01_2023_gasdem_megencost_sweep_nosolar_w_hstore.csv'
    gridsolar = 'results/csvs/costs/25_01_2023_gasdem_megencost_sweep_w_hstore.csv'
    plot_cost_any(nogrid, axs[0])
    plot_cost_any(nosolar, axs[1])
    plot_cost_any(gridsolar, axs[2])
    find_net_income_pass(nosolar, axs[3])

    for ax in axs:
        ax.tick_params(axis='both', which='major', labelsize=14)
    
    fig.supylabel("Euro per MWh gas", fontsize = 16)
    fig.supxlabel("Methanogen cost (Eur/kW)", fontsize = 16)
    

    handles, labels = axs[2].get_legend_handles_labels()
    fig.legend(handles, labels, ncol = 3, loc = 'upper center', fontsize = 12)
    fig.subplots_adjust(top = 0.84, bottom = 0.15)



        
    fig.savefig('Presentations/' + presentation + '/megencosts_income.pdf')
    fig.savefig('Presentations/' + presentation + '/megencosts_income.png', dpi = 500)
    plt.show()



##################################################################
######################## DURATION CURVES #########################
##################################################################

def compare_dcurves():
    nosolar = pd.read_csv("results/csvs/06_12_2022_gasdem_megencost_sweep_nosolar.csv")
    nogrid = pd.read_csv("results/csvs/06_12_2022_gasdem_megencost_sweep_nogrid.csv")
    gridsolar = pd.read_csv("results/csvs/06_12_2022_gasdem_megencost_sweep.csv")

    nosolarmax = nosolar.query('load == load.max() & `megen cost` == `megen cost`.max() ')
    nogridmax = nogrid.query('load == load.max() & `megen cost` == `megen cost`.max() ')
    gridsolarmax = gridsolar.query('load == load.max() & `megen cost` == `megen cost`.max() ')


    nosolarmax= nosolarmax.sort_values(by = ["methanogen link ts"], ascending = False)
    nosolarmax.index = range(8760)

    nogridmax = nogridmax.sort_values(by = ["methanogen link ts"], ascending = False)
    nogridmax.index = range(8760)

    gridsolarmax= gridsolarmax.sort_values(by = ["methanogen link ts"], ascending = False)
    gridsolarmax.index = range(8760)

    fig, ax = plt.subplots()

    ax.plot(gridsolarmax['methanogen link ts'], label = "Grid and solar", color = "C2")
    ax.plot(nosolarmax['methanogen link ts'], label = "Only grid", color = "C0")
    ax.plot(nogridmax['methanogen link ts'], label = "Only solar", color = "C1")


    ax.set_title("Dcurve of megen link 3 scenarios, 10MW load and 10x sabatier cost")
    ax.set_xlabel("hours")
    ax.set_ylabel("kWh/h")
    
    ax.legend()
    plt.savefig("Presentations/December8pres/three_dcurve_reverse.pdf")
    plt.savefig("Presentations/December8pres/three_dcurves_reverse.png", dpi = 500)
    plt.show()


def plot_methlink_dcurv(path):
    '''This uses a csv provided by extract_data(), in helpers, to make a plot of all of the duration curves
    for the methanogen link in a given folder '''
    
    presentationdate = "January31pres"

    df = pd.read_csv(path)

    o = path.split("_")
    if 'nogrid' in o:
        experiment = "nogrid"
    elif "nosolar" in o:
        experiment = "nosolar"
    else:
        experiment = "gridsolar"




    loads = df['load'].unique()
    megen_costs = df['megen cost'].unique()

    maxload = df['load'].max()

    pairs =  list(itertools.product(loads, megen_costs))
    # minimum =  min(df['megen cost'])
    # maximum = max (df['megen cost'])
    # pairs = [x for x in pairs if x[1] == minimum or x[1] == maximum]


    fig, ax = plt.subplots()
    # ax.set_yscale("log")
    cmap = plt.get_cmap('summer_r')
    norm = LogNorm(vmin = 1/10000, vmax = 1) #This is the range of fractions for log

    # for pair in pairs:
    #     a_load = pair[0]
    #     fracload = a_load / 10000

    #     a_cost = pair[1]
    #     tempdf = df[(df["load"] == a_load) & (df["megen cost"] == a_cost)]
    #     tempdf = tempdf.sort_values(by = ["electrolyzer ts"], ascending = False)
    #     tempdf.index = range(8760)


    #     ax.plot(tempdf['electrolyzer ts'], color = cmap(norm(fracload)))

    tempdf = df[(df["load"] == 10000) & (df["megen cost"] == max(df['megen cost']))]
    tempdf = tempdf.sort_values(by = ["electrolyzer ts"], ascending = False)
    tempdf.index = range(8760)    
    tempdf['electrolyzer ts'] = tempdf['electrolyzer ts']/tempdf['electrolyzer ts'].max()
    ax.plot(tempdf['electrolyzer ts'], color = 'C0', label = "electrolyzer max megen cost")

    tempdf2 = df[(df["load"] == 10000) & (df["megen cost"] == min(df['megen cost']))]
    tempdf2 = tempdf2.sort_values(by = ["electrolyzer ts"], ascending = False)
    tempdf2.index = range(8760)    
    tempdf2['electrolyzer ts'] = tempdf2['electrolyzer ts']/tempdf2['electrolyzer ts'].max()
    ax.plot(tempdf2['electrolyzer ts'], color = 'C2', label = "electrolyzer min megen cost")

    methlink = df[(df["load"] == 10000) & (df["megen cost"] == max(df['megen cost']))]
    methlink = tempdf.sort_values(by = ["methanogen link ts"], ascending = False)
    methlink.index = range(8760)
    methlink["methanogen link ts"] = methlink["methanogen link ts"]/methlink["methanogen link ts"].max()
    ax.plot(methlink["methanogen link ts"], color = 'C1', label = 'methanogen max megen cost', linewidth = 3)



    methlink2 = df[(df["load"] == 10000) & (df["megen cost"] == min(df['megen cost']))]
    methlink2 = tempdf.sort_values(by = ["methanogen link ts"], ascending = False)
    methlink2.index = range(8760)
    methlink2["methanogen link ts"] = methlink2["methanogen link ts"]/methlink2["methanogen link ts"].max()
    ax.plot(methlink2["methanogen link ts"], color = 'C3', label = 'methanogen min megen cost', linewidth = 2, linestyle = ':')



    # tempdf = df[(df["load"] == 1) & (df["megen cost"] == min(df['megen cost']))]
    # tempdf = tempdf.sort_values(by = ["grid to electricity link ts"], ascending = False)
    # tempdf.index = range(8760)
    # ax.plot(tempdf['grid to electricity link ts'], label = '0.1 x methanation cost')


    # fig.set_size_inches(11, 7)
    ax.set_xlabel("Hours in a year")
    ax.set_ylabel("Normalized to maximum")
    ax.set_title("Dcurves for methanogen link for " + experiment)
    # cbar = fig.colorbar(plt.cm.ScalarMappable(norm = norm, cmap = cmap), label = "Average gas load (kWh)")
    # tls = cbar.ax.get_yticks()
    # tls = [tl * 10000 for tl in tls ]
    # cbar.set_ticklabels(tls)
    ax.legend()

    prespath = "Presentations/" + presentationdate + "/"  + experiment +  "/methlink_electrolyzer_dcurves"

    plt.savefig(prespath + '.pdf')
    plt.savefig(prespath + '.png', dpi = 500)
    plt.show()


def plot_gasstore_dcurv():

    df = pd.read_csv("results/csvs/15_11_2022_gasdem_megencost_sweep.csv")
    
    df['snapshot'] = pd.to_datetime(df['snapshot'])
    loads = df['load'].unique()
    megen_costs = df['megen cost'].unique()

    maxload = df['load'].max()

    pairs =  list(itertools.product(loads, megen_costs))
    minimum =  min(df['megen cost'])
    maximum = max (df['megen cost'])
    # pairs = [x for x in pairs if x[1] == minimum or x[1] == maximum]


    fig, ax = plt.subplots()
    # ax.set_yscale("log")
    cmap = plt.get_cmap('summer_r')
    norm = LogNorm(vmin = 1/10000, vmax = 1) #This is the range of fractions for log

    # for pair in pairs:
    #     a_load = pair[0]
    #     fracload = a_load / 10000

    #     a_cost = pair[1]
    #     tempdf = df[(df["load"] == a_load) & (df["megen cost"] == a_cost)]
    #     # tempdf = tempdf.sort_values(by = ["snapshot"])

    #     tempdf.index = tempdf['snapshot']


    #     ax.plot(tempdf['gas store ts'], color = cmap(norm(fracload)))

    tempdf = df[(df["load"] == maxload) & (df["megen cost"] == maximum)]
    tempdf.index = tempdf['snapshot']
    ax.plot(tempdf['gas store ts'], label = '10x methanation cost')


    tempdf = df[(df["load"] == maxload) & (df["megen cost"] == minimum)]
    tempdf.index = tempdf['snapshot']
    ax.plot(tempdf['gas store ts'], label = '0.1x methanation cost')

    # tempdf = df[(df["load"] == 1) & (df["megen cost"] == min(df['megen cost']))]
    # tempdf = tempdf.sort_values(by = ["grid to electricity link ts"], ascending = False)
    # tempdf.index = range(8760)
    # ax.plot(tempdf['grid to electricity link ts'], label = '0.1 x methanation cost')


    fig.set_size_inches(11, 7)
    ax.set_xlabel("Time")
    ax.set_ylabel("kWh of methane storage")
    ax.set_title("Methane storage over the year")
    # cbar = fig.colorbar(plt.cm.ScalarMappable(norm = norm, cmap = cmap), label = "Average gas load (kWh)")

    # tls = cbar.ax.get_yticks()
    # tls = [tl * 10000 for tl in tls ]
    # cbar.set_ticklabels(tls)
    ax.legend()

    plt.savefig("Presentations/November18pres/minmaxcost_store_yr.pdf")
    plt.savefig("Presentations/November18pres/minmaxcost_store_yr.png", dpi = 500)
    plt.show()

    

def plot_gridtoelec_dcurv(path):
    '''Note, since this plots a dcurv of the electricity flowing between the system and the grid,
    it does not consider the nogrid csvs.
    
    In the old format, the model name would be attached to the .csv once the path is split, so it might save 
    in gridsolar'''
    df = pd.read_csv(path)
    o = path.split("_")
    if "nosolar" in o:
        model = "nosolar"
    else:
        model = "gridsolar"


    presentationdate = "January31pres"

    loads = df['load'].unique()

    megen_costs = df['megen cost'].unique()

    maxload = df['load'].max()

    pairs =  list(itertools.product(loads, megen_costs))
    minimum =  min(df['megen cost'])
    maximum = max (df['megen cost'])
    # pairs = [x for x in pairs if x[1] == minimum or x[1] == maximum]

    fig, ax = plt.subplots()
    ax.set_yscale("symlog", linthresh = 1)
    cmap = plt.get_cmap('summer_r')
    norm = LogNorm(vmin = 1/10000, vmax = 1) #This is the range of fractions for log

    for pair in pairs:
        a_load = pair[0]
        fracload = a_load / 10000

        a_cost = pair[1]
        tempdf = df[(df["load"] == a_load) & (df["megen cost"] == a_cost)]
        tempdf = tempdf.sort_values(by = ["grid to electricity link ts"], ascending = False)
        tempdf.index = range(8760)


        fax = ax.plot(tempdf['grid to electricity link ts'], color = cmap(norm(fracload)))

    # tempdf = df[(df["load"] == 1) & (df["megen cost"] == max(df['megen cost']))]
    # tempdf = tempdf.sort_values(by = ["grid to electricity link ts"], ascending = False)
    # tempdf.index = range(8760)    
    # ax.plot(tempdf['grid to electricity link ts'], label = '10x methanation cost')



    # tempdf = df[(df["load"] == 1) & (df["megen cost"] == min(df['megen cost']))]
    # tempdf = tempdf.sort_values(by = ["grid to electricity link ts"], ascending = False)
    # tempdf.index = range(8760)
    # ax.plot(tempdf['grid to electricity link ts'], label = '0.1 x methanation cost')


    fig.set_size_inches(11, 7)
    ax.set_xlabel("Hours in a year")
    ax.set_ylabel("kW to solar system (+) and to grid (-)")
    ax.set_title("Dcurves for link between grid and electricity for " + model )
    cbar = fig.colorbar(plt.cm.ScalarMappable(norm = norm, cmap = cmap), label = "Average gas load (kWh)")

    tls = cbar.ax.get_yticks()
    tls = [tl * 10000 for tl in tls ]
    cbar.set_ticklabels(tls)
    # ax.legend()
    prespath = "Presentations/" + presentationdate + "/"  + model +  "/gridelec_dcurvs_oldcost"

    plt.savefig(prespath + '.pdf')
    plt.savefig(prespath + '.png', dpi = 500)

    plt.show()


