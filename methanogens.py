
#The purpose of this file is to make a simple model of methanation. There will be two models:
#one with normal sabatier and one with methanogens (bacteria that produce methane)

#author @Adam Dvorak
#Github: Adam-Dvorak1

#With assistance from Lisa Zeyen

import pypsa
from datetime import datetime
from plotters import override_component_attrs
from buildnetwork import add_buses, add_generators, add_loads, add_stores, add_links, add_methanogen, add_sabatier


#  Lisa: We are going to need multi-links for modelling the CO2 management.
#  Since default setting for links in PyPSA is having only one entry (bus0)
#  and one exit point (bus1) with a given efficieny (efficiency) we have to
#  overwrite some component settings with the following function


if __name__ == "__main__":

        overrides = override_component_attrs("override_component_attrs")

        n = pypsa.Network(override_component_attrs=overrides)

        methanogens = False

        n = add_buses(n)
        n = add_generators(n)
        n = add_loads(n)
        n = add_stores(n)
        n = add_links(n)

        if methanogens == True:
                n = add_methanogen(n)
        else:
                n = add_sabatier(n)

        n.lopf(n.snapshots, pyomo=False, solver_name="gurobi")
        
        curDT = datetime.now()
        version = curDT.strftime("_%d_%m_%Y")

        if methanogens == True: 
                n.export_to_netcdf("results/NetCDF/methanogen" + version + ".nc")
        else:
                n.export_to_netcdf("results/NetCDF/sabatier" + version + ".nc")
