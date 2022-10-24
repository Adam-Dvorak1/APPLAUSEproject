
#The purpose of this file is to make a simple model of methanation. There will be two models:
#one with normal sabatier and one with methanogens (bacteria that produce methane)

#author @Adam Dvorak
#Github: Adam-Dvorak1

#With assistance from Lisa Zeyen


import pypsa
import numpy as np
import pandas as pd
from pypsa.descriptors import Dict
from pypsa.components import components, component_attrs
import os


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




overrides = override_component_attrs("override_component_attrs")
network = pypsa.Network(override_component_attrs=overrides)




gasdf = pd.read_csv('data/AppleGas.csv', index_col = 0)
gasdf.index = pd.to_datetime(gasdf.index)


tech_data = pd.read_csv("data/costs_2025.csv")




###------------------Add buses---------------------------------

'''Adam: As Lisa told me, the carrier is not needed for calculation, 
but is a good attribute for analyzing later'''
network.add("Bus","electricity", carrier = "electricity")
#The electricity bus will connect to the hydrogen bus using electrolysis

network.add("Bus", "H2", carrier  = "H2")
#The hydrogen bus will connect to the CH4 bus as an input to methanation

#--------------------------------
# We know how generators connect to a bus. The hydrogen produced
# by electricity can also serve as a "generator". How will these connect?
# Some sort of link
#-------------------------------



network.add("Bus", "gas", carrier = "gas")


network.add("Bus", "CO2_out", carrier = "co2 released") #This CO2 bus is the 

network.add("Bus", "CO2_in", carrier = "co2 stored")



###-------------------Add loads-------------------------
'''We are following a process similar to what we did for simple model of last year. For now, we are assuming
california solar data (population weighted, I believe) from renewables.ninja. However, we need load data of 
methane demand. 

Maybe I can make a constant '''


network.add("Load", #Why are there two loads here? Which is the name?
            "Gas Load", 
            bus="gas", 
            p_set=gasdf["Constant_MW_methane"])

###-------------------Add generators-------------------------

#These connect to the electricity bus. We do not have any CO2 generators. But should we?
#Note: we are using costs from 2025 from the tech_data tables associated with PyPSA



#-------------------Solar-------------------------

hours_in_2011 = pd.date_range('2011-01-01T00:00:00','2011-12-31T23:00:00', freq='H') #I changed the date rate from Z
network.set_snapshots(hours_in_2011)

df_cal_solar = pd.read_csv('data/CaliforniaTimeSeries.csv', index_col=0)
df_cal_solar.index = pd.to_datetime(df_cal_solar.index)
df_cal_solar = df_cal_solar['solar'][[hour.strftime("%Y-%m-%dT%H:%M:%S") for hour in network.snapshots]]


## Here, we get the solar tech data






network.add("Generator", "Solar PV", bus="electricity", p_nom_extendable = True, 
    carrier = 'solar', capital_cost = annual_cost('solar-utility'),
    marginal_cost = 0, p_max_pu = df_cal_solar) #Should we have p_nom_extendable = True? Should we set p_max_pu to a number? Solar has
    #no marginal cost, right?


#-----------------
# How do we manage to add the electricity grid? 
#----------------


###-------------------<<<Add stores>>>---------------------------------
'''We have 
        1) a battery storage connecting to the electricity bus
        2) NO hydrogen storage 
        3) A CO2 store that connects to the methanation process
        4) A CO2 store that connects to the environment
'''

# -------CO2------------------
'''This CO2 store will connect to the methanation process'''
network.add("Store",
      "CO2_in storage",
      e_nom_extendable=True,
      e_initial=3e5,   # assume some initial filling of the CO2 storage just for our minimal example
      e_nom_max=np.inf,   # here you can set a maximum limit for your co2 store
      capital_cost=20,
      carrier="co2 stored",
      bus="CO2_in"
  )


# -------battery------------------
'''This battery connects to the electricity bus'''
network.add("Store",
        "battery",
        bus = "battery",
        e_cyclic = True, #NO FREE LUNCH must return back to original position by end of the year
        e_nom_extendable = True,
        capital_cost = annual_cost("battery storage"))








###--------------------<<<Add links>>>------------------------------------------------------
'''Note, since there is no hydrogen storage, there are no links that connect to the H2
bus alone'''

##--------------------Electricity bus-----------------------------------


# -------Electrolysis to H2 bus------------------
network.add("Link",
        "H2 Electrolysis",
        bus1 = "H2",
        bus0 = "electricity", #as in, electricity is producing hydrogen
        p_nom_extendable = True,
        carrier = "H2 Electrolysis",
        capital_cost = annual_cost("electrolysis"),
        efficiency = tech_data.query("technology == 'electrolysis' & parameter == 'efficiency'")['value'].values[0],
        )

# -------Battery Charger------------------
network.add("Link",
        "battery charger",
        bus0 = "electricity",
        bus1 = "battery",
        carrier = "battery charger",
        efficiency =tech_data.query("technology == 'battery inverter' & parameter == 'efficiency'")['value'].values[0] ** 0.5,
        p_nom_extendable = True,
        capital_cost = annual_cost("battery inverter"))

# -------Battery Discharger----------------
network.add("Link",
        "battery discharger",
        bus0 = "battery",
        bus1 = "electricity",
        carrier = "battery discharger",
        efficiency = tech_data.query("technology == 'battery inverter' & parameter == 'efficiency'")['value'].values[0] ** 0.5,
        p_nom_extendable = True,
        ) 

#----------------
#I am assuming that all of the cost is taken up in the battery charger. 
#I don't know if this is the right way to incorporate this
#Also, should the p_nom_extendable be the same for both cases? Though 
#I suppose it should not matter so much if there is no degradation
#----------------
        



##--------------------METHANATION-----------------------------------
'''Note: This requires four links. One from H2, one from CO2, one to a different 
CO2 bus, and one to the converter/methane bus'''

# -------Methanation ---------------------
# We assume here methanogenation
# Any other 
sabatier_efficiency = 0.8   # ?????
gas_co2_intensity = 0.2     # CO2 intensity in CH4
compressor_efficiency = 0.9#This is unique to the methanogenic process, where we assume that methane needs to be compressed after the fact
network.add("Link",
      "methanation",
      bus0="H2",
      bus1="gas",
      bus2 = "CO2_out",
      bus3 = "CO2_in",
      carrier="methanation",
      marginal_cost=0,
      capital_cost=100,   # annualised capital costs. Working in 
      p_nom_extendable=True,
      efficiency= sabatier_efficiency,    # how much CH4 is produced per H2 input. Positive
      efficiency2= sabatier_efficiency * gas_co2_intensity, # how much CO2 is produced per CH4 output. Positive
      efficiency3 = - (1-sabatier_efficiency), #How much CO2 is used per CH4. Negative. This means that close to 0 is most efficient
      )




network.lopf(pyomo=False, solver_name="gurobi")
#%%


# how much H2 is used for Fischer-Tropsch
network.links_t.p0.plot(title="H2 used for methanogens")
# how much CO2 is used for Fischer-Tropsch
network.links_t.p1.plot(title="CH4 produced via methanogens")
# same like multpliying it with the efficiency
(network.links_t.p0*network.links.efficiency).plot(title="CH4 produced via methanogens")
# how much synthetic fuel is produced via Fischer-Tropsch
network.links_t.p2.plot(title="CO2 used for methanogens")
# same like multpliying it with the efficiency2
(network.links_t.p0*network.links.efficiency2).plot(title="CO2 used for methanogens")
# how much CO2 is in the CO2 storage
network.stores_t.e.plot()