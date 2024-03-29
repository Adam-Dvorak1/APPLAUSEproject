# '''The purpose of this file is to house the functions that I use to plot my results'''
# %%
import pypsa
import numpy as np
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.dates as mdates
from matplotlib.colors import LogNorm
from matplotlib import patheffects
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
import string
from helpers import return_income_df, prep_csv, annual_cost, add_costreq_column, mod_solar_cost



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

labeldict = {"Onshore wind": "Onshore wind", 'Highest price': "Highest price", '2022 median': '2022 median', '2021 median': '2021 median', 'H2 Electrolysis': 'H2 electrolysis', 'High to low voltage': 'grid connection', 'methanogens': 'methanation unit', 'Solar PV': 'solar electricity', 'battery': 'battery', 'H2 store': 'H2 store', 'grid elec total cost': 'electricity imported from grid', 'grid elec total income': 'income electricity \nexported to grid'}

#---------<<Other  dicts>------------------

color_dict = {"battery": '#9467bd', "battery charger":'#1f77b4', "methanogens": '#2ca02c', "Solar PV": '#ff7f0e',
"H2 Electrolysis": '#d62728', "grid elec total cost": '#7f7f7f', "grid elec total income": '#e377c2', "H2 store": '#43aaa0', 
"Onshore wind": '#2c7ef2', 'High to low voltage':'#260d29'}



#%%

####################################################################
################     SINGLE DATA POINT PLOTS      ##################
####################################################################
def plot_gridlinksize():
    '''
    5 July 2023
    This function takes in cost csvs from '''
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
    '''
    11 June 2023
     
    This function reads in a cost csv. It doesn't really 'pass' anymore.
    
    10 July 2023
    We change the  '''

    costdf = pd.read_csv(path, index_col = 0)

    #This is for solar
    mindf = pd.read_csv("results/csvs/costs/26_05_2023_megen_mindf.csv", index_col=0)

    #This is for wind

    # mindf = pd.read_csv("results/csvs/costs/15_06_2023_electrolyzer_wind_mindf.csv", index_col=0)


    o = path.split("_")

    experiment = "gas price"

    # presentation = 'May3pres CORC'

    # If any of the values of the column are not 0, keep them. 
    # Gets rid of generators/links etc with no cost
    costdf = costdf.loc[:,  (costdf != 0).any(axis=0)]



    # To find the net income, add up all of the total income and expenses. Costs are positive
    # and income is negative. Then, multiply by -1 to get the positive balance if you made money 
    # This skips over Gas Load, methanogen capital cost, and electrolyzer capital cost. If 'year'
    # is in the columns, it also skips over that

    costdf['Net income'] = costdf[costdf.columns[5:]].sum(axis = 1) * -1 #From "Battery charger" and on

    # print(costdf)
    # costdf.to_csv('withnetincome')
    # print(mindf.columns[4:])
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
    costdf['cost diff'] = costdf.apply(lambda row: row['cost diff']/8760*1000/row['Gas Load'] * -1, axis = 1) #10000 kW or 10 MW




    mediancost = costdf['methanogen capital cost'].median()

    if experiment == "megen_cost":
        costdf['methanogen capital cost'] = costdf['methanogen capital cost']/mediancost
        costdf.index = costdf["methanogen capital cost"].round(1)

    elif experiment== 'gas price':
        costdf['Gas Load'] = costdf['Gas Load']/10000
        costdf.index = costdf['Gas Load']



    alldf = costdf.copy()

    costdf = costdf.loc[costdf['electrolyzer capital cost'] == costdf['electrolyzer capital cost'].median()]

    ############################################
    fig, ax = plt.subplots()
    costdf['cost diff'].plot(kind = "bar", ax = ax)

    # print(costdf)



    



    # ax.set_title("Methane price", fontsize = 20)

    # ax.axhline(118, label = "Highest methane price", color = "#b03060")
    # ax.axhline (25, label = "2022 median price", color = "#21cc89")
    # ax.axhline (14, label = "2021 median price", color = "#00a8e1")


    # ax.axhline(118, label = "Highest price", color = "#b03060")
    # ax.text(0,122,r"$\bf{Highest\:methane\:price\:in\:CA}$", color  = 'r')
    # ax.axhline(138.5, label = "Highest price with carbon tax", linestyle = 'dashed', color = "#b03060")
    # ax.text(0,143,r"$\bf{Highest\:methane\:price\:in\:CA\:with\:carbon\:tax}$", color  = 'r')
    # ax.axhline (25, label = "2022 median", color = 'C1')
    # ax.text(0,29,r"$\bf{2022\:methane\:price\:in\:CA}$", color  = "C1")
    # ax.axhline(45.5, label = "Highest price with carbon tax", linestyle = 'dashed', color = "C1")
    # ax.text(0,50,r"$\bf{2022\:methane\:price\:in\:CA\:with\:carbon\:tax}$", color  = 'C1')

   

    ticks = [tick for tick in ax.get_xticklabels()]

    x_label_dict = dict([(x.get_text(), x.get_position()[0] ) for x in ticks])


    # minus20val = alldf['electrolyzer capital cost'].sort_values().unique()[3]
    # plus20val = alldf['electrolyzer capital cost'].sort_values().unique()[-3]
    # for val in alldf['methanogen capital cost'].unique():
    #     highincome = alldf.loc[(alldf['methanogen capital cost'] == val) & (alldf['electrolyzer capital cost'] == plus20val)]["cost diff"].values[0]
    #     lowincome = alldf.loc[(alldf['methanogen capital cost'] == val) & (alldf['electrolyzer capital cost'] == minus20val)]["cost diff"].values[0]
    #     val = round(val, 1)
    #     x_coord = x_label_dict[str(val)]
    #     ax.vlines(x  = x_coord, ymin = lowincome, ymax = highincome, color = 'k')

    # ax.set_ylim(0, 150)
    ax.tick_params(axis='both', which='major', labelsize=14)
    ax.tick_params(axis='x', rotation=0)
    # a = ['0x', '0.2x', '0.4x', '0.6x','0.8x', '1.0x', '1.2x', '1.4x','1.6x', '1.8x', '2.0x']
    a = ['0.1x', '1x', '10x']
    ax.set_xticklabels(a)
    # ax.set_xlabel("Methanation unit capacity cost (relative to default)", fontsize = 14)
    ax.set_xlabel("Gas load (relative to default)", fontsize = 14)
    ax.set_ylabel('Dollars per MWh methane', fontsize = 14)
    fig.subplots_adjust(bottom=0.2)
    # plt.show()
    # plt.close('all')

    # fig.savefig('paper/Figures/RealFigures/gasprice_wind.pdf')

    # fig.savefig('Presentations/' + presentation + '/breakeven_gas_comp.png', dpi = 500)

    fig.savefig('paper/Figures/RealFigures/supfigs/Gas_load_comp.pdf')
    fig.savefig('paper/Figures/RealFigures/supfigs/Gas_load_comp.png', dpi = 500)
    fig.savefig('paper/Figures/Screenshots/supfigs/Gas_load_comp.png', dpi = 100)


def find_net_income_pass_Spain(path):
    '''This function is the same as find_net_income() except it passes an ax on to another function
    5 April 2023
    
    Earlier, we have modified this equation to make it so that 
    
    20 April 2023
    We are separating this plot from the four scenarios plot, so 
    21 April, 2023
    This is being modified for the spain dfs'''
    costdf = pd.read_csv(path, index_col = 0)
    sns.set_theme()

    #This is for solar
    mindf = pd.read_csv("results/csvs/costs/23_06_2023_Spain_mindf.csv", index_col=0)

    #This is for wind

    # mindf = pd.read_csv("results/csvs/costs/15_06_2023_electrolyzer_wind_mindf.csv", index_col=0)

    gasload = 10000

    o = path.split("_")

    experiment = "megen_cost"

    # presentation = 'May3pres CORC'

    # If any of the values of the column are not 0, keep them. 
    # Gets rid of generators/links etc with no cost
    costdf = costdf.loc[:,  (costdf != 0).any(axis=0)]



    # To find the net income, add up all of the total income and expenses. Costs are positive
    # and income is negative. Then, multiply by -1 to get the positive balance if you made money 
    # This skips over Gas Load, methanogen capital cost, and electrolyzer capital cost. If 'year'
    # is in the columns, it also skips over that

    costdf['Net income'] = costdf[costdf.columns[5:]].sum(axis = 1) * -1 #From "Battery charger" and on

    # print(costdf)
    # costdf.to_csv('withnetincome')
    # print(mindf.columns[4:])
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

    costdf = costdf.loc[costdf['electrolyzer capital cost'] == costdf['electrolyzer capital cost'].median()]

    ############################################
    fig, (ax, ax2) = plt.subplots(2, 1, sharex = True)
    # fig, ax = plt.subplots()
    costdf['cost diff'].plot(kind = "bar", ax = ax)
    # costdf['cost diff'].plot(kind = 'bar', ax = ax2)

    # ax.set_title("Break-even gas price--Spain", fontsize = 20)
        
    ax.spines['bottom'].set_visible(False)
    ax2.spines['top'].set_visible(False)
    ax.xaxis.tick_top()
    ax.tick_params(labeltop=False)  # don't put tick labels at the top
    ax2.xaxis.tick_bottom()

    ax.axhline(370, label = "Highest price", color = "#b03060")
    ax.text(0,362,r"$\bf{Highest\:methane\:price\:in\:Spain}$", color  = 'r')
    ax.axhline(390, label = "Highest price with carbon tax", linestyle = 'dashed', color = "#b03060")
    ax.text(0,382,r"$\bf{Highest\:methane\:price\:in\:Spain\:with\:carbon\:tax}$", color  = 'r')
    ax.axhline (65, label = "2022 July 1 price", color = 'C1')
    ax.text(0,60,r"$\bf{2022\:methane\:price\:in\:Spain}$", color  = "C1")
    ax.axhline(85, label = "2022 July 1 price with carbon tax", linestyle = 'dashed', color = "C1")
    ax.text(0,80,r"$\bf{2022\:methane\:price\:in\:Spain\:with\:carbon\:tax}$", color  = 'C1')


    # ax.axhline (10, label = "2021 July 1", color = "#00a8e1")

    ticks = [tick for tick in ax.get_xticklabels()]

    x_label_dict = dict([(x.get_text(), x.get_position()[0] ) for x in ticks])


    # ax.set_ylim(0, 100)
    # ax2.set_ylim(300, 400)
    # minus20val = alldf['electrolyzer capital cost'].sort_values().unique()[3]
    # plus20val = alldf['electrolyzer capital cost'].sort_values().unique()[-3]
    # for val in alldf['methanogen capital cost'].unique():
    #     highincome = alldf.loc[(alldf['methanogen capital cost'] == val) & (alldf['electrolyzer capital cost'] == plus20val)]["cost diff"].values[0]
    #     lowincome = alldf.loc[(alldf['methanogen capital cost'] == val) & (alldf['electrolyzer capital cost'] == minus20val)]["cost diff"].values[0]
    #     val = round(val, 1)
    #     x_coord = x_label_dict[str(val)]
    #     ax.vlines(x  = x_coord, ymin = lowincome, ymax = highincome, color = 'k')
        # ax2.vlines(x  = x_coord, ymin = lowincome, ymax = highincome, color = 'k')

    # 
    # ax.tick_params(axis='both', which='major', labelsize=14)
    # ax.tick_params(axis='x', rotation=45)
    # a = ['0x', '0.2x', '0.4x', '0.6x','0.8x', '1.0x', '1.2x', '1.4x','1.6x', '1.8x', '2.0x']
    # ax.set_xticklabels(a)
    # ax.set_xlabel("Methanation unit capacity cost (relative to default)", fontsize = 14)
    # ax.set_ylabel('Dollars per MWh methane', fontsize = 14)
    fig.subplots_adjust(bottom=0.2)
    plt.show()
    # plt.close('all')




def find_all_netincome():
    '''
    2 July 2023
    
    The purpose of this function is to plot the break even gas price of the solar system,
    the wind system, and the Spain system. Together with it, we will maybe add 2022 prices and the 
    max European gas price. The output will be a multiple bar chart'''

    sns.set_theme()
    solar = return_income_df('results/csvs/costs/17_07_2023_electrolyzer_gridsolar.csv', choice = 'solar')
    wind = return_income_df('results/csvs/costs/17_07_2023_electrolyzer_gridwind.csv', choice = 'wind')
    spain = return_income_df('results/csvs/costs/17_07_2023_spain_gridsolar.csv', choice = 'spain')

    combinedf = pd.DataFrame(index = range(len(solar)))

    combinedf.index = solar.index
    combinedf['CA solar'] = solar['cost diff']
    combinedf['CA wind'] = wind['cost diff']
    combinedf['ESP solar'] = spain['cost diff']

    fig, ax = plt.subplots()
    combinedf.plot( y = [ 'CA wind', 'CA solar','ESP solar'],  kind = 'bar', ax = ax, color = ["C0", 'C1', 'C4'])
    ax.set_ylim(0, 140)
    ax.tick_params(axis='both', which='major', labelsize=14)
    ax.tick_params(axis='x', rotation=45)
    a = ['0x', '0.2x', '0.4x', '0.6x','0.8x', '1.0x', '1.2x', '1.4x','1.6x', '1.8x', '2.0x']
    ax.set_xticklabels(a)
    ax.set_xlabel("Methanation unit capacity cost (relative to default)", fontsize = 14)
    ax.set_ylabel('USD/MWh methane', fontsize = 14)
    fig.subplots_adjust(bottom=0.4)

    ax.axhline (25, label = r"$\mathrm{2022\;median\;methane\;price\;in\;CA}$", color = 'C1')
    # ax.text(0,29,"2022 methane price in CA", color  = "C1", path_effects=
    #         [patheffects.withStroke(linewidth=1,foreground="k")])
    ax.axhline(45.5, label = r"$ \mathrm{2022\;median\;CA\;price\;with\;100\;USD/t}_{CO_2}\;\mathrm{tax}$", linestyle = 'dashed', color = "C1")
    # ax.text(0,50,"2022 methane price in CA with carbon tax", color  = 'C1', path_effects=
    #         [patheffects.withStroke(linewidth=1,foreground="k")])
    
    ax.axhline (115, label = r"$\mathrm{2022\;median\;NED\;TTF\;price}$", color = 'C4')
    # ax.text(0,70,"2022 methane price in Spain", color  = "C0", path_effects=
    #         [patheffects.withStroke(linewidth=1,foreground="k")])
    ax.axhline(135, label = r"$ \mathrm{2022\;median\;NED\;TTF\;with\;100\;USD/t}_{CO_2}\;\mathrm{tax}$", linestyle = 'dashed', color = "C4")
    # ax.text(0,90,"2022 methane price in Spain with carbon tax", color  = 'C0', path_effects=
    #         [patheffects.withStroke(linewidth=1,foreground="k")])

    (handles, labels) = ax.get_legend_handles_labels()

    handles.insert(4, plt.Line2D([0,0],[0,0], linestyle='none', marker='None'))
    labels.insert(4,'')
    ax.legend(handles[::-1], labels[::-1], loc = 'lower center', ncol = 2, bbox_to_anchor=(0.5, -0.84))
    # plt.show()
    plt.savefig('paper/Figures/RealFigures/allnetincome.pdf')
    plt.savefig('paper/Figures/RealFigures/allnetincome.png', dpi = 500)
    plt.savefig('paper/Figures/Screenshots/ss_allnetincome.png', dpi = 100)
    plt.close('all')

def find_net_income_year_el_solar(path):
    '''
    30 June 2023
    
    This could belong as a 'break even gas price' function (the find_net_income functions),
     or a heatmap, because the purpose of this function is to compare the break even gas price
     that we get from each combination of weather/solar year. We get this experiment from 
     27 June 2023 'yearsolar'. To find the break even gas price, we also need the mindf, which
      is from the same day '''
    
    costdf = pd.read_csv(path, index_col = 0)

    #This is for solar
    mindf = pd.read_csv("results/csvs/costs/27_06_2023_yearsolar_mindf.csv", index_col=0)


    gasload = 10000


    # If any of the values of the column are not 0, keep them. 
    # Gets rid of generators/links etc with no cost
    costdf = costdf.loc[:,  (costdf != 0).any(axis=0)]


    # To find the net income, add up all of the total income and expenses. Costs are positive
    # and income is negative. Then, multiply by -1 to get the positive balance if you made money 
    # This skips over Gas Load, methanogen capital cost, and electrolyzer capital cost. If 'year'
    # is in the columns, it also skips over that

    costdf['Net income'] = costdf[costdf.columns[5:]].sum(axis = 1) * -1 #From "Battery charger" and on
    mindf['Net income'] = mindf[mindf.columns[5:]].sum(axis = 1) * -1 

    # How much can you expect to make with 0 gas load--ie, the solar system and the
    # battery is financing itself for the grid
    sys_income = mindf['Net income'].values[0]


    costdf['cost diff']= costdf['Net income'] - sys_income 
    #Finding cost diff per MW per hour
    costdf['cost diff'] = costdf['cost diff']/8760*1000/gasload * -1 #10000 kW or 10 MW


    # var = 'H2 store size'
    costdf = costdf.pivot(index = 'solar year', columns = 'grid year', values= 'cost diff')
    costdf.sort_index(level = 0, ascending = False, inplace = True)

    fig, ax= plt.subplots()
    sns.heatmap(costdf, cmap = 'viridis', annot = True, ax = ax)
    ax.tick_params(axis='both', which='major', labelsize=14)
    # ax.tick_params(axis = 'y', rotation = 0)
    # ax.tick_params(axis='x', rotation=45)

    # fig.subplots_adjust(bottom = 0.15)
    # ax.set_title(var + ' (kWh)')
    plt.savefig('paper/Figures/RealFigures/yearelecsolar.pdf')
    plt.savefig('paper/Figures/Screenshots/yearelecsolar.png', dpi = 100)

    # plt.show()
    




def plot_cost_any(path, ax): #change back to (path, ax)
    '''
    9 Feb 2023
    The purpose of this function is to be able to plot cost_any plots side by side
    '''
    costdf = pd.read_csv(path, index_col = 0)

    val = 10000

    o = path.replace('.', ' ').replace('_', ' ').split() #.split() splits by space

    if 'gridwind' in o:
        experiment = "Only Grid"
    elif "onlysolar" in o:
        experiment = "Only Solar"
    elif 'onlywind' in o:
        experiment = "Only Wind"
    elif 'gridwind' in o:
        experiment = 'Full system with wind'
    elif 'mindf' in o:
        experiment = 'Full system with no methane'
    else:
        experiment = "Full system with methane"



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
    costdf = costdf/val/8760*1000/0.769 #price per MWh of gas produced by model


    # fig, ax = plt.subplots() #comment this out
    # fig.set_size_inches(8, 7)
    # fig.subplots_adjust(top = 0.8)
    

    if 'mindf' in o:# 21 April not entirely sure why costdf for min has one less column but cest la vie
        colors = [color_dict[colname] for colname in costdf.columns.get_level_values(0)[4:]]
        costdf[costdf.columns[4:]].plot( kind = "bar", stacked = True, color = colors, ax = ax)
    else:
        colors = [color_dict[colname] for colname in costdf.columns.get_level_values(0)[5:]]
        costdf[costdf.columns[5:]].plot( kind = "bar", stacked = True, color = colors, ax = ax)


    #comment out these two lines
    # ax.set_ylabel("LCOE (Dollars/MWh_methane)", fontsize = 16)
    # ax.set_xlabel("Methanation unit cost (Dollars/kWh)", fontsize = 16)
    ax.tick_params(axis='x', rotation=45)
    ax.tick_params(axis = 'both', labelsize = 14)
    ax.set_title( experiment, fontsize = 18)
    # ax.axhline(340, label = '26-Aug-22 price (high)', color = "C0")
    # ax.axhline(118, label = "Highest price", color = "#b03060")
    # ax.axhline (25, label = "2022 median", color = "#21cc89")
    # ax.axhline (14, label = "2021 median", color = "#00a8e1")
    ax.set_xlabel('') #uncomment this line
    handles, labels = ax.get_legend_handles_labels()
    labels[2] = 'methanation'
    # fig.legend(labels = labels, bbox_to_anchor=(0.97, 0.9), ncol =4, fontsize = 11)
    
    ax.get_legend().remove() #uncomment

    # plt.tight_layout()


    # fig.savefig('Poster/elecpricebreakdown.pdf')
    # plt.show()#delete




def four_cost_plot_pres():
    
    presentation = 'May3pres CORC'
    fig, ax = plt.subplots(2,2,figsize=(10,9), sharex=True, sharey = "row")
    fig.subplots_adjust(wspace = 0.1)
    axs = ax.flatten()

    onlygrid = 'results/csvs/costs/17_07_2023_electrolyzer_onlygrid.csv'
    onlysolar = 'results/csvs/costs/18_07_2023_electrolyzer_onlysolar.csv' #onlysolar is no longer dispatch
    gridsolar = 'results/csvs/costs/17_07_2023_electrolyzer_gridsolar.csv'
    mindf = 'results/csvs/costs/17_07_2023_electrolyzer_mindf.csv'

    # onlygrid = 'results/csvs/costs/17_07_2023_electrolyzer_onlygrid.csv'
    # onlysolar = 'results/csvs/costs/17_07_2023_electrolyzer_onlywind.csv' #onlysolar is no longer dispatch
    # gridsolar = 'results/csvs/costs/17_07_2023_electrolyzer_gridwind.csv'
    # mindf = 'results/csvs/costs/17_07_2023_electrolyzer_mindf_wind.csv'
    plot_cost_any(onlysolar, axs[0])
    plot_cost_any(onlygrid, axs[1])
    plot_cost_any(gridsolar, axs[2])
    plot_cost_any(mindf, axs[3])


    for n, ax in enumerate(axs):
        ax.tick_params(axis='both', which='major', labelsize=15)
        ax.tick_params(axis='x', rotation=45)
        a = ['0x', '0.2x', '0.4x', '0.6x','0.8x', '1.0x', '1.2x', '1.4x','1.6x', '1.8x', '2.0x']
        # a = ax.get_xticks()
        # a = [str(entry) + 'x' for entry in a]
        ax.set_xticklabels(a)
        ax.text(-0.1, 1.05, string.ascii_lowercase[n] + ")", transform=ax.transAxes, 
        size=20, weight='bold')

        #ax.xaxis.set_major_formatter(mtick.PercentFormatter(xmax=5))#for some reason this percent formatter takes the position of the 

    axs[0].set_ylim(bottom = 0)
    
    fig.supylabel("Levelized Cost of Methane [USD/MWh]", fontsize = 18)
    fig.supxlabel("Methanation unit capacity cost (relative to reference case)", fontsize = 16)
    

    handles, labels = axs[2].get_legend_handles_labels()
    labels = [labeldict[label] for label in labels]
    #print(labels)
    fig.legend(handles, labels, ncol = 3, loc = 'upper center', fontsize = 14)
    fig.subplots_adjust(top = 0.84, bottom = 0.15)


    # plt.show()
    # fig.savefig('paper/Figures/Screenshots/supfigs/ss_fourplots_wind.png', dpi = 100)
    # fig.savefig('paper/Figures/RealFigures/supfigs/fourplots_wind.pdf')
    # fig.savefig('paper/Figures/RealFigures/supfigs/fourplots_wind.png', dpi = 500)

    fig.savefig('paper/Figures/Screenshots/ss_fourplots.png', dpi = 100)
    fig.savefig('paper/Figures/RealFigures/fourplots.pdf')
    fig.savefig('paper/Figures/RealFigures/fourplots.png', dpi = 500)
    plt.close('all')

        
    # fig.savefig('paper/Figures/RealFigures/megencosts_income_wind.pdf')
    # fig.savefig('paper/Figures/RealFigures/megencosts_income_wind.png', dpi = 500)


def four_cost_plot_Spain():
    

    presentation = 'May3pres CORC'
    fig, ax = plt.subplots(2,2,figsize=(10,9), sharex=True, sharey = "row")
    fig.subplots_adjust(wspace = 0.1)
    axs = ax.flatten()

    

    onlygrid = 'results/csvs/costs/17_07_2023_spain_onlygrid.csv'
    onlysolar = 'results/csvs/costs/17_07_2023_spain_onlysolar.csv'
    gridsolar = 'results/csvs/costs/17_07_2023_spain_gridsolar.csv'
    mindf = 'results/csvs/costs/17_07_2023_spain_mindf.csv'
    plot_cost_any(onlysolar, axs[0])
    plot_cost_any(onlygrid, axs[1])
    plot_cost_any(gridsolar, axs[2])
    plot_cost_any(mindf, axs[3])


    for n, ax in enumerate(axs):
        ax.tick_params(axis='both', which='major', labelsize=15)
        ax.tick_params(axis='x', rotation=45)
        a = ['0x', '0.2x', '0.4x', '0.6x','0.8x', '1.0x', '1.2x', '1.4x','1.6x', '1.8x', '2.0x']
        # a = ax.get_xticks()
        # a = [str(entry) + 'x' for entry in a]
        ax.set_xticklabels(a)
        ax.text(-0.11, 1.05, string.ascii_lowercase[n] + ")", transform=ax.transAxes, 
        size=18, weight='bold')

        #ax.xaxis.set_major_formatter(mtick.PercentFormatter(xmax=5))#for some reason this percent formatter takes the position of the 

    ymin, ymax = axs[0].get_ylim()
    # axs[1].set_ylim(ymin, ymax)
    # axs[1].get_yaxis().set_ticks([])
    ymin, ymax = axs[2].get_ylim()
    # axs[3].set_ylim(ymin, ymax)
    # axs[3].get_yaxis().set_ticks([])





    # axs[0].set_title(r"$\bf{a)}$", fontsize = 20)
    
    # axs[0].set_ylabel("Levelized Cost of Methane [$/MWh]", fontsize = 14)
    fig.supylabel("Levelized Cost of Methane [USD/MWh]", fontsize = 18)
    fig.supxlabel("Methanation unit capacity cost (relative to reference case)", fontsize = 16)
    

    handles, labels = axs[2].get_legend_handles_labels()
    labels = [labeldict[label] for label in labels]
    #print(labels)
    fig.legend(handles, labels, ncol = 3, loc = 'upper center', fontsize = 14)
    fig.subplots_adjust(top = 0.83, bottom = 0.15)


        
    fig.savefig('paper/Figures/Screenshots/supfigs/ss_fourplots_Spain.png', dpi = 100)
    fig.savefig('paper/Figures/RealFigures/supfigs/fourplots_Spain.pdf')
    fig.savefig('paper/Figures/RealFigures/supfigs/fourplots_Spain.png', dpi = 500)
    # plt.show()
    plt.close('all')


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

    gasload = 10000 * 0.769

    elecdf = pd.read_csv('results/csvs/costs/17_07_2023_electrolyzer_gridsolar.csv', index_col= 0)
    battdf = pd.read_csv('results/csvs/costs/18_07_2023_battery_gridsolar.csv', index_col = 0)
    # h2df = pd.read_csv('results/csvs/costs/18_07_2023_h2store_gridsolar.csv', index_col = 0)
    gi_costdf = pd.read_csv('results/csvs/costs/18_07_2023_gicost_gridsolar.csv', index_col = 0) #g
    drdf05 = pd.read_csv('results/csvs/costs/18_07_2023_DR0.5_gridsolar.csv', index_col = 0) #discount rate of 5%
    drdf09 = pd.read_csv('results/csvs/costs/19_07_2023_DR0.9_gridsolar.csv', index_col = 0)

    elecdf_hisolvals = elecdf.copy()
    elecdf_losolvals = elecdf.copy()


    elecdf_hisolvals = mod_solar_cost(elecdf_hisolvals, 'high')
    elecdf_losolvals = mod_solar_cost(elecdf_losolvals, 'low')

    mindf = pd.read_csv("results/csvs/costs/17_07_2023_electrolyzer_mindf.csv", index_col=0)
    mindf['Net income'] = mindf[mindf.columns[5:]].sum(axis = 1) * -1 #Before we did not care about the electrolyzer capital cost. If we change the mindf, we will need to change this as well. 
    sys_income = mindf['Net income'].values[0]

    mindf05 = pd.read_csv('results/csvs/costs/18_07_2023_DR0.5_gridsolar_mindf.csv', index_col = 0)
    mindf09 = pd.read_csv('results/csvs/costs/19_07_2023_DR0.9_gridsolar_mindf.csv', index_col = 0)

    mindf05['Net income'] = mindf05[mindf05.columns[5:]].sum(axis = 1) * -1 #Before we did not care about the electrolyzer capital cost. If we change the mindf05, we will need to change this as well. 
    sys_income05 = mindf05['Net income'].values[0]

    mindf09['Net income'] = mindf09[mindf09.columns[5:]].sum(axis = 1) * -1 #Before we did not care about the electrolyzer capital cost. If we change the mindf09, we will need to change this as well. 
    sys_income09 = mindf09['Net income'].values[0]
    
    elecdf = add_costreq_column(elecdf, gasload, sys_income)
    elecdf_hisolvals = add_costreq_column(elecdf_hisolvals, gasload, sys_income)
    elecdf_losolvals = add_costreq_column(elecdf_losolvals, gasload, sys_income)
    # h2df = add_costreq_column(h2df, gasload, sys_income)
    battdf = add_costreq_column(battdf, gasload, sys_income)
    #print(elecdf.loc[elecdf['methanogen capital cost'] == 120])
    gi_costdf = add_costreq_column(gi_costdf, gasload, sys_income)
    drdf05 = add_costreq_column(drdf05, gasload, sys_income05)
    drdf09 = add_costreq_column(drdf09, gasload, sys_income09)


    
    basecostreq = elecdf.loc[(elecdf['methanogen capital cost'] == elecdf['methanogen capital cost'].median()) & (elecdf['electrolyzer capital cost'] == elecdf['electrolyzer capital cost'].median())]['cost diff'].values[0]

    # print(basecostreq)
    elecdf = elecdf.sort_values(by ="methanogen capital cost")
    megenpr = elecdf['methanogen capital cost'].unique()
    megenpr = [x for x in megenpr]
    megenlow = megenpr[4]
    megenhi = megenpr[6]
    methanation_high = elecdf.loc[(elecdf['methanogen capital cost'] == megenhi) & (elecdf['electrolyzer capital cost'] == elecdf['electrolyzer capital cost'].median())]['cost diff'].values[0]
    methanation_high = methanation_high/basecostreq - 1
    methanation_low = elecdf.loc[(elecdf['methanogen capital cost'] == megenlow) & (elecdf['electrolyzer capital cost'] == elecdf['electrolyzer capital cost'].median())]['cost diff'].values[0]
    methanation_low = methanation_low/basecostreq-1

    elecdf = elecdf.sort_values(by ="electrolyzer capital cost")
    elecpr = elecdf['electrolyzer capital cost'].unique()
    elecpr = [x for x in elecpr]
    eleclow = elecpr[4]
    elechi = elecpr[6]

    electrolyzer_high = elecdf.loc[(elecdf['methanogen capital cost'] == elecdf['methanogen capital cost'].median()) & (elecdf['electrolyzer capital cost'] == elechi)]['cost diff'].values[0]
    electrolyzer_high = electrolyzer_high/basecostreq-1
    electrolyzer_low = elecdf.loc[(elecdf['methanogen capital cost'] == elecdf['methanogen capital cost'].median()) & (elecdf['electrolyzer capital cost'] == eleclow)]['cost diff'].values[0]
    electrolyzer_low = electrolyzer_low/basecostreq-1



    battdf = battdf.sort_values(by ="battery capital cost")
    battpr = battdf['battery capital cost'].unique()
    battpr = [x for x in battpr]
    battlow = battpr[4]
    batthi = battpr[6]


    # h2df = h2df.sort_values(by ="H2 store capital cost")
    # h2pr = h2df['H2 store capital cost'].unique()
    # h2pr = [x for x in h2pr]
    # h2low = h2pr[4]
    # h2hi = h2pr[6]


    batt_high = battdf.loc[(battdf['methanogen capital cost'] == battdf['methanogen capital cost'].median()) & (battdf['battery capital cost'] == batthi)]['cost diff'].values[0]
    batt_high = batt_high/basecostreq-1
    batt_low = battdf.loc[(battdf['methanogen capital cost'] == battdf['methanogen capital cost'].median()) & (battdf['battery capital cost'] == battlow)]['cost diff'].values[0]
    batt_low = batt_low/basecostreq-1


    # h2_high = h2df.loc[ (h2df['H2 store capital cost'] == h2hi)]['cost diff'].values[0]
    # h2_high = h2_high/basecostreq-1
    # h2_low = h2df.loc[ (h2df['H2 store capital cost'] == h2low)]['cost diff'].values[0]
    # h2_low = h2_low/basecostreq-1


    meth_elec_high = elecdf.loc[(elecdf['methanogen capital cost'] == megenhi) & (elecdf['electrolyzer capital cost'] == elechi)]['cost diff'].values[0]
    meth_elec_high = meth_elec_high/basecostreq - 1
    meth_elec_low = elecdf.loc[(elecdf['methanogen capital cost'] == megenlow) & (elecdf['electrolyzer capital cost'] == eleclow)]['cost diff'].values[0]
    meth_elec_low = meth_elec_low/basecostreq - 1

    # print(elecdf_hisolvals)
    solarhigh = elecdf_hisolvals.loc[(elecdf_hisolvals['methanogen capital cost'] == elecdf_hisolvals['methanogen capital cost'].median()) & (elecdf_hisolvals['electrolyzer capital cost'] == elecdf_hisolvals['electrolyzer capital cost'].median())]['cost diff'].values[0]
    solarhigh = solarhigh/basecostreq - 1
    solarlow = elecdf_losolvals.loc[(elecdf_losolvals['methanogen capital cost'] == elecdf_losolvals['methanogen capital cost'].median()) & (elecdf_losolvals['electrolyzer capital cost'] == elecdf_losolvals['electrolyzer capital cost'].median())]['cost diff'].values[0]
    solarlow = solarlow/basecostreq - 1    

    drhigh = drdf09['cost diff'].values[0]
    drhigh = drhigh/basecostreq-1
    drlow = drdf05['cost diff'].values[0]
    drlow = drlow/basecostreq-1


    # val17 = yeardf.loc[yeardf['year'] == 2017]['cost diff'].values[0]
    # val17 = val17/basecostreq-1

    # val18 = yeardf.loc[yeardf['year'] == 2018]['cost diff'].values[0]
    # val18 = val18/basecostreq-1

    # val20 = yeardf.loc[yeardf['year'] == 2020]['cost diff'].values[0]
    # val20 = val20/basecostreq-1

    # year_high = yeardf[yeardf['year'] != 2018]['cost diff'].max() #Because 2018 is weird #I think I fixed 2018
    # year_high = yeardf['cost diff'].max()
    # year_high = year_high/basecostreq-1
    # year_low = yeardf['cost diff'].min()
    # year_low = year_low/basecostreq-1

    gi_costdf = gi_costdf.sort_values(by = 'inverter capital cost')
    gipr = gi_costdf['inverter capital cost'].unique()
    gipr = [x for x in gipr]
    
    gilo = gipr[4]
    gihi = gipr[6]


    # print(gi_high)
    # print(basecostreq)

    gi_high = gi_costdf.loc[gi_costdf['inverter capital cost']== gihi]['cost diff'].values[0]
    gi_high = gi_high/basecostreq-1
    gi_low = gi_costdf.loc[gi_costdf['inverter capital cost']== gilo]['cost diff'].values[0]
    gi_low = gi_low/basecostreq-1
    # meth_elec_high = meth_elec_high/basecostreq - 1



    # year_high = 
    fig, ax = plt.subplots()
    fig.set_size_inches(8, 6)
    factorlist = [r"$\bf{electrolyzer}$" + ' annualized capital cost\n43 USD/kW/yr [+/- 20%]', r"$\bf{methanation\:unit}$" + ' annualized\ncapital cost 76 USD/kW/yr [+/- 20%]', r"$\bf{Both}$"+' methanation unit and electrolyzer\ncapital cost [+/- 20%]',  r"$\bf{grid}$"+ ' connection annualized capital cost\n14 USD/kW/yr[+/- 20%]', r"$\bf{battery\:storage}$"+' annualized\ncapital cost 15 USD/kWh/yr[+/- 20%]',r"$\bf{solar\:PV}$"' annualized capital cost \n 59 USD/kW/yr [+/- 20%] ', r"$\bf{discount\:rate}$"' 7% [5\% - 9\%] ']
    # factorlist = ['methanation unit annual capital cost\n120 USD/kW/yr[+/- 40%]', 'electrolyzer annualized capital cost\n146 $/kW/yr[+/- 40%]', 'methanation and electrolyzer cost\n both [+/- 40%]',  'grid inverter annualized capital cost\n34 $/kW/yr[+/- 40%]', 'data year\n2019 [2020, 2017]']
    highs = [electrolyzer_high, methanation_high, meth_elec_high,  gi_high,  batt_high,solarhigh, drhigh]
    # highs = [methanation_high, electrolyzer_high, meth_elec_high, gi_high, year_high]
    highs = [x * 100 for x in highs]
    lows = [ electrolyzer_low, methanation_low, meth_elec_low,  gi_low, batt_low,solarlow, drlow]
    # lows = [methanation_low, electrolyzer_low, meth_elec_low,  gi_low, year_low]
    lows = [x * 100 for x in lows]

    highbars = ax.barh(factorlist, highs, height= 0.4, color = 'C0')

    ax.bar_label(highbars, fmt = '%.0f%%', label_type='center', color = 'white')
    lowbars = ax.barh(factorlist, lows, height = 0.4, color = 'C1')
    ax.bar_label(lowbars, fmt = '%.0f%%', label_type='center')
    ax.invert_yaxis()
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(xmax = 100))
    ax.spines[['right', 'top', 'left']].set_visible(False)
    ax.set_yticklabels(factorlist, fontsize = 13)
    ax.set_xlabel ("Percent change in break-even gas price", fontsize = 16)
    # ax.set_title('Sensitivity of methane price to various factors', fontsize = 20, position = (0.13, 0.9))
    plt.tight_layout()
    # plt.savefig('paper/figures/RealFigures/compareChangeBars.pdf')
    # plt.savefig('paper/figures/RealFigures/compareChangeBars.png', dpi = 500)
    # plt.savefig('paper/figures/Screenshots/ss_compareChangeBars.png', dpi = 100)
    # plt.show()
    plt.close('all')


    #Finding the default price


##################################################################
###################### CAPACITY FACTORS ##########################
##################################################################

########################## FIGURE 7 #############################
def cf_sensitivity():
    '''
    20 April 2023
    This function uses a csv that takes into account all of the different biomethane time series, sees 
    what percent each of them is varying, and so forth
    
    Twovar can be 'electrolyzer cost' or 'grid connection cost
    '''
    df = pd.read_csv('results/csvs/cfdata/allcfs_17_07_2023_electrolyzer_gridsolar.csv', index_col = 0)

    #var = 'constant biogas'
    #var = 'constant biogas +/-1%'
    # var = 'constant biogas +/-10%'
    # var = 'biogas capacity factor'
    # var = 'grid capacity factor'
    # var = 'local to grid capacity factor'
    # var = 'grid to local capacity factor'
    var = 'electrolyzer capacity factor'
    # var = 'methanation capacity factor'


    twovar = 'electrolyzer cost'
    presentation = 'Maypres'
    df['methanation cost'] = df['methanation cost'] / df['methanation cost'].median()
    df[twovar] = df[twovar]/ df[twovar].median()
    df = df.round(2)
    df['biogas capacity factor'] = df['biogas capacity factor'] * 100


    df = df.pivot(index = 'methanation cost', columns = twovar, values= var)
    df.sort_index(level = 0, ascending = False, inplace = True)

    fig, ax = plt.subplots()
    sns.heatmap(df, cmap = 'viridis', annot = True, ax = ax, cbar_kws={ 'label': 'Capacity factor (%)'})
    ax.tick_params(axis='both', which='major', labelsize=14)
    ax.tick_params(axis = 'y', rotation = 0)
    ax.tick_params(axis='x', rotation=45)
    a = ['0x', '0.2x', '0.4x', '0.6x','0.8x', '1.0x', '1.2x', '1.4x','1.6x', '1.8x', '2.0x']
    ax.set_xticklabels(a)
    a = a[::-1]
    ax.set_yticklabels(a)

    fig.subplots_adjust(bottom = 0.15)
    ax.set_title(var)

    # plt.show()
    # plt.close('all')
    if var == 'biogas capacity factor':
        plt.savefig('paper/Figures/RealFigures/'+ var + '.pdf')
        plt.savefig('paper/Figures/RealFigures/'+ var + '.png', dpi = 500)
        plt.savefig('paper/Figures/Screenshots/ss_'+ var + '.png', dpi = 100)
    else:
        plt.savefig('paper/Figures/RealFigures/supfigs/'+ var + '.pdf')
        plt.savefig('paper/Figures/RealFigures/supfigs/'+ var + '.png', dpi = 500)
        plt.savefig('paper/Figures/Screenshots/supfigs/ss_'+ var + '.png', dpi = 100)        



def cf_compare(csvpath, twovar):
    '''
    22 June 2023
    
    This function takes in a allcf_csv, takes the capacity factor of methanation and the electrolyzer,
    and plots them next to one another while varying the price of the methanation unit on the x axis
    
    Twovar can either be 'electrolyzer cost' or 'grid connection cost'
    
    ''' 
    sns.set_theme()
    df = pd.read_csv(csvpath, index_col = 0)
    df['methanation cost'] = df['methanation cost'] / df['methanation cost'].median()
    df = df[df[twovar] == df[twovar].median()]

    df[twovar] = df[twovar]/ df[twovar].median()

    df = df.round(2)

    df = df.sort_values(by ="methanation cost")

    # df.index = df['methanation cost']

    fig, ax = plt.subplots()

    df.plot(x= 'methanation cost', y = ['electrolyzer capacity factor', 'methanation capacity factor'], kind = 'bar', ax = ax)

    ax.set_ylim(0, 1)
    ax.set_ylabel('Capacity factor', fontsize = 14)
    ax.set_xlabel("Methanation Unit price relative to default", fontsize = 14)
    ax.tick_params(axis='both', which='major', labelsize=14)
    ax.tick_params(axis='x', rotation=45)
    a = ['0x', '0.2x', '0.4x', '0.6x','0.8x', '1.0x', '1.2x', '1.4x','1.6x', '1.8x', '2.0x']
    # a = ax.get_xticks()
    # a = [str(entry) + 'x' for entry in a]
    ax.set_xticklabels(a)
    # plt.savefig('paper/Figures/RealFigures/Supfigs/onlywindcf.pdf')
    # plt.savefig('paper/Figures/RealFigures/Supfigs/onlywindcf.png', dpi = 500)
    plt.savefig('paper/Figures/Screenshots/supfigs/ss_onlysolarcf.png', dpi = 100)
    # plt.tight_layout()
    # plt.show()
    # plt.close('all')

    
def capacity(sumcsvpath, twovar):
    '''
    26 April 2023
    
    This function is similar to cf_sensitivity, except that it makes a heatmap based on the size of
    the 'battery size' or 'H2 store size. It takes a summary csv. Twovar can either be 'electrolyzer cost' or 'grid connection cost'
    
    colormaps: magma, viridis'''
    df = pd.read_csv(sumcsvpath, index_col=0)

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



##################################################################################
######################## DURATION CURVES AND TIME SERIES #########################
#################################################################################

def plot_bp_gas():
    '''
    5 July 2023
    The purpose of this function is to plot the natural gas prices around the world. 
    It plots the same data as the figure on page 33 of the BP stats review. Years
    2005-2021. I typed in the table on the page by hand.
    
    13 July 2023
    Adding 2022, from Energy Institute stats review '''

    # sns.set_theme()
    plt.rcdefaults()
    countries = {'GER import': [5.83, 7.87, 7.99, 11.6, 8.53, 8.03, 10.49, 10.93, 10.73, 9.11, 6.72, 4.93, 5.62, 6.64, 5.03, 4.06, 8.94, 24.17],
     'UK NBP': [7.38, 7.88, 6.01, 10.79, 4.85, 6.56, 9.04, 9.46, 10.64, 8.25, 6.53, 4.69, 5.80, 8.06, 4.47, 3.42, 15.80, 25.10],
     'NED TTF': [6.07, 7.46, 5.93, 10.66, 4.96, 6.77, 9.26, 9.45, 9.75, 8.14, 6.44, 4.54, 5.72, 7.90, 4.45, 3.07, 16.02, 37.48],
     'USA Henry Hub': [8.79, 6.76, 6.95, 8.85, 3.89, 4.39, 4.01, 2.76, 3.71, 4.35, 2.69, 2.46, 2.96, 3.12, 2.51, 1.99, 3.84, 6.45],
     'CAN': [7.25, 5.83, 6.17, 7.99, 3.38, 3.69, 3.47, 2.27, 2.93, 3.87, 2.01, 1.55, 2.58, 1.18, 1.27, 1.58, 2.75, np.nan]}
    
    
    df = pd.DataFrame(countries)
    years = pd.date_range('2005', '2023', freq = 'Y')
    df.index = years
    fig, ax = plt.subplots()
    df = df/0.29
    df.plot(ax = ax, linewidth = 2)
    ax.set_xlabel('Year', fontsize = 14)
    ax.set_ylim(0, 180)
    ax.legend(loc = "upper left")
    ax.xaxis.set_tick_params(labelsize=12)
    ax.yaxis.set_tick_params(labelsize=12)
    ax.set_ylabel('USD/MWh', fontsize = 14)


    '''
    In this section of the code, we are going to plot daily data from 2022
    '''

    axinax = ax.inset_axes([0.45, 0.65, 0.5, 0.3])
    df2 = pd.read_csv('data/ICE Dutch TTF Natural Gas Futures Historical Data(1).csv') 
    df2 = df2.sort_index(ascending=False)
    df2 = df2.reset_index(drop=True)
    # df2['Price'] = df2['Price']/0.29
    df2['Price'].plot(ax = axinax, color = 'C2')
    
    axinax.set_xticklabels(['test', 'Jan', 'May', 'Oct'])
    ax.text(0.9, 0.6, s = '2022', transform = ax.transAxes)
    
    plt.savefig('paper/Figures/RealFigures/bp_gasprice.pdf')
    plt.savefig('paper/Figures/RealFigures/bp_gasprice.png', dpi = 500)
    plt.savefig('paper/Figures/Screenshots/ss_bp_gasprice.png', dpi = 100)
    # plt.show()
    # plt.close('all')
    


def plot_elec_ts():
    df = pd.read_csv('results/csvs/alldata/11_04_2023_year_2019_gridsolar_dispatch_onerun.csv')
    
    fig, ax = plt.subplots()
    half_year_locator = mdates.MonthLocator(interval=6)
    df[24:192].plot(x = 'snapshot', y = ['solar ts', 'grid to electricity link ts', 'battery store ts'], ax = ax)
    fig.legend()
    # fig, ax = plt.subplots()
    # ax.plot(df['grid to electricity link ts'][4020:4044])
    # ax.plot(df[''])
    plt.savefig("Presentations/April21pres/electimeseriesJan.pdf")



def plot_gridprice(path, ax):
    '''
    1 July 2023
    The purpose of this function is to serve as a helper for the bigger function
    plot_all_gridprice()'''
    ax.tick_params(axis='both', which='major', labelsize=12)
    df = pd.read_csv(path, index_col = 0)
    # df.index = pd.to_datetime(df.index)
    df['Average'].plot(ax = ax, linewidth = 2)
    ax.fill_between(x = df.index, y1 = df['10th percentile'], y2 = df['90th percentile'], alpha = 0.5, label = '10th to 90th percentile')
    # ax.fill_between(x = df.index, y1 = df['Min'], y2 = df['Max'], alpha = 0.2)

    ypos = df['Average'].mean()

    ax.axhline(y = ypos, linestyle = '--')
    ypos = round(ypos, 1)
    ax.text(5, ypos + 3, f'{ypos}' + ' USD/MWh' )
    
    # date_fmt = mdates.DateFormatter('%b %Y')
    # ax.xaxis.set_major_formatter(date_fmt)
    # ax.get_legend().remove()


    # ax.xaxis.set_major_locator(quarter_year_locator)
    # ax.xaxis.set_major_formatter(month_formatter)



def find_avg_gridprice(path):
    '''
    20 July 2023
    The purpose of this function is to find the average price of electricity for each hour of the year
    We are also interested in '''
    
    df = pd.read_csv(path, index_col = 0)
    df.index = pd.to_datetime(df.index)

    avdf = pd.DataFrame(index = range(24), columns = ['Average', 'Min', 'Max', '10th percentile', '90th percentile' ])

    for x in range(24):
        df24 = df[x::24].sort_values(by = 'price', ascending = True)
        avdf.loc[x, 'Average'] = df24.mean().values[0]
        avdf.loc[x, 'Min'] = df24.min().values[0]
        avdf.loc[x, 'Max'] = df24.max().values[0]
        avdf.loc[x, '10th percentile'] = df24.iloc[35].values[0]
        avdf.loc[x, '90th percentile'] = df24.iloc[328].values[0]
    
    moveidx = list(range(8)) #Since this is in UTC, but we want to show local time, we need to shift the last 16 indices to the front (or move the first 8 indices to the back)
    a = avdf.iloc[[i for i in avdf.index if i not in moveidx], :]
    b = avdf.iloc[moveidx, :]
    avdf = pd.concat([a, b])
    avdf = avdf.reset_index(drop = True)

    path = path.split('.')
    path = path[0] + "_avghr." + path[1]
    avdf.to_csv(path)


    # ax.xaxis.set_major_locator(quarter_year_locator)
    # ax.xaxis.set_major_formatter(month_formatter)


def plot_all_gridprice():
    '''
    1 July 2023
    The purpose of this function is to plot the gridprice of california from 2017-2020
    in four rows'''
    # sns.set_theme()
    fig, axs = plt.subplots(2, 2, sharey = True, sharex = True, gridspec_kw = {'hspace' : 0.1, 'wspace' : 0.1})
    plot_gridprice('data/elecprice_csvs/2017UTCCAISOprice_avghr.csv', axs[0,0])
    plot_gridprice('data/elecprice_csvs/2018UTCCAISOprice_avghr.csv', axs[0,1])
    plot_gridprice('data/elecprice_csvs/2019UTCCAISOprice_avghr.csv', axs[1,0])
    plot_gridprice('data/elecprice_csvs/2020UTCCAISOprice_avghr.csv', axs[1,1])
    axs = axs.flatten()
    colors = ['C0', 'C1', 'C2', 'C3']
    # for ax in axs[0:4]:
    #     ax.xaxis.set_ticklabels([])

      
    # date_fmt = mdates.DateFormatter('%b %Y')
    # axs[3].xaxis.set_ticklabels(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
    handles = []
    labels = []
    for n, ax in enumerate(axs):
        ax.text(0.01, 0.88, string.ascii_lowercase[n] + ")", transform=ax.transAxes, 
        size=14, weight='bold')
        ax.get_lines()[0].set_color(colors[n])
        ax.get_lines()[1].set_color(colors[n])
        handle, label = ax.get_legend_handles_labels()
        ax.set_ylim(-20, 150)
        # if n == 2:
        #     for line in handle:
        #         line.set_linewidth(0.5)
        handles.append(handle[0])
        labels.append(label[0])
    labels = ['2017', '2018', '2019', '2020']

    handles.append(handle[1])
    labels.append(label[1])
    # handles, labels = fig.
    leg = fig.legend(handles = handles, labels = labels,ncol = 3, loc= 'upper center')

    for n, line in enumerate(leg.get_lines()):
        line.set_linewidth(2)
        # if n == 2:
        #     line.set_linewidth(2)
    fig.supxlabel('Hours in a year')
    fig.supylabel('USD/MWh electricity')
    fig.savefig('paper/Figures/RealFigures/supfigs/elecprices.pdf')
    fig.savefig('paper/Figures/Screenshots/supfigs/ss_elecprices.png', dpi = 100)
    # plt.show()
    # plt.close('all')

def plot_gridprice_dc():
    '''
    1 July 2023
    The purpose of this function is to plot the duration curve of four electricity price
    time series from California'''
    plt.rcdefaults()
    fig, ax = plt.subplots()
    elec17 = prep_csv('data/elecprice_csvs/2017UTCCAISOprice.csv')
    elec18 = prep_csv('data/elecprice_csvs/2018UTCCAISOprice.csv')
    elec19 = prep_csv('data/elecprice_csvs/2019UTCCAISOprice.csv')
    elec20 = prep_csv('data/elecprice_csvs/2020UTCCAISOprice.csv')


    ax.plot(elec19['price'], linewidth = 4, label = '2019', color = 'C2')
    ax.plot(elec17['price'], linewidth = 3, linestyle = 'dotted', label = '2017')
    ax.plot(elec18['price'], linewidth = 2, linestyle = '--', label = '2018')
    
    ax.plot(elec20['price'], linewidth = 1, label = '2020', color = 'C3')

    ax.legend()
    handles, labels = ax.get_legend_handles_labels()
    ax.set_xlabel('Hours in a year')
    ax.set_ylabel('Dollars per kWh electricity')
    
    ax.set_yscale('symlog')
    
    fig.savefig('paper/Figures/RealFigures/supfigs/elecprice_dcurv.pdf')
    fig.savefig('paper/Figures/RealFigures/supfigs/elecprice_dcurv.png', dpi = 500)
    fig.savefig('paper/Figures/Screenshots/supfigs/ss_elecprice_dcurv.png', dpi = 100)
    # plt.show()
    # plt.close('all')


def plot_gridprice_dc_wspain():
    '''
    5 July 2023
    The purpose of this function is to plot the duration curve of prices from Spain together
    with electricity prices from California'''
    plt.rcdefaults()
    fig, ax = plt.subplots()

    elec19 = prep_csv('data/elecprice_csvs/2019UTCCAISOprice.csv')

    elecESP = prep_csv('data/Spain/2019UTCDayAheadPrice.csv')


    ax.plot(elec19['price'], linewidth = 4, label = '2019 CA', color = 'C2')
    ax.plot(elecESP['price'], linewidth = 2, linestyle = '--', label = '2019 Spain', color = 'C0')

    ax.legend()
    handles, labels = ax.get_legend_handles_labels()
    ax.set_yscale('symlog')
    ax.set_xlabel('Hours in a year')
    ax.set_ylabel('Dollars per kWh electricity')
    
    
    fig.savefig('paper/Figures/RealFigures/supfigs/elecprice_dcurv_wspain.pdf')
    fig.savefig('paper/Figures/RealFigures/supfigs/elecprice_dcurv_wspain.png', dpi = 500)
    fig.savefig('paper/Figures/Screenshots/supfigs/ss_elecprice_dcurv_wspain.png', dpi = 100)
    # plt.show()
    # plt.close('all')


def compare_dcurves():
    '''
    Modified 5 July 2023
    
    This function makes a supplementary Figure about the
    methanation link time series'''
    onlysolar = pd.read_csv("results/csvs/alldata/18_07_2023_electrolyzer_onlysolar.csv")
    onlygrid = pd.read_csv("results/csvs/alldata/17_07_2023_electrolyzer_onlygrid.csv")
    gridsolar = pd.read_csv("results/csvs/alldata/17_07_2023_electrolyzer_gridsolar.csv")



    onlysolar = onlysolar.query('`megen cost` == `megen cost`.median() ')
    onlygrid = onlygrid.query(' `megen cost` == `megen cost`.median() ')
    gridsolar = gridsolar.query(' `megen cost` == `megen cost`.median() & `electrolyzer cost` == `electrolyzer cost`.median()')


    onlysolar= onlysolar.sort_values(by = ["methanogen link ts"], ascending = False)
    onlysolar.index = range(8760)


    onlygrid = onlygrid.sort_values(by = ["methanogen link ts"], ascending = False)
    onlygrid.index = range(8760)

    gridsolar= gridsolar.sort_values(by = ["methanogen link ts"], ascending = False)
    gridsolar.index = range(8760)

    onlysolar['methanogen link ts'] = onlysolar['methanogen link ts'] /1000
    onlygrid['methanogen link ts'] = onlygrid['methanogen link ts']/1000
    gridsolar['methanogen link ts'] = gridsolar['methanogen link ts']/1000

    fig, ax = plt.subplots()

    ax.plot(gridsolar['methanogen link ts'], label = "Full System", color = "C2")
    ax.plot(onlysolar['methanogen link ts'], label = "Only solar", color = "C1")
    ax.plot(onlygrid['methanogen link ts'], label = "Only grid", color = "C0")


    # ax.set_title("Dcurve of megen link 3 scenarios, 10MW load and 10x sabatier cost")
    ax.set_xlabel("hours", fontsize = 14)
    ax.xaxis.set_tick_params(labelsize=12)
    ax.yaxis.set_tick_params(labelsize=12)
    ax.set_ylabel("MW", fontsize = 14)
    
    ax.legend(fontsize = 12)
    # plt.savefig('paper/Figures/RealFigures/supfigs/methlink_dc.pdf')
    # plt.savefig('paper/Figures/RealFigures/supfigs/methlink_dc.png', dpi = 500)
    # plt.savefig('paper/Figures/Screenshots/supfigs/ss_methlink_dc.png', dpi = 100)
    # plt.show()

def compare_dcurves_elec():
    '''
    Modified 26 July 2023
    
    This function makes a supplementary Figure about the
    electrolyzer link'''
    onlysolar = pd.read_csv("results/csvs/alldata/18_07_2023_electrolyzer_onlysolar.csv")
    onlygrid = pd.read_csv("results/csvs/alldata/17_07_2023_electrolyzer_onlygrid.csv")
    gridsolar = pd.read_csv("results/csvs/alldata/17_07_2023_electrolyzer_gridsolar.csv")



    onlysolar = onlysolar.query('`megen cost` == `megen cost`.median() ')
    onlygrid = onlygrid.query(' `megen cost` == `megen cost`.median() ')
    gridsolar = gridsolar.query(' `megen cost` == `megen cost`.median() & `electrolyzer cost` == `electrolyzer cost`.median()')


    onlysolar= onlysolar.sort_values(by = ["electrolyzer ts"], ascending = False)
    onlysolar.index = range(8760)


    onlygrid = onlygrid.sort_values(by = ["electrolyzer ts"], ascending = False)
    onlygrid.index = range(8760)

    gridsolar= gridsolar.sort_values(by = ["electrolyzer ts"], ascending = False)
    gridsolar.index = range(8760)

    onlysolar['electrolyzer ts'] = onlysolar['electrolyzer ts'] /1000
    onlygrid['electrolyzer ts'] = onlygrid['electrolyzer ts']/1000
    gridsolar['electrolyzer ts'] = gridsolar['electrolyzer ts']/1000

    fig, ax = plt.subplots()

    ax.plot(gridsolar['electrolyzer ts'], label = "Full System", color = "C2")
    ax.plot(onlysolar['electrolyzer ts'], label = "Only solar", color = "C1")
    ax.plot(onlygrid['electrolyzer ts'], label = "Only grid", color = "C0")


    # ax.set_title("Dcurve of megen link 3 scenarios, 10MW load and 10x sabatier cost")
    ax.set_xlabel("hours", fontsize = 14)
    ax.xaxis.set_tick_params(labelsize=12)
    ax.yaxis.set_tick_params(labelsize=12)
    ax.set_ylabel("MW", fontsize = 14)
    
    ax.legend(fontsize = 12)
    plt.savefig('paper/Figures/RealFigures/supfigs/electrolyzer_dc.pdf')
    plt.savefig('paper/Figures/RealFigures/supfigs/electrolyzer_dc.png', dpi = 500)
    plt.savefig('paper/Figures/Screenshots/supfigs/ss_electrolyzer_dc.png', dpi = 100)
    # plt.show()

def methanation_dc_onlysolar():
    '''
    26 July 2023
    
    This function compares the duration curves of a methanation unit with the only solar model'''
    onlysolar = pd.read_csv("results/csvs/alldata/18_07_2023_electrolyzer_onlysolar.csv")




    onlysolar= onlysolar.sort_values(by = ["methanogen link ts"], ascending = False)





    onlysolar['methanogen link ts'] = onlysolar['methanogen link ts'] /1000
    # onlysolar['methanogen link ts'] = onlysolar['methanogen link ts']/onlysolar['methanogen link ts'].max()


    fig, ax = plt.subplots()

    
    norm = mpl.colors.Normalize(vmin=0, vmax=130.787074)
    cmap = plt.get_cmap('viridis')

    for value in onlysolar['megen cost'].unique():
        tempdf = onlysolar[onlysolar['megen cost'] == value]
        # print(tempdf)
        tempdf = tempdf.sort_values(by = ["methanogen link ts"], ascending = False)
        tempdf.index = range(8760)
        ax.plot(tempdf['methanogen link ts'], color = cmap(norm(value)))
    # ax.plot(onlysolar['methanogen link ts'], label = "Only solar", color = "C1")

    cbar = fig.colorbar(plt.cm.ScalarMappable(norm = norm, cmap = cmap), label = "Methanation annualized cost (USD/kW/yr)")


    # ax.set_title("Dcurve of megen link 3 scenarios, 10MW load and 10x sabatier cost")
    ax.set_xlabel("hours", fontsize = 14)
    ax.xaxis.set_tick_params(labelsize=12)
    ax.yaxis.set_tick_params(labelsize=12)
    ax.set_ylabel("MW", fontsize = 14)
    
    ax.legend(fontsize = 12)
    plt.savefig('paper/Figures/RealFigures/supfigs/methlinks_onlysolar_dc.pdf')
    plt.savefig('paper/Figures/RealFigures/supfigs/methlinks_onlysolar_dc.png', dpi = 500)
    plt.savefig('paper/Figures/Screenshots/supfigs/ss_methlinks_onlysolar_dc.png', dpi = 100)
    # plt.show()
    plt.close('all')


def compare_dcurves_secondary():
    '''
    5 July 2023
    
    Based on compare_dcurves, this function finds the difference in electrolyzer performance
    between the solar, wind, and spain cases'''
    gridsolar = pd.read_csv("results/csvs/alldata/25_05_2023_megen_gridsolar.csv")
    gridwind = pd.read_csv('results/csvs/alldata/15_06_2023_electrolyzer_gridwind.csv')
    spainsolar = pd.read_csv("results/csvs/alldata/23_06_2023_Spain_gridsolar.csv")




    spainsolar = spainsolar.query(' `megen cost` == `megen cost`.median() & `electrolyzer cost` == `electrolyzer cost`.median()')
    gridwind = gridwind.query(' `megen cost` == `megen cost`.median() & `electrolyzer cost` == `electrolyzer cost`.median()')
    gridsolar = gridsolar.query(' `megen cost` == `megen cost`.median() & `electrolyzer cost` == `electrolyzer cost`.median()')


    spainsolar= spainsolar.sort_values(by = ["grid to electricity link ts"], ascending = False)
    spainsolar.index = range(8760)


    gridwind = gridwind.sort_values(by = ["grid to electricity link ts"], ascending = False)
    gridwind.index = range(8760)

    gridsolar= gridsolar.sort_values(by = ["grid to electricity link ts"], ascending = False)
    gridsolar.index = range(8760)

    spainsolar['grid to electricity link ts'] = spainsolar['grid to electricity link ts'] /1000
    gridwind['grid to electricity link ts'] = gridwind['grid to electricity link ts']/1000
    gridsolar['grid to electricity link ts'] = gridsolar['grid to electricity link ts']/1000

    fig, ax = plt.subplots()

    ax.plot(gridsolar['grid to electricity link ts'], label = "CA solar", linewidth = 3, color = "C2")
    ax.plot(spainsolar['grid to electricity link ts'], label = "ESP solar", linewidth = 2, color = "C1")
    ax.plot(gridwind['grid to electricity link ts'], label = "CA wind", linestyle = '--', color = "C0")


    # ax.set_title("Dcurve of megen link 3 scenarios, 10MW load and 10x sabatier cost")
    ax.set_xlabel("hours", fontsize = 14)
    ax.xaxis.set_tick_params(labelsize=12)
    ax.yaxis.set_tick_params(labelsize=12)
    ax.set_ylabel("Grid connection operation (MW)", fontsize = 14)
    
    ax.legend(fontsize = 12)
    plt.savefig('paper/Figures/RealFigures/supfigs/gridconnection_dc.pdf')
    plt.savefig('paper/Figures/RealFigures/supfigs/gridconnection_dc.png', dpi = 500)
    plt.savefig('paper/Figures/Screenshots/supfigs/ss_gridconnection_dc.png', dpi = 100)
    # plt.show()


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
    newname =  path.replace('nogrid', 'onlysolar')
    if newname != path:
        os.rename(path,newname)

if __name__ == '__main__':
    find_avg_gridprice('data/elecprice_csvs/2018UTCCAISOprice.csv')
    find_avg_gridprice('data/elecprice_csvs/2019UTCCAISOprice.csv')
    find_avg_gridprice('data/elecprice_csvs/2017UTCCAISOprice.csv')
    find_avg_gridprice('data/elecprice_csvs/2020UTCCAISOprice.csv')