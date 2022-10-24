
#The purpose of this file is to make a simple model of methanation. There will be two models:
#one with normal sabatier and one with methanogens (bacteria that produce methane)

#author @Adam Dvorak
#Github: Adam-Dvorak1

#With assistance from Lisa Zeyen

#%%
import pypsa
import numpy as np
import pandas as pd
from pypsa.descriptors import Dict
from pypsa.components import components, component_attrs
import os
from datetime import datetime
from helpers import override_component_attrs, annual_cost


#  Lisa: We are going to need multi-links for modelling the CO2 management.
#  Since default setting for links in PyPSA is having only one entry (bus0)
#  and one exit point (bus1) with a given efficieny (efficiency) we have to
#  overwrite some component settings with the following function



overrides = override_component_attrs("override_component_attrs")

#%%
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

hours_in_2019 = pd.date_range('2019-01-01T00:00:00','2019-12-31T23:00:00', freq='H') #I changed the date rate from Z
network.set_snapshots(hours_in_2019)

df_cal_solar = pd.read_csv('data/RealCalFlatsSolarCFs.csv', index_col=0)
df_cal_solar.index = pd.to_datetime(df_cal_solar.index)
df_cal_biogas = df_cal_solar['biogas'][[hour.strftime("%Y-%m-%dT%H:%M:%S") for hour in network.snapshots]]
df_cal_solar = df_cal_solar['solar'][[hour.strftime("%Y-%m-%dT%H:%M:%S") for hour in network.snapshots]]



network.add("Generator", "Solar PV", bus="electricity", p_nom_extendable = True, 
    carrier = 'solar', capital_cost = annual_cost('solar-utility'), #Eur/kW/yr
    marginal_cost = 0, p_max_pu = df_cal_solar) #Should we have p_nom_extendable = True? Should we set p_max_pu to a number? Solar has
    #no marginal cost, right?


##-------------------Biogas---------------------------------------------- 
#We want the biogas to be free

network.add("Generator", "Biogas", bus="biogas", p_nom_extendable = True, 
    carrier = 'biogas', capital_cost = 0,
    marginal_cost = 0, p_max_pu = df_cal_biogas) #Note, I need a biogas 



###-------------------<<<Add loads>>>--------------------------------------------------------------
'''We are following a process similar to what we did for simple model of last year. For now, we are assuming
california solar data (population weighted, I believe) from renewables.ninja. However, we need load data of 
methane demand. 

Maybe I can make a constant '''


network.add("Load", #Why are there two loads here? Which is the name?
            "load", 
            bus="gas", 
            p_set=gasdf["All_in_one_demand"])


###-------------------<<<Add stores and links to stores>>>-------------------------------------------
'''We have 
        1) a battery storage connecting to the electricity bus
        2) No hydrogen storage here
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
    capital_cost=0, #Zero CO2 cost
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
        capital_cost = annual_cost("battery storage")) #Eur/kWh/yr
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
        capital_cost = annual_cost("electrolysis") * 2, #We are assuming that the cost of the compressor is equal to the cost of the electrolysis #Eur/kW/yr
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
        capital_cost = 0, #annual_cost("biogas upgrading")/1000 * 2, #Does it make a difference that the compressor is only
        #for one of the links? Can we still add
        efficiency = 0.4 * 0.9 * 0.98, #We know that the compressor is 98% efficient. Let's guess that 0.4* 0.9 of the biogas turns into co2
        efficiency2 = 0.6 * 0.9#The rest of the biogas turns into methane, at an efficiency of 0.9
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

methanogens = False

if methanogens == True:
        network.add("Link",
                "methanogens",
                bus0="H2 compressed",
                bus1="gas",
                bus2= "CO2 out",
                bus3 = "CO2 compressed",
                carrier="methanation",
                marginal_cost=0,
                capital_cost=annual_cost("methanation") * 3,   # annualised capital costs. Assume
                p_nom_extendable=True,
                efficiency=sabatier_efficiency,    # how much CH4 is produced per H2 input. So 0.8 MW Ch4 produced per MW of H2
                efficiency2= 0.01, #I have no idea how many MW CO2 is emitted per MW produced by sabatier. hopefully not much. We are saying 0.01 MW of CO2 per  
                efficiency3 = - sabatier_efficiency * gas_co2_intensity, #Let's assume that 0.2 MW of compressed CO2 is used per 1 MW of CH4. Negative.
                lifetime=30)
else:
        network.add("Link",
                "sabatier",
                bus0="H2 compressed",
                bus1="gas",
                bus2= "CO2 out",
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
curDT = datetime.now()

version = curDT.strftime("_%d_%m_%Y")
if methanogens == True: 
        network.export_to_netcdf("results/NetCDF/methanogen" + version + ".nc")
else:
        network.export_to_netcdf("results/NetCDF/sabatier" + version + ".nc")
#%%


# how much H2 is used for Fischer-Tropsch

# plt.plot(network.links_t.p0[0:96])
# plt.yscale("log")
# plt.show()
# how much CO2 is used for Fischer-Tropsch

# network.links_t.p1.plot(title="CH4 produced via sabatier")
# # same like multpliying it with the efficiency
# (network.links_t.p0*network.links.efficiency).plot(title="CH4 produced via sabatier")
# # how much synthetic fuel is produced via Fischer-Tropsch
# network.links_t.p2.plot(title="CO2 used for sabatier")
# # same like multpliying it with the efficiency2
# (network.links_t.p0*network.links.efficiency2).plot(title="CO2 used for sabatier")
# # how much CO2 is in the CO2 storage
# network.stores_t.e.plot()

# #Here we add a link from 


# network.links_t


# We need to add 

#network.generators.p_nom_opt

#%%
# x = 5
# print (x)
# %%
