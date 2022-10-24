#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May 13 20:14:18 2022

minimal example for Methanaion

@author: lisa
"""

import pypsa
import pandas as pd
from pyomo.environ import *
import numpy as np
from pypsa.descriptors import Dict
from pypsa.components import components, component_attrs
import os
import matplotlib.pyplot as plt
#%%

#  We are going to need multi-links for modelling the CO2 management.
#  Since default setting for links in PyPSA is having only one entry (bus0)
#  and one exit point (bus1) with a given efficieny (efficiency) we have to
#  overwrite some component settings with the following function

def override_component_attrs(directory):
    """Tell PyPSA that links can have multiple outputs by
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
    """

    attrs = Dict({k : v.copy() for k,v in component_attrs.items()})

    for component, list_name in components.list_name.items():
        fn = f"{directory}/{list_name}.csv"
        if os.path.isfile(fn):
            overrides = pd.read_csv(fn, index_col=0, na_values="n/a")
            attrs[component] = overrides.combine_first(attrs[component])

    return attrs


#%%##############################################################
########## MAIN #################################################
# Create PyPSA network with new attributes for the links
overrides = override_component_attrs("override_component_attrs")
n = pypsa.Network(override_component_attrs=overrides)
# Set snapshots to the year 2022
snapshots = pd.date_range('2022-01-01', '2023-01-01', freq='1H', closed='left')
n.set_snapshots(snapshots)


# # stored CO2 -------------------------------------------------------
n.add("Bus",
  "co2 stored",
  carrier="co2 stored"
  )

n.add("Store",
      "co2 stored",
      e_nom_extendable=True,
      e_initial=3e5,   # assume some initial filling of the CO2 storage just for our minimal example
      e_nom_max=np.inf,   # here you can set a maximum limit for your co2 store
      capital_cost=20,
      carrier="co2 stored",
      bus="co2 stored"
  )


# bus for natural gas ---------------------------------
n.add("Bus",
  "gas",
  carrier="gas"
  )

# demand for gas
n.add("Load",
      "gas",
      bus="gas",
      p_set=100,
      sign=-1)


# bus for hydrogen -------------------
n.add("Bus",
  "H2",
  carrier="H2"
  )

# assume import of H2 since we do not model green/blue/gray hydrogen production
# in this minimal example
n.add("Generator",
  "H2",
  bus="H2",
  carrier="H2",
  marginal_cost=80,
  p_nom_extendable=True,
  )

# add Methanation ------------------------------
# We assume here the Sabatier Process for methanation
sabatier_efficiency = 0.8   # efficiency how much CH4 per H2 input
gas_co2_intensity = 0.2     # CO2 intensity in CH4

n.add("Link",
      "methanation",
      bus0="H2",
      bus1="gas",
      bus2="co2 stored",
      carrier="methanation",
      marginal_cost=0,
      capital_cost=26818,   # annualised capital costs
      p_nom_extendable=True,
      efficiency=sabatier_efficiency,    # how much CH4 is produced per H2 input
      efficiency2=-sabatier_efficiency * gas_co2_intensity, # how much CO2 is used per CH4 output
      lifetime=30)

n.lopf(pyomo=False, solver_name="gurobi")
#%%


# how much H2 is used for Fischer-Tropsch
n.links_t.p0.plot(title="H2 used for methanation")
# how much CO2 is used for Fischer-Tropsch
n.links_t.p1.plot(title="CH4 produced via methanation")
# same like multpliying it with the efficiency
(n.links_t.p0*n.links.efficiency).plot(title="CH4 produced via methanation")
# how much synthetic fuel is produced via Fischer-Tropsch
n.links_t.p2.plot(title="CO2 used for methanation")
# same like multpliying it with the efficiency2
(n.links_t.p0*n.links.efficiency2).plot(title="CO2 used for methanation")
# how much CO2 is in the CO2 storage
n.stores_t.e.plot()



# ##--------------------Hydrogen bus------------------------------------
'''Note I don't think I actually need links to the hydrogen storage'''
# # -------H2 to H2 storage------------------

# network.add("Link",
#         "H2 to storage",
#         bus1 = "H2",
#         bus0 = "electricity bus",
#         p_nom_extendable = True,
#         carrier = "H2 Electrolysis",
#         efficiency = 0.66,
#         capital_cost = cost_electro * 0.66 #EUR/MW_el, making sure to multiply by efficiency
#         )

# # -------Fuel cell from H2 storage------------------

# h2fueleff = tech_data.query("technology == 'fuel cell' & parameter == 'efficiency'")['value'].values[0] 
# network.add("Link",
#         "H2 Fuel Cell",
#         bus0 = "H2",
#         bus1 = "electricity bus",
#         p_nom_extendable = True,
#         carrier = "H2 Fuel Cell",
#         efficiency =h2fueleff,
#         capital_cost = annual_cost("fuel cell") * h2fueleff)