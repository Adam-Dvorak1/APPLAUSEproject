import time
from multiprocessing import Pool
import multiprocessing
import itertools
import numpy as np

__spec__ = "ModuleSpec(name='builtins', loader=<class'_frozen_importlib.BuiltinImporter'>)"  



gas_dems = [x for x in np.logspace(0, 4, 10)] #number of kWh 
methanogen_costs = [x for x in np.logspace(-1, 1, 10)]#multiplier to sabatier price

f = list(itertools.product(gas_dems, methanogen_costs))




if __name__ == "__main__":
#     print("this is a test") 
#     with Pool(processes=4) as pool:      
        
#   # start 4 worker processes
#         result = pool.apply_async(f, (10,)) # evaluate "f(10)" asynchronously in a single process
