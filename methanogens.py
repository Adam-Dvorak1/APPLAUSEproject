
#The purpose of this file is to make a simple model of methanation. There will be two models:
#one with normal sabatier and one with methanogens (bacteria that produce methane)

#author @Adam Dvorak
#Github: Adam-Dvorak1

#With assistance from Lisa Zeyen

import pypsa
from datetime import datetime
import numpy as np
import os
import pathlib
from buildnetwork import add_buses, add_generators, add_loads, add_stores, add_links, add_methanogen, add_sabatier
from helpers import override_component_attrs
from modifynetwork import change_gasload

#  Lisa: We are going to need multi-links for modelling the CO2 management.
#  Since default setting for links in PyPSA is having only one entry (bus0)
#  and one exit point (bus1) with a given efficieny (efficiency) we have to
#  overwrite some component settings with the following function
def get_relpath(path, home):
        rel_path = os.path.relpath(path, home)
        return rel_path

def new_folder(name):

    dir = pathlib.Path().resolve() #This is the current path
    mypath = str(dir) + "/results/NetCDF" #Going into the NetCDF folder
    curDT = datetime.now()
    version = curDT.strftime("%d_%m_%Y")
    mypath = mypath + "/" + version + "_" + name
    

    if os.path.exists(mypath):
        mypath = mypath + "1"

    os.mkdir(mypath)

    return mypath
    

if __name__ == "__main__":

        ##---<<Variables>>-----
        methanogens = True #whether methanogen or sabatier
        name = "log_cost_sweep" #name of the run, added to date
        # costrange = np.logspace(0, 4, 10)        

        overrides = override_component_attrs("override_component_attrs")

        n = pypsa.Network(override_component_attrs=overrides)


        n = add_buses(n)
        n = add_generators(n)
        n = add_loads(n)
        n = add_stores(n)
        n = add_links(n)

        if methanogens == True:
                n = add_methanogen(n)
                methanation = "methanogen"
        else:
                n = add_sabatier(n)
                methanation = "sabatier"


 
        allpath = new_folder(name)
        homepath = pathlib.Path().resolve()
        rel_path = get_relpath(allpath, homepath)

        for value in costrange:

                n = change_gasload(n, value)
                n.lopf(n.snapshots, pyomo=False, solver_name="gurobi")

                value = round(value, 1)
                mod_path= rel_path + "/" + methanation + str(value) + ".nc"
                
                n.export_to_netcdf(mod_path)
        
