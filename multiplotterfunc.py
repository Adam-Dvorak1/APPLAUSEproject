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
import importlib
import matplotlib.ticker as mtick
import helpers
importlib.reload(helpers)
from helpers import annual_cost, add_costreq_column, mod_solar_cost



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

labeldict = {'Highest price': "Highest price", '2022 median': '2022 median', '2021 median': '2021 median', 'H2 Electrolysis': 'H2 electrolysis', 'High to low voltage': 'grid connection', 'methanogens': 'methanation unit', 'Solar PV': 'solar electricity', 'battery': 'battery', 'H2 store': 'H2 store', 'grid elec total cost': 'electricity exported to grid', 'grid elec total income': 'income electricity \nimported from grid'}

#---------<<Other  dicts>------------------

color_dict = {"battery": '#9467bd', "battery charger":'#1f77b4', "methanogens": '#2ca02c', "Solar PV": '#ff7f0e',
"H2 Electrolysis": '#d62728', "grid elec total cost": '#7f7f7f', "grid elec total income": '#e377c2', "H2 store": '#43aaa0', 
"Onshore wind": '#ADD8E6', 'High to low voltage':'#260d29'}



#%%

####################################################################
################     SINGLE DATA POINT PLOTS      ##################
####################################################################
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











#%%

####################################################################
#################      LCOE AND INCOME DATA      ###################
####################################################################



def find_net_income_pass(path):
    '''This function is the same as find_net_income() except it passes an ax on to another function
    5 April 2023
    
    Earlier, we have modified this equation to make it so that 
    
    20 April 2023
    We are separating this plot from the four scenarios plot, so '''

    costdf = pd.read_csv(path, index_col = 0)

    mindf = pd.read_csv("results/csvs/costs/11_04_2023_mindf_default_costs.csv", index_col=0)

    gasload = 10000

    o = path.split("_")

    experiment = "megen_cost"

    presentation = 'May3pres CORC'

    # If any of the values of the column are not 0, keep them. 
    # Gets rid of generators/links etc with no cost
    costdf = costdf.loc[:,  (costdf != 0).any(axis=0)]



    # To find the net income, add up all of the total income and expenses. Costs are positive
    # and income is negative. Then, multiply by -1 to get the positive balance if you made money 
    # This skips over Gas Load, methanogen capital cost, and electrolyzer capital cost. If 'year'
    # is in the columns, it also skips over that

    costdf['Net income'] = costdf[costdf.columns[5:]].sum(axis = 1) * -1 #From "Battery charger" and on

    print(mindf.columns[4:])
    mindf['Net income'] = mindf[mindf.columns[5:]].sum(axis = 1) * -1 #Before we did not care about the electrolyzer capital cost. If we change the mindf, we will need to change this as well. 
    # 11 April: Now we have changed the mindf because of the added grid cost

    # How much can you expect to make with 0 gas load--ie, the solar system and the
    # battery is financing itself for the grid
    sys_income = mindf['Net income'].values[0]

    # Making it orderly for my view




    costdf = costdf.sort_values(['Gas Load', 'methanogen capital cost'])

    # Now the 'cost diff' column is how much money is being lost--it is the cost of the case
    # with the methanogen, minus the revenue of the case with no gas demand. This only makes
    # sense for the case with high gas load
    costdf['cost diff']= costdf['Net income'] - sys_income 
   
    #Finding cost diff per MW per hour
    costdf['cost diff'] = costdf['cost diff']/8760*1000/gasload * -1 #10000 kW or 10 MW




    mediancost = costdf['methanogen capital cost'].median()

    if experiment == "megen_cost":
        costdf['methanogen capital cost'] = costdf['methanogen capital cost']/mediancost
        costdf.index = costdf["methanogen capital cost"].round(1)
        costdf.index

    alldf = costdf.copy()
    if 'electrolyzer' in o:
        costdf = costdf.loc[costdf['electrolyzer capital cost'] == costdf['electrolyzer capital cost'].median()]
    ############################################
    fig, ax = plt.subplots()
    costdf['cost diff'].plot(kind = "bar", ax = ax)



    



    ax.set_title("Break-even gas price", fontsize = 20)
    
    ax.axhline(118, label = "Highest price", color = "#b03060")
    ax.axhline (25, label = "2022 median", color = "#21cc89")
    ax.axhline (14, label = "2021 median", color = "#00a8e1")

    ticks = [tick for tick in ax.get_xticklabels()]

    x_label_dict = dict([(x.get_text(), x.get_position()[0] ) for x in ticks])

    for val in alldf['methanogen capital cost'].unique():
        highincome = alldf.loc[(alldf['methanogen capital cost'] == val) & (alldf['electrolyzer capital cost'] == alldf['electrolyzer capital cost'].max())]["cost diff"].values[0]
        lowincome = alldf.loc[(alldf['methanogen capital cost'] == val) & (alldf['electrolyzer capital cost'] == alldf['electrolyzer capital cost'].min())]["cost diff"].values[0]
        val = round(val, 1)
        x_coord = x_label_dict[str(val)]
        ax.vlines(x  = x_coord, ymin = lowincome, ymax = highincome, color = 'k')

    ax.set_ylim(0, 145)
    ax.tick_params(axis='both', which='major', labelsize=14)
    ax.tick_params(axis='x', rotation=45)
    a = ['0x', '0.2x', '0.4x', '0.6x','0.8x', '1.0x', '1.2x', '1.4x','1.6x', '1.8x', '2.0x']
    ax.set_xticklabels(a)
    ax.set_xlabel("Methanation unit capacity cost (relative to default)", fontsize = 14)
    ax.set_ylabel('Dollars per MWh methane', fontsize = 14)
    fig.subplots_adjust(bottom=0.2)
    # plt.show()
    # plt.close('all')

    fig.savefig('Presentations/' + presentation + '/breakeven_gas.pdf')
    fig.savefig('Presentations/' + presentation + '/breakeven_gas.png', dpi = 500)


def find_net_income_pass_Spain(path):
    '''This function is the same as find_net_income() except it passes an ax on to another function
    5 April 2023
    
    Earlier, we have modified this equation to make it so that 
    
    20 April 2023
    We are separating this plot from the four scenarios plot, so 
    21 April, 2023
    This is being modified for the spain dfs'''

    costdf = pd.read_csv(path, index_col = 0)

    mindf = pd.read_csv("results/csvs/costs/19_04_2023_Spain_mindf.csv", index_col=0)

    gasload = 10000

    o = path.split("_")

    experiment = "megen_cost"

    presentation = 'May3pres CORC'

    # If any of the values of the column are not 0, keep them. 
    # Gets rid of generators/links etc with no cost
    costdf = costdf.loc[:,  (costdf != 0).any(axis=0)]



    # To find the net income, add up all of the total income and expenses. Costs are positive
    # and income is negative. Then, multiply by -1 to get the positive balance if you made money 
    # This skips over Gas Load, methanogen capital cost, and electrolyzer capital cost. If 'year'
    # is in the columns, it also skips over that

    costdf['Net income'] = costdf[costdf.columns[5:]].sum(axis = 1) * -1 #From "Battery charger" and on

    mindf['Net income'] = mindf[mindf.columns[4:]].sum(axis = 1) * -1 #Before we did not care about the electrolyzer capital cost. If we change the mindf, we will need to change this as well. 
    # 11 April: Now we have changed the mindf because of the added grid cost

    # How much can you expect to make with 0 gas load--ie, the solar system and the
    # battery is financing itself for the grid
    sys_income = mindf['Net income'].values[0]

    # Making it orderly for my view




    costdf = costdf.sort_values(['Gas Load', 'methanogen capital cost'])

    # Now the 'cost diff' column is how much money is being lost--it is the cost of the case
    # with the methanogen, minus the revenue of the case with no gas demand. This only makes
    # sense for the case with high gas load
    costdf['cost diff']= costdf['Net income'] - sys_income 
   
    #Finding cost diff per MW per hour
    costdf['cost diff'] = costdf['cost diff']/8760*1000/gasload * -1 #10000 kW or 10 MW




    mediancost = costdf['methanogen capital cost'].median()

    if experiment == "megen_cost":
        costdf['methanogen capital cost'] = costdf['methanogen capital cost']/mediancost
        costdf.index = costdf["methanogen capital cost"].round(1)
        costdf.index

    alldf = costdf.copy()
    if 'electrolyzer' in o:
        costdf = costdf.loc[costdf['electrolyzer capital cost'] == costdf['electrolyzer capital cost'].median()]
    ############################################
    fig, ax = plt.subplots()
    costdf['cost diff'].plot(kind = "bar", ax = ax)


    # ax.set_ylabel ("Required gas cost (Eur/MWh)")
    ax.set_xlabel("")
    



    # ax.set_title("Break-even gas price--Spain", fontsize = 20)
    
    #ax.axhline(362, label = "Highest price", color = "C1")
    ax.axhline (60, label = "2022 July 1", color = "#21cc89")
    ax.axhline (10, label = "2021 July 1", color = "#00a8e1")

    ticks = [tick for tick in ax.get_xticklabels()]

    x_label_dict = dict([(x.get_text(), x.get_position()[0] ) for x in ticks])

    for val in alldf['methanogen capital cost'].unique():
        highincome = alldf.loc[(alldf['methanogen capital cost'] == val) & (alldf['electrolyzer capital cost'] == alldf['electrolyzer capital cost'].max())]["cost diff"].values[0]
        lowincome = alldf.loc[(alldf['methanogen capital cost'] == val) & (alldf['electrolyzer capital cost'] == alldf['electrolyzer capital cost'].min())]["cost diff"].values[0]
        val = round(val, 1)
        x_coord = x_label_dict[str(val)]
        ax.vlines(x  = x_coord, ymin = lowincome, ymax = highincome, color = 'k')


    ax.tick_params(axis='both', which='major', labelsize=14)
    ax.tick_params(axis='x', rotation=45)
    a = ['0x', '0.2x', '0.4x', '0.6x','0.8x', '1.0x', '1.2x', '1.4x','1.6x', '1.8x', '2.0x']
    ax.set_xticklabels(a)
    ax.set_xlabel("Methanation unit capacity cost (relative to default)", fontsize = 14)
    ax.set_ylabel('Dollars per MWh methane', fontsize = 14)
    box = ax.get_position()
    # ax.set_position([box.x0, box.y0, box.width * 0.9, box.height])
    fig.subplots_adjust( top = 0.9, bottom=0.2)
    fig.legend(loc='upper center', ncol = 3)
    # plt.tight_layout()
    

    fig.savefig('Presentations/' + presentation + '/breakeven_gas_Spain.pdf')
    fig.savefig('Presentations/' + presentation + '/breakeven_gas_Spain.png', dpi = 500)
    # plt.show()




def plot_cost_any(path, ax): #change back to (path, ax)
    '''
    9 Feb 2023
    The purpose of this function is to be able to plot cost_any plots side by side
    '''
    costdf = pd.read_csv(path, index_col = 0)

    val = 10000

    o = path.replace('.', ' ').replace('_', ' ').split() #.split() splits by space

    if 'justgrid' in o:
        experiment = "Just Grid"
    elif "justsolar" in o:
        experiment = "Just Solar"
    elif 'justwind' in o:
        experiment = "Just Wind"
    elif 'gridwind' in o:
        experiment = 'Full system with wind'
    elif 'mindf' in o:
        experiment = 'Full system with no gas'
    else:
        experiment = "Full system with solar"



    costdf = costdf.loc[:,  (costdf != 0).any(axis=0)]#If any of the values of the column are not 0, keep them. Gets rid of generators/links etc with no cost

    if 'battery charger' in costdf.columns:
        costdf['battery'] = costdf['battery'] + costdf['battery charger'] #This is new
        costdf = costdf.drop(['battery charger'], axis = 1)


    #only positive--so no "income"
    # if experiment != "Full system with solar":
    #     costdf = costdf.loc[:,  (costdf > 0).any(axis=0)]#If any of the values of the column are not negative, keep them. Gets rid of the "income"


    #costdf = costdf.loc[costdf["Gas Load"] == val]
    if 'electrolyzer' in o:
        costdf = costdf.loc[costdf['electrolyzer capital cost'] == costdf['electrolyzer capital cost'].median()]
    elif 'year' in o:
        costdf = costdf.loc[costdf['year'] == 2019]
    elif 'grid' in o:
        costdf = costdf.loc[costdf['methanogen capital cost'] == 120]
        costdf = costdf.sort_values(by = '')
    else:
        costdf = costdf.loc[costdf['electrolyzer capital cost'] == costdf['electrolyzer capital cost'].median()]
        
    # print(costdf)
    mediancost = costdf['methanogen capital cost'].median()
    costdf['methanogen capital cost'] = costdf['methanogen capital cost']/mediancost
    
    #print(costdf)
    costdf = costdf.sort_values(by ="methanogen capital cost")
    costdf.index = costdf["methanogen capital cost"].round(1)
    costdf = costdf/val/8760*1000 #price per MWh

    

    if 'mindf' in o:# 21 April not entirely sure why costdf for min has one less column but cest la vie
        colors = [color_dict[colname] for colname in costdf.columns.get_level_values(0)[4:]]
        costdf[costdf.columns[4:]].plot( kind = "bar", stacked = True, color = colors, ax = ax)
    else:
        colors = [color_dict[colname] for colname in costdf.columns.get_level_values(0)[5:]]
        costdf[costdf.columns[5:]].plot( kind = "bar", stacked = True, color = colors, ax = ax)


    #comment out these two lines
    # ax.set_ylabel("LCOE (Dollars/MWh_energy)")
    # ax.set_xlabel("Methanogen cost (Dollars/kWh)")
    

    ax.set_title( experiment, fontsize = 20)
    # ax.axhline(340, label = '26-Aug-22 price (high)', color = "C0")
    # ax.axhline(118, label = "Highest price", color = "#b03060")
    # ax.axhline (25, label = "2022 median", color = "#21cc89")
    # ax.axhline (14, label = "2021 median", color = "#00a8e1")
    ax.set_xlabel('')
    #ax.legend()


    # fig.savefig('Presentations/' + presentation + '/' + experiment + '.pdf')
    #plt.show()#delete
    ax.get_legend().remove() #uncomment



def plot_grid_restriction():
    '''23 March 2023
    This function takes a run that analyzes the effect of grid restriction. Using the normal sabatier price, 
    it plots on the x axis the variation in the grid restriction'''
    presentation = 'March24pres'
    path = 'results/csvs/costs/24_03_2023_grid_invert_megen_median_gridsolar_dispatch_uppers.csv'
    costdf = pd.read_csv(path, index_col = 0)

    val = 10000

    o = path.replace('.', ' ').replace('_', ' ').split() #.split() splits by space

    if 'justgrid' in o:
        experiment = "Just Grid"
    elif "justsolar" in o:
        experiment = "Just Solar"
    elif 'justwind' in o:
        experiment = "Just Wind"
    elif 'gridwind' in o:
        experiment = 'Full system with wind'
    else:
        experiment = "Full system with solar"



    costdf = costdf.loc[:,  (costdf != 0).any(axis=0)]#If any of the values of the column are not 0, keep them. Gets rid of generators/links etc with no cost

    costdf = costdf.loc[costdf['methanogen capital cost'] == 120]
    costdf = costdf.sort_values(by = 'grid link max size')
    costdf.index = costdf['grid link max size'] /14667

    # print(costdf)

    cols = costdf.columns.to_list()
    cols = cols [0:5] + [cols[-1]] + cols [5:-1] # bc solar, delete for data frames that already have solar in the right position
 
    costdf = costdf[cols]


    costdf = costdf/val/8760*1000 #price per MWh


    colors = [color_dict[colname] for colname in costdf.columns.get_level_values(0)[5:]]

    fig, ax = plt.subplots()
    costdf[costdf.columns[5:]].plot( kind = "bar", stacked = True, color = colors, ax = ax) #, ax = ax

    for label in ax.get_xticklabels():
        label.set_rotation(0)
        
        
    ax.set_xlabel('Multiplier to average')

    #comment out these two lines
    # ax.set_ylabel("LCOE (Dollars/MWh_energy)")
    # ax.set_xlabel("Methanogen cost (Dollars/kWh)")
    ax.set_title( experiment, fontsize = 20)
    # ax.axhline(340, label = '26-Aug-22 price (high)', color = "C0")
    ax.axhline(118, label = "Highest price", color = "C1")
    ax.axhline (25, label = "2022 median", color = "C2")
    ax.axhline (14, label = "2021 median", color = "C3")
  
    # ax.legend()


    #fig.savefig('Presentations/' + presentation + '/' + experiment + 'gridrestriction.pdf')
    plt.show()#delete
    plt.close('all')
    ax.get_legend().remove() #uncomment




def four_cost_plot():
    
    presentation = 'April21pres'
    fig, ax = plt.subplots(2,2,figsize=(10,9), sharex=True)
    axs = ax.flatten()

    

    justgrid = 'results/csvs/costs/05_04_2023_megen_justgrid_zero_double_sweep.csv'
    justsolar = 'results/csvs/costs/11_04_2023_megen_justsolar_dispatch_zero_double_sweep.csv'
    gridsolar = 'results/csvs/costs/11_04_2023_electrolyzer_megen_gridsolar_dispatch_zero_double_sweep.csv'
    mindf = 'results/csvs/costs/11_04_2023_mindf_default_costs.csv'
    plot_cost_any(justsolar, axs[0])
    plot_cost_any(justgrid, axs[1])
    plot_cost_any(gridsolar, axs[2])
    plot_cost_any(mindf, axs[3])


    for ax in axs:
        ax.tick_params(axis='both', which='major', labelsize=14)
        ax.tick_params(axis='x', rotation=45)
        a = ['0x', '0.2x', '0.4x', '0.6x','0.8x', '1.0x', '1.2x', '1.4x','1.6x', '1.8x', '2.0x']
        # a = ax.get_xticks()
        # a = [str(entry) + 'x' for entry in a]
        ax.set_xticklabels(a)

        #ax.xaxis.set_major_formatter(mtick.PercentFormatter(xmax=5))#for some reason this percent formatter takes the position of the 

    ymin, ymax = axs[0].get_ylim()
    axs[1].set_ylim(bottom = ymin)
    ymin, ymax = axs[2].get_ylim()
    axs[3].set_ylim(ymin, ymax)
    
    fig.supylabel("Dollars per MWh gas", fontsize = 16)
    fig.supxlabel("Methanation cost relative to default", fontsize = 16)
    

    handles, labels = axs[2].get_legend_handles_labels()
    fig.legend(handles, labels, ncol = 3, loc = 'upper center', fontsize = 12)
    fig.subplots_adjust(top = 0.84, bottom = 0.15)



        
    fig.savefig('Presentations/' + presentation + '/megencosts_income.pdf')
    fig.savefig('Presentations/' + presentation + '/megencosts_income.png', dpi = 500)
    # plt.show()

def four_cost_plot_pres():
    
    presentation = 'May3pres CORC'
    fig, ax = plt.subplots(2,2,figsize=(10,9), sharex=True)
    axs = ax.flatten()

    

    justgrid = 'results/csvs/costs/05_04_2023_megen_justgrid_zero_double_sweep.csv'
    justsolar = 'results/csvs/costs/11_04_2023_megen_justsolar_dispatch_zero_double_sweep.csv' #Justsolar is no longer dispatch
    gridsolar = 'results/csvs/costs/11_04_2023_electrolyzer_megen_gridsolar_dispatch_zero_double_sweep.csv'
    mindf = 'results/csvs/costs/11_04_2023_mindf_default_costs.csv'
    plot_cost_any(justsolar, axs[0])
    plot_cost_any(justgrid, axs[1])
    plot_cost_any(gridsolar, axs[2])
    plot_cost_any(mindf, axs[3])


    for ax in axs:
        ax.tick_params(axis='both', which='major', labelsize=14)
        ax.tick_params(axis='x', rotation=45)
        a = ['0x', '0.2x', '0.4x', '0.6x','0.8x', '1.0x', '1.2x', '1.4x','1.6x', '1.8x', '2.0x']
        # a = ax.get_xticks()
        # a = [str(entry) + 'x' for entry in a]
        ax.set_xticklabels(a)

        #ax.xaxis.set_major_formatter(mtick.PercentFormatter(xmax=5))#for some reason this percent formatter takes the position of the 

    ymin, ymax = axs[0].get_ylim()
    axs[1].set_ylim(bottom = ymin)
    ymin, ymax = axs[2].get_ylim()
    axs[3].set_ylim(ymin, ymax)
    
    fig.supylabel("Dollars per MWh methane", fontsize = 16)
    fig.supxlabel("Methanation unit capacity cost (relative to default)", fontsize = 16)
    

    handles, labels = axs[2].get_legend_handles_labels()
    labels = [labeldict[label] for label in labels]
    #print(labels)
    fig.legend(handles, labels, ncol = 3, loc = 'upper center', fontsize = 12)
    fig.subplots_adjust(top = 0.84, bottom = 0.15)



        
    fig.savefig('Presentations/' + presentation + '/megencosts_income.pdf')
    fig.savefig('Presentations/' + presentation + '/megencosts_income.png', dpi = 500)
    # plt.show()




def four_cost_plot_Spain():
    
    presentation = 'May3pres CORC'
    fig, ax = plt.subplots(2,2,figsize=(10,9), sharex=True)
    axs = ax.flatten()

    

    justgrid = 'results/csvs/costs/21_04_2023_Spain_justgrid_megen_sweep.csv'
    justsolar = 'results/csvs/costs/21_04_2023_Spain_justsolar_megen_sweep.csv'
    gridsolar = 'results/csvs/costs/19_04_2023_Spain_electrolyzer_gridsolar_dispatch_zero_double_sweep.csv'
    mindf = 'results/csvs/costs/19_04_2023_Spain_mindf.csv'
    plot_cost_any(justsolar, axs[0])
    plot_cost_any(justgrid, axs[1])
    plot_cost_any(gridsolar, axs[2])
    plot_cost_any(mindf, axs[3])


    for ax in axs:
        ax.tick_params(axis='both', which='major', labelsize=14)
        ax.tick_params(axis='x', rotation=45)
        a = ['0x', '0.2x', '0.4x', '0.6x','0.8x', '1.0x', '1.2x', '1.4x','1.6x', '1.8x', '2.0x']
        # a = ax.get_xticks()
        # a = [str(entry) + 'x' for entry in a]
        ax.set_xticklabels(a)

        #ax.xaxis.set_major_formatter(mtick.PercentFormatter(xmax=5))#for some reason this percent formatter takes the position of the 

    ymin, ymax = axs[0].get_ylim()
    axs[1].set_ylim(bottom = ymin)
    ymin, ymax = axs[2].get_ylim()
    axs[3].set_ylim(top = ymax)
    ymin, ymax = axs[3].get_ylim()
    axs[2].set_ylim(bottom = ymin)

    
    fig.supylabel("Dollars per MWh gas", fontsize = 16)
    fig.supxlabel("Methanation cost relative to default", fontsize = 16)
    

    handles, labels = axs[2].get_legend_handles_labels()
    fig.legend(handles, labels, ncol = 3, loc = 'upper center', fontsize = 12)
    fig.subplots_adjust(top = 0.84, bottom = 0.15)



        
    fig.savefig('Presentations/' + presentation + '/Spainmegencosts_income.pdf')
    fig.savefig('Presentations/' + presentation + '/Spainmegencosts_income.png', dpi = 500)
    # plt.show()


def compare_cost_bars():
    '''
    11 April 2023
    This function will be modified in the following ways:
    - The mindf will be updated in accordance with the new price of the grid connection
    - All the csvs are otherwise updated


    23 March 2023
    This function will take in various csvs to show the following variations
    - in methanogen price (1/4 to 4x default)
    - in electrolyzer price (1/4 to 4x default)
    - in year (2017 to 2020)
    - in grid restriction (1/10 to 2x average)
    - in solar price (low NREL to high NREL) (planned)
    
    It takes in 3 csvs:
    electrolyzer csv--for methanogen price, electrolyzer price, and solar variation price. Note, this is only true for a dispatch model, as we know exactly how much 
    year csv-- for year
    grid csv-- for grid
    
    It then finds the min and max required gas price according to each of the variation. 
    
    Finally, it plots the min and max on a mirrored vertical bar plot as a percent variation of the middle'''
    presentation = "March24pres"
    methanogencost = 120
    gasload = 10000

    elecdf = pd.read_csv('results/csvs/costs/11_04_2023_electrolyzer_megen_gridsolar_dispatch_zero_double_sweep.csv', index_col= 0)
    yeardf = pd.read_csv('results/csvs/costs/11_04_2023_year_gridsolar_dispatch.csv', index_col=0)
    gi_costdf = pd.read_csv('results/csvs/costs/12_04_2023_GIcost_gridsolar_dispatch_zero_double_sweep.csv', index_col = 0) #g

    elecdf_hisolvals = elecdf.copy()
    elecdf_losolvals = elecdf.copy()


    elecdf_hisolvals = mod_solar_cost(elecdf_hisolvals, 'high')
    elecdf_losolvals = mod_solar_cost(elecdf_losolvals, 'low')

    mindf = pd.read_csv("results/csvs/costs/11_04_2023_mindf_default_costs.csv", index_col=0)
    mindf['Net income'] = mindf[mindf.columns[5:]].sum(axis = 1) * -1 #Before we did not care about the electrolyzer capital cost. If we change the mindf, we will need to change this as well. 
    sys_income = mindf['Net income'].values[0]

    elecdf = add_costreq_column(elecdf, gasload, sys_income)
    elecdf_hisolvals = add_costreq_column(elecdf_hisolvals, gasload, sys_income)
    elecdf_losolvals = add_costreq_column(elecdf_losolvals, gasload, sys_income)
    yeardf = add_costreq_column(yeardf, gasload, sys_income)
    #print(elecdf.loc[elecdf['methanogen capital cost'] == 120])
    gi_costdf = add_costreq_column(gi_costdf, gasload, sys_income)


    
    basecostreq = elecdf.loc[(elecdf['methanogen capital cost'] == elecdf['methanogen capital cost'].median()) & (elecdf['electrolyzer capital cost'] == elecdf['electrolyzer capital cost'].median())]['cost diff'].values[0]

    # print(basecostreq)
    elecdf = elecdf.sort_values(by ="methanogen capital cost")
    megenpr = elecdf['methanogen capital cost'].unique()
    megenpr = [x for x in megenpr]
    megenlow = megenpr[3]
    megenhi = megenpr[7]
    methanation_high = elecdf.loc[(elecdf['methanogen capital cost'] == megenhi) & (elecdf['electrolyzer capital cost'] == elecdf['electrolyzer capital cost'].median())]['cost diff'].values[0]
    methanation_high = methanation_high/basecostreq - 1
    methanation_low = elecdf.loc[(elecdf['methanogen capital cost'] == megenlow) & (elecdf['electrolyzer capital cost'] == elecdf['electrolyzer capital cost'].median())]['cost diff'].values[0]
    methanation_low = methanation_low/basecostreq-1

    elecdf = elecdf.sort_values(by ="electrolyzer capital cost")
    elecpr = elecdf['electrolyzer capital cost'].unique()
    elecpr = [x for x in elecpr]
    eleclow = elecpr[3]
    elechi = elecpr[7]

    electrolyzer_high = elecdf.loc[(elecdf['methanogen capital cost'] == elecdf['methanogen capital cost'].median()) & (elecdf['electrolyzer capital cost'] == elechi)]['cost diff'].values[0]
    electrolyzer_high = electrolyzer_high/basecostreq-1
    electrolyzer_low = elecdf.loc[(elecdf['methanogen capital cost'] == elecdf['methanogen capital cost'].median()) & (elecdf['electrolyzer capital cost'] == eleclow)]['cost diff'].values[0]
    electrolyzer_low = electrolyzer_low/basecostreq-1


    meth_elec_high = elecdf.loc[(elecdf['methanogen capital cost'] == megenhi) & (elecdf['electrolyzer capital cost'] == elechi)]['cost diff'].values[0]
    meth_elec_high = meth_elec_high/basecostreq - 1
    meth_elec_low = elecdf.loc[(elecdf['methanogen capital cost'] == megenlow) & (elecdf['electrolyzer capital cost'] == eleclow)]['cost diff'].values[0]
    meth_elec_low = meth_elec_low/basecostreq - 1

    solarhigh = elecdf_hisolvals.loc[(elecdf_hisolvals['methanogen capital cost'] == elecdf_hisolvals['methanogen capital cost'].median()) & (elecdf_hisolvals['electrolyzer capital cost'] == elecdf_hisolvals['electrolyzer capital cost'].median())]['cost diff'].values[0]
    solarhigh = solarhigh/basecostreq - 1
    solarlow = elecdf_losolvals.loc[(elecdf_losolvals['methanogen capital cost'] == elecdf_losolvals['methanogen capital cost'].median()) & (elecdf_losolvals['electrolyzer capital cost'] == elecdf_losolvals['electrolyzer capital cost'].median())]['cost diff'].values[0]
    solarlow = solarlow/basecostreq - 1    



    val17 = yeardf.loc[yeardf['year'] == 2017]['cost diff'].values[0]
    val17 = val17/basecostreq-1

    val18 = yeardf.loc[yeardf['year'] == 2018]['cost diff'].values[0]
    val18 = val18/basecostreq-1

    val20 = yeardf.loc[yeardf['year'] == 2020]['cost diff'].values[0]
    val20 = val20/basecostreq-1

    # year_high = yeardf[yeardf['year'] != 2018]['cost diff'].max() #Because 2018 is weird #I think I fixed 2018
    year_high = yeardf['cost diff'].max()
    year_high = year_high/basecostreq-1
    year_low = yeardf['cost diff'].min()
    year_low = year_low/basecostreq-1

    gi_costdf = gi_costdf.sort_values(by = 'inverter capital cost')
    gipr = gi_costdf['inverter capital cost'].unique()
    gipr = [x for x in gipr]
    gilo = gipr[3]
    gihi = gipr[7]

    gi_high = gi_costdf.loc[gi_costdf['inverter capital cost']== gihi]['cost diff'].values[0]
    gi_high = gi_high/basecostreq-1
    gi_low = gi_costdf.loc[gi_costdf['inverter capital cost']== gilo]['cost diff'].values[0]
    gi_low = gi_low/basecostreq-1
    # meth_elec_high = meth_elec_high/basecostreq - 1



    # year_high = 
    fig, ax = plt.subplots()
    factorlist = ['methanation cost\n120 Eur/kW/yr[+/- 40%]', 'electrolyzer cost\n146 Eur/kW/yr[+/- 40%]', 'meth and elec cost\n both [+/- 40%]', 'solar cost \n high/low NREL', 'inverter cost\n34 Eur/kW/yr[+/- 40%]', 'year\n2019 [2020, 2017]']
    # highs = [methanation_high, electrolyzer_high, meth_elec_high, year_high, grid_high]
    # lows = [methanation_low, electrolyzer_low, meth_elec_low, year_low]
    highs = [methanation_high, electrolyzer_high, meth_elec_high, solarhigh, gi_high, year_high]
    highs = [x * 100 for x in highs]
    lows = [methanation_low, electrolyzer_low, meth_elec_low, solarlow, gi_low, year_low]
    lows = [x * 100 for x in lows]

    highbars = ax.barh(factorlist, highs, height= 0.4, color = 'C0')

    ax.bar_label(highbars, fmt = '%.0f%%', label_type='center', color = 'white')
    lowbars = ax.barh(factorlist, lows, height = 0.4, color = 'C1')
    ax.bar_label(lowbars, fmt = '%.0f%%', label_type='center')
    ax.invert_yaxis()
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(xmax = 100))
    ax.spines[['right', 'top', 'left']].set_visible(False)
    ax.set_xlabel ("Percent change in methanation cost requirement")
    plt.tight_layout()
    # plt.savefig('paper/Figures/RealFigures/compareChangeBars.pdf')
    plt.show()
    plt.close('all')


    #Finding the default price

##################################################################
########################### HEAT MAPS ############################
##################################################################


def capacity(sumcsvpath, twovar):
    '''
    26 April 2023
    
    This function is similar to cf_sensitivity, except that it makes a heatmap based on the size of
    the 'battery size' or 'H2 store size. It takes a summary csv. Twovar can either be 'electrolyzer cost' or 'grid connection cost'
    
    colormaps: magma, viridis'''
    df = pd.read_csv(sumcsvpath, index_col=0)

    df['methanation cost'] = df['megen cost']
    df['methanation cost'] = df['methanation cost'] / df['methanation cost'].median()
    df[twovar] = df[twovar]/ df[twovar].median()

    df = df.round(2)

    presentation = 'Maypres'

    var = "battery size"
    # var = 'H2 store size'
    df = df.pivot(index = 'methanation cost', columns = twovar, values= var)
    print(df)
    df.sort_index(level = 0, ascending = False, inplace = True)

    fig, ax= plt.subplots()
    sns.heatmap(df, cmap = 'viridis', ax = ax)
    ax.tick_params(axis='both', which='major', labelsize=14)
    ax.tick_params(axis = 'y', rotation = 0)
    ax.tick_params(axis='x', rotation=45)

    fig.subplots_adjust(bottom = 0.15)
    ax.set_title(var + ' (kWh)')

    # plt.show()
    # plt.close('all')
    plt.savefig('Presentations/' + presentation + '/_'+ twovar + "_" + var + '.pdf')



def cf_sensitivity():
    '''20 April 2023
    This function uses a csv that takes into account all of the different biomethane time series, sees 
    what percent each of them is varying, and so forth
    
    Twovar can be 'electrolyzer cost' or 'grid connection cost
    '''
    df = pd.read_csv('results/csvs/cfdata/allcfs_12_04_2023_GIcost_gridsolar_dispatch_zero_double_sweep.csv', index_col = 0)

    #var = 'constant biogas'
    #var = 'constant biogas +/-1%'
    # var = 'constant biogas +/-10%'
    # var = 'biogas capacity factor'
    var = 'grid capacity factor'
    # var = 'local to grid capacity factor'
    # var = 'grid to local capacity factor'
    # var = 'electrolyzer capacity factor'
    # var = 'methanation capacity factor'


    twovar = 'grid connection cost'
    presentation = 'Maypres'
    df['methanation cost'] = df['methanation cost'] / df['methanation cost'].median()
    df[twovar] = df[twovar]/ df[twovar].median()
    df = df.round(2)


    df = df.pivot(index = 'methanation cost', columns = twovar, values= var)
    df.sort_index(level = 0, ascending = False, inplace = True)

    fig, ax = plt.subplots()
    sns.heatmap(df, cmap = 'viridis', annot = True, ax = ax)
    ax.tick_params(axis='both', which='major', labelsize=14)
    ax.tick_params(axis = 'y', rotation = 0)
    ax.tick_params(axis='x', rotation=45)

    fig.subplots_adjust(bottom = 0.15)
    ax.set_title(var)

    # plt.show()
    # plt.close('all')
    #var = 'constant biogas err10'
    plt.savefig('Presentations/' + presentation + '/_'+ twovar + "_" + var + '.pdf')


##################################################################
########################TIME SERIES #########################
##################################################################

def plot_elec_ts():
    df = pd.read_csv('results/csvs/alldata/11_04_2023_year_2019_gridsolar_dispatch_onerun.csv')
    fig, ax = plt.subplots()
    df[24:192].plot(x = 'snapshot', y = ['solar ts', 'grid to electricity link ts', 'battery store ts'], ax = ax)
    fig.legend()
    # fig, ax = plt.subplots()
    # ax.plot(df['grid to electricity link ts'][4020:4044])
    # ax.plot(df[''])
    plt.savefig("Presentations/April21pres/electimeseriesJan.pdf")

def plot_grid_prices():
    df = pd.read_csv

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
    # o = path.split("_")
    # if "nosolar" in o:
    #     model = "nosolar"
    # else:
    #     model = "gridsolar"


    presentationdate = "February24pres"



    # pairs = [x for x in pairs if x[1] == minimum or x[1] == maximum]

    fig, ax = plt.subplots()


    tempdf = df
    tempdf['grid to electricity link ts'] = tempdf['grid to electricity link ts'] /1000
    tempdf = tempdf.sort_values(by = ["grid to electricity link ts"], ascending = False)
    tempdf.index = range(8760)


    ax.plot(tempdf['grid to electricity link ts'])
    ax.hlines([x*14.7 for x in [0.1, 0.5, 0.75, 1, 1.25, 1.5, 2] ], 0, 8760, colors = ['C1', 'C2', "C3", "C4", "C5", "C6", "C7"])


    # fig.set_size_inches(11, 7)
    ax.set_xlabel("Hours in a year")
    ax.set_ylabel("MW to solar system")
    ax.set_title("Dcurves for link between grid and electricity for full model" )


    prespath = "Presentations/" + presentationdate + "/gridelec_dcurv"

    plt.savefig(prespath + '.pdf')
    # plt.savefig(prespath + '.png', dpi = 500)

    plt.show()


import os
pathiter = (os.path.join(root, filename)
    for root, _, filenames in os.walk('results/csvs/costs/archive')
    for filename in filenames
)

for path in pathiter:
    newname =  path.replace('nogrid', 'justsolar')
    if newname != path:
        os.rename(path,newname)
# %%
