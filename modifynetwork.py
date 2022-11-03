import pandas as pd

def change_gasload(network, multiplier):
    '''There are two loads, one for gas demand, and one ginormous grid demand.
    The grid demand is assumed to be constant and huge. The gas load is assumed to be
    taken at the end of the year. The default for the "all_in_one_demand" for the 
    applegas csv is 3kWh per hour, taken at the last hour of the year. It works because
    there is a free storage that can take all of the gas until the end of the year--this way
    we answer the question "we want this amount of gas per year, what is the optimal config"'''
    gasdf = pd.read_csv('data/AppleGas.csv', index_col = 0)
    gasdf.index = pd.to_datetime(gasdf.index)

    network.remove("Load", "Gas Load")

    network.add("Load", #Why are there two loads here? Which is the name?
        "Gas Load", 
        bus="gas", 
        p_set=gasdf["All_in_one_demand"]/3 * multiplier) #Now

    return network