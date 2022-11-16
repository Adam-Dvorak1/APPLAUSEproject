import time
from multiprocessing import Pool
import multiprocessing
import itertools
import numpy as np
import pypsa
from buildnetwork import add_buses, add_generators, add_loads, add_stores, add_links, add_methanogen, add_sabatier
from helpers import override_component_attrs

__spec__ = "ModuleSpec(name='builtins', loader=<class'_frozen_importlib.BuiltinImporter'>)"  


# if __name__ == "__main__":
gas_dems = [x for x in np.logspace(0, 4, 10)] #number of kWh 
methanogen_costs = [x for x in np.logspace(-1, 1, 10)]#multiplier to sabatier price




overrides = override_component_attrs("override_component_attrs")

n = pypsa.Network(override_component_attrs=overrides)


n = add_buses(n)
n = add_generators(n)
n = add_loads(n)
n = add_stores(n)
n = add_links(n)

ns = list([n] )


f = list(itertools.product(ns, gas_dems, methanogen_costs))

ns = list([n] )

f = list(itertools.product(ns, f))


# def letsprintf(f1, f2):
#     print("this is the first variable")
#     print(f1)
#     print("this is the second variable")
#     print(f2)

# if __name__ == "__main__":
#     print("this is a test") 
#     with Pool(processes=4) as pool:      
        
#         pool.starmap(letsprintf, f) # evaluate "f(10)" asynchronously in a single process
