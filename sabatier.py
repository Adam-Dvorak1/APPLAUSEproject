
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


'''We want to get rid of this H2 bus because we can just have another efficiency
be multiplied in the link between the electricity and H2 compressed buses. 

Total efficiency = efficiency of electrolysis * efficiency of compression
Total cost = cost of electrolyzer + cost of compressor

The H2 compressed bus will then have a link connecting to the electricity bus,
and then it will be a part of the methanation process as well
'''
# network.add("Bus", "H2", carrier  = "H2")
# #The hydrogen bus will connect to the CH4 bus as an input to methanation 


network.add("Bus", "H2 compressed", carrier  = "H2 compressed")

#--------------------------------
# We know how generators connect to a bus. The hydrogen produced
# by electricity can also serve as a "generator". How will these connect?
# Some sort of link
#-------------------------------



network.add("Bus", "gas", carrier = "gas")


network.add("Bus", "CO2 out", carrier = "co2 released") #This CO2 bus is the 

network.add("Bus", "biogas", carrier = "biogas") #For both processes, we have access to a biogas plant


network.add("Bus", "CO2 compressed", carrier = "co2 compressed")







###-------------------<<<Add generators>>>----------------------------------------------


#These connect to the electricity bus. We do not have any CO2 generators. But should we?
#Note: we are using costs from 2025 from the tech_data tables associated with PyPSA



##-------------------Solar---------------------------------------

hours_in_2011 = pd.date_range('2011-01-01T00:00:00','2011-12-31T23:00:00', freq='H') #I changed the date rate from Z
network.set_snapshots(hours_in_2011)

df_cal_solar = pd.read_csv('data/CaliforniaTimeSeries.csv', index_col=0)
df_cal_solar.index = pd.to_datetime(df_cal_solar.index)
df_cal_solar = df_cal_solar['solar'][[hour.strftime("%Y-%m-%dT%H:%M:%S") for hour in network.snapshots]]



network.add("Generator", "Solar PV", bus="electricity", p_nom_extendable = True, 
    carrier = 'solar', capital_cost = annual_cost('solar-utility'),
    marginal_cost = 0, p_max_pu = df_cal_solar) #Should we have p_nom_extendable = True? Should we set p_max_pu to a number? Solar has
    #no marginal cost, right?


#-----------------
# How do we manage to add the electricity grid? 
#----------------


##-------------------Biogas----------------------------------------------
network.add("Generator", "Biogas", bus="biogas", p_nom_extendable = True, 
    carrier = 'biogas', capital_cost = annual_cost('solar-utility'),
    marginal_cost = 0, p_max_pu = df_cal_solar) #Note, I need a biogas 



###-------------------<<<Add loads>>>-------------------------
'''We are following a process similar to what we did for simple model of last year. For now, we are assuming
california solar data (population weighted, I believe) from renewables.ninja. However, we need load data of 
methane demand. 

Maybe I can make a constant '''


network.add("Load", #Why are there two loads here? Which is the name?
            "load", 
            bus="gas", 
            p_set=gasdf["All_in_one_demand"])


###-------------------<<<Add stores and links to stores>>>---------------------------------
'''We have 
        1) a battery storage connecting to the electricity bus
        2) YES hydrogen storage here
        3) A CO2 store that connects to the methanation process
        4) A CO2 store that connects to the environment
'''

## ------------------CO2----------------------------------------------
'''This CO2 store will connect to the methanation process'''
network.add("Bus", "CO2 compressed store", carrier = "CO2 compressed store")
network.add("Store",
    "CO2 compressed store",
    bus= "CO2 compressed store",
    e_nom_extendable=True,
    e_initial=0,   # assume some initial filling of the CO2 storage just for our minimal example
    e_nom_max=np.inf,   # here you can set a maximum limit for your co2 store
    capital_cost=3,
    carrier="CO2 compressed store")

network.add("Link",
        "To CO2 store",
        bus0 = "CO2 compressed",
        bus1 = "CO2 compressed store")

network.add("Link",
        "From CO2 store",
        bus1 = "CO2 compressed",
        bus0 = "CO2 compressed store")



## ------------------battery--------------------------------------------------------------------
'''This battery connects to the electricity bus'''

network.add("Bus", "battery", carrier = "battery")
network.add("Store",
        "battery",
        bus = "battery",
        e_cyclic = True, #NO FREE LUNCH must return back to original position by end of the year
        e_nom_extendable = True,
        capital_cost = annual_cost("battery storage"))

network.add("Link",
        "battery charger",
        bus0 = "electricity",
        bus1 = "battery",
        carrier = "battery charger",
        efficiency =tech_data.query("technology == 'battery inverter' & parameter == 'efficiency'")['value'].values[0] ** 0.5,
        p_nom_extendable = True,
        capital_cost = annual_cost("battery inverter"))

network.add("Link",
        "battery discharger",
        bus0 = "battery",
        bus1 = "electricity",
        carrier = "battery discharger",
        efficiency = tech_data.query("technology == 'battery inverter' & parameter == 'efficiency'")['value'].values[0] ** 0.5,
        p_nom_extendable = True,
        ) 



## -------------------Hydrogen------------------------------------------------------------
'''This hydrogen store is compressed hydrogen'''
network.add("Bus", "H2 store", carrier = "H2 store")
network.add("Store",
        "H2 store",
        bus = "H2 store",
        e_cyclic = True, #NO FREE LUNCH must return back to original position by end of the year
        e_nom_extendable = True,
        capital_cost = annual_cost("hydrogen storage tank incl. compressor"))#Note, I am not sure whether

network.add("Link",
        "To H2 store",
        bus0 = "H2 compressed",
        bus1 = "H2 store",
        p_nom_extendable = True,
        capital_cost = 0)

network.add("Link",
        "From H2 store",
        bus1 = "H2 compressed",
        bus0 = "H2 store",
        p_nom_extendable = True,
        capital_cost = 0)



## ---------------------gas-----------------------------------------------------
'''The gas store means that it doesn't actually matter how much we need to produce at any given
moment. All that matters is how much is produced at the end of the year'''

network.add("Bus", "gas store", carrier = "gas store")
network.add("Store",
        "gas store",
        bus = "gas store",
        e_cyclic = True, #NO FREE LUNCH must return back to original position by end of the year
        e_nom_extendable = True,
        capital_cost = 0)

network.add("Link",
        "To gas store",
        bus0 = "gas",
        bus1 = "gas store",
        p_nom_extendable = True,
        capital_cost = 0)

network.add("Link",
        "From gas store",
        bus1 = "gas",
        bus0 = "gas store",        
        p_nom_extendable = True,
        capital_cost = 0)
        




# -------CO2_out------------------

#This will connect to CO2 out
network.add("Bus", "CO2 environment", carrier = "CO2 environment")
network.add("Store",
        "CO2 environment",
        bus = "CO2 environment",
        #e_cyclic = True, #NO FREE LUNCH must return back to original position by end of the year
        e_nom_extendable = True,
        capital_cost = 0)

network.add("Link",
        "To CO2 environment",
        bus0 = "CO2 out",
        bus1 = "CO2 environment",
        p_nom_extendable = True,
        capital_cost = 0)

network.add("Link",
        "From CO2 environment",
        bus1 = "CO2 out",
        bus0 = "CO2 environment",
        p_nom_extendable = True,
        capital_cost = 0)


###--------------------<<<Add links between buses>>>------------------------------------------------------
'''Note, there is hydrogen storage! This might require a compressor'''


## ---------------Electricity bus to H2 compressed bus--------------------------
'''This link takes the compression and electrolysis to the H2 compressed bus all in one'''
# -------Electrolysis------------------
network.add("Link",
        "H2 Electrolysis", #in reality, this is both compression and electrolysis
        bus0 = "electricity",
        bus1 = "H2 compressed",
        #as in, electricity is producing hydrogen
        p_nom_extendable = True,
        carrier = "H2 Electrolysis",
        capital_cost = annual_cost("electrolysis") * 2, #We are assuming that the cost of the compressor is equal to the cost of the electrolysis
        efficiency = tech_data.query("technology == 'electrolysis' & parameter == 'efficiency'")['value'].values[0]* 0.993, 
        #This efficiency takes in the efficiency of the compression as well as the efficiency of the electrolysis
        )




# ##--------------------H2 bus to H2 compressed bus-----------------------------------
# network.add("Link",
#         "H2 Compression",
#         bus1 = "H2 compressed",
#         bus0 = "H2", #as in, electricity is producing hydrogen
#         p_nom_extendable = True,
#         carrier = "H2 Compression",
#         capital_cost = annual_cost("electrolysis"), #This is not true right now. What is the cost for compression?
#         efficiency = 0.993 #This 
#         )



## ---------------Biogas bus to CO2 compressed and gas bus--------------------------
network.add("Link",
        "Biogas upgrading", #in reality, this is both compression and electrolysis
        bus0 = "biogas", #as in, electricity is producing hydrogen
        bus1 = "CO2 compressed",
        bus2 = "gas",
        p_nom_extendable = True,
        carrier = "biogas",
        capital_cost = annual_cost("biogas upgrading") * 2, #Does it make a difference that the compressor is only
        #for one of the links? Can we still add
        efficiency = 0.4 * 0.9 * 0.98, #We know that the compressor is 98% efficient. Let's guess that 0.4* 0.9 of the biogas turns into co2
        efficiency2 = 0.6 * 0.9#The rest of the biogas turns into methane, at an efficiency of 0.9

        #This efficiency takes in the efficiency of the compression as well as the efficiency of the electrolysis
        )



##--------------------METHANATION-----------------------------------
'''Note: This requires four links. One from H2, one from CO2, one to a different 
CO2 bus, and one to the converter/methane bus

The C02 in, and the electricity have negative efficiencies

Note: the units here are in kW, right?

It is a bit difficult for me to really understand what these efficiencies mean'''


# -------Methanation ---------------------
# We assume here the Sabatier Process for methanation
sabatier_efficiency = 0.8   # efficiency how much CH4 per H2 input
gas_co2_intensity = 0.2     # CO2 intensity in CH4

#
network.add("Link",
      "methanation",
      bus0="H2 compressed",
      bus1="gas",
      bus2= "CO2_out",
      bus3 = "electricity",
      bus4 = "CO2 compressed",
      carrier="methanation",
      marginal_cost=0,
      capital_cost=annual_cost("methanation"),   # annualised capital costs
      p_nom_extendable=True,
      efficiency=sabatier_efficiency,    # how much CH4 is produced per H2 input. So 0.8 MW Ch4 produced per MW of H2
      efficiency2= 0.01, #I have no idea how many MW CO2 is emitted per MW produced by sabatier. hopefully not much. We are saying 0.01 MW of CO2 per  
      efficiency3 = - sabatier_efficiency * 0.1, #How much electricity is used per 0.8 CH4 produced. Negative. 
      #Let's say that we know that 0.1 MW electricity is used to produce 1 MW CH4. Then, the efficiency is - sabatier efficiency * 0.1
      efficiency4 = - sabatier_efficiency * gas_co2_intensity, #Let's assume that 0.2 MW of compressed CO2 is used per 1 MW of CH4. Negative.
      lifetime=30)



network.lopf(network.snapshots, pyomo=False, solver_name="gurobi")
#%%


# how much H2 is used for Fischer-Tropsch

plt.plot(network.links_t.p0[0:96])
plt.yscale("log")
plt.legend()
plt.show()
# how much CO2 is used for Fischer-Tropsch
network.links_t.p1.plot(title="CH4 produced via sabatier")
# same like multpliying it with the efficiency
(network.links_t.p0*network.links.efficiency).plot(title="CH4 produced via sabatier")
# how much synthetic fuel is produced via Fischer-Tropsch
network.links_t.p2.plot(title="CO2 used for sabatier")
# same like multpliying it with the efficiency2
(network.links_t.p0*network.links.efficiency2).plot(title="CO2 used for sabatier")
# how much CO2 is in the CO2 storage
network.stores_t.e.plot()

#Here we add a link from 



# We need to add 

#network.generators.p_nom_opt