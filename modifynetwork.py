import pandas as pd
import datetime
from helpers import annual_cost
import numpy as np
from buildnetwork import add_links



def change_gasload(network, multiplier):
    '''There are two loads, one for gas demand, and one ginormous grid demand.
    The grid demand is assumed to be constant and huge. The gas load is assumed to be
    taken at the end of the year. The default for the "all_in_one_demand" for the 
    applegas csv is 3kWh per hour, taken at the last hour of the year. It works because
    there is a free storage that can take all of the gas until the end of the year--this way
    we answer the question "we want this amount of gas per year, what is the optimal config"'''
    gasdf = pd.read_csv('data/gasdem_csvs/2019AppleGas.csv', index_col = 0)
    gasdf.index = pd.to_datetime(gasdf.index)

    network.remove("Load", "Gas Load")

    network.add("Load", #Why are there two loads here? Which is the name?
        "Gas Load", 
        bus="gas", 
        p_set=gasdf["All_in_one_demand"]/3 * multiplier) #Now

    return network

def remove_links(network):
    '''
    3 April 2023

    I am really struggling trying to find the reason for why the solar is not working. Maybe it is the fact
    that there is no link? So let's remove some links and add them again'''

    network.mremove("Link", ['H2 Electrolysis', 'High to low voltage', 
                             "Solar system to electricity", 'Biogas upgrading'])
    
    return network

def zeroload(network):
    '''25 May 2023
    As I sometimes forget to add in 0 gas demand when doing a mindf, I am finally making a funciton for it'''

    gasdf = pd.read_csv('data/gasdem_csvs/2019AppleGas.csv', index_col = 0)
    gasdf.index = pd.to_datetime(gasdf.index)

    network.remove("Load", 'Gas Load')
    network.add("Load", #Why are there two loads here? Which is the name?
        "Gas Load", 
        bus="gas", 
        p_set=gasdf["All_in_one_demand"] * 0) 
    
    return network

def add_generators_sol_yrs(network, year):

    '''
    21 February 2023
    
    We are adding functionality to do similar tests to 
    The purpose of this function is to be able to do a sensitivity analysis based on the 
    year of electricity/wind data at 'cal flats'. So, this is not present in the base case,
    but it is present when modifying the network.
    
    It takes a string for year. 
    
    It is almost a copy of add_generators in buildnetwork.py'''
    gridpresent = False #if the grid is not present already, then we don't want to add it back in
    
    network.remove("Generator", "Biogas")
    
    network.remove("Generator", "Solar PV")


    if 'Grid' in network.generators.index:
        network.remove("Generator", 'Grid')

        gridpresent = True


    
    hours_in_year = pd.date_range(year + '-01-01T00:00:00', year + '-12-31T23:00:00', freq='H') #I changed the date rate from Z
    network.set_snapshots(hours_in_year)

    #We are editing this to see whether it has to do with the csv
    df_cal_solar = pd.read_csv('data/final_solar_csvs/PVGISRealCalFlatsSolarCFs_' + year + '.csv', index_col=0) #Solar CFs taken from renewables.ninja and google maps location of California Flats (35.854394, -120.304389), though renewables.ninja only does 3 decimal points
    df_cal_solar.index = pd.to_datetime(df_cal_solar.index)
    df_cal_biogas = df_cal_solar['biogas'][[hour.strftime("%Y-%m-%dT%H:%M:%S") for hour in network.snapshots]] #This is only assuming a constant generator, which I added to the original data from renewables.ninja
    df_cal_solar = df_cal_solar['solar'][[hour.strftime("%Y-%m-%dT%H:%M:%S") for hour in network.snapshots]] #capacity factor time series 

    if gridpresent == True:
        gridprice = pd.read_csv("data/elecprice_csvs/" + year + "UTCCAISOprice.csv", index_col = 0) #From http://www.energyonline.com/Data/GenericData.aspx?DataId=20, which is taken from CAISO. Units of /MWh
        gridprice.index = pd.to_datetime(gridprice.index)
        gridprice = gridprice['price'][[hour.strftime("%Y-%m-%d %H:%M:%S") for hour in network.snapshots]]
        gridprice = gridprice/1000 #Before, I used to divide by 100. But I believe that I should have divided by 1000, because we want per kWh, and we had per MWh 

        if int(year) % 4 != 0:
            gridgen = pd.DataFrame(index = range (8760))
        else:
            gridgen = pd.DataFrame(index = range(8784))

        gridgen = gridgen.set_index(hours_in_year)
        gridgen['grid'] = 1#in kW, so 100GW


        network.add("Generator", "Grid", bus = 'grid', p_nom = 100000000,#100 GW. The capacity is for free. However, we still pay marginal cost
            carrier = "grid", capital_cost = 0, marginal_cost = gridprice, p_max_pu = gridgen['grid'])#The datafile gives US cents/kWh. I wanted dollars (or euros) per kWh.     # This is using 2019 (UTC) data from CAISO, LCG consulting.Prices are in c/kWh

    


    network.add("Generator", "Solar PV", bus="local elec",p_nom_extendable = True,#We can't put p_nom here because p_nom is for free. We need p_nom_extendable to be True, and then set a max
        carrier = 'solar', capital_cost = 0, #Eur/kW/yr
        marginal_cost = 0, p_nom = 130000, p_nom_max = 130000, p_max_pu = df_cal_solar) #Max installation of 130 MW, which is Apple's share of Cal Flats https://www.apple.com/newsroom/2021/03/apple-powers-ahead-in-new-renewable-energy-solutions-with-over-110-suppliers/

    network.add("Generator", "Biogas", bus="biogas", p_nom_extendable = True, 
        carrier = 'biogas', capital_cost = 0,
        marginal_cost = 0, p_max_pu = df_cal_biogas) # In reality, there is a marginal cost for biogas. What is it? 


    return network

def add_grid_solar_yrs(network, yeargrid, yearsolar):

    '''
    27 June 2023
    
    The purpose of this function is to compare the combinations of grid and solar years. It will
    use the year of the grid for the real year of the network'''

    network.remove("Generator", "Biogas")
    
    network.remove("Generator", "Solar PV")

    network.remove("Generator", 'Grid')

    
    hours_in_fullyear = pd.date_range(yeargrid + '-01-01T00:00:00', yeargrid + '-12-31T23:00:00', freq='H') #I changed the date rate from Z
    

    gridprice = pd.read_csv("data/elecprice_csvs/" + yeargrid + "UTCCAISOprice.csv", index_col = 0) #From http://www.energyonline.com/Data/GenericData.aspx?DataId=20, which is taken from CAISO. Units of /MWh
    gridprice.index = hours_in_fullyear
    if yeargrid == '2020':
        gridprice = gridprice[(np.in1d(gridprice.index.date, [datetime.date(2020, 2, 29)], invert = True))]

    
    

    hours_in_year = gridprice.index #The purpose of this is because we can easily exclude the leap day by removing it from the dataframe. This also needs to be done to the loads
    # print(hours_in_year)
    network.set_snapshots(hours_in_year)

    gridprice = gridprice['price'][[hour.strftime("%Y-%m-%d %H:%M:%S") for hour in network.snapshots]]
    gridprice = gridprice/1000 #Before, I used to divide by 100. But I believe that I should have divided by 1000, because we want per kWh, and we had per MWh 




    gridgen = pd.DataFrame(index = range(8760))
    gridgen = gridgen.set_index(hours_in_year)
    gridgen['grid'] = 1#in kW, so 100GW


    network.add("Generator", "Grid", bus = 'grid', p_nom = 100000000,#100 GW. The capacity is for free. However, we still pay marginal cost
        carrier = "grid", capital_cost = 0, marginal_cost = gridprice, p_max_pu = gridgen['grid'])#The datafile gives US cents/kWh. I wanted dollars (or euros) per kWh.     # This is using 2019 (UTC) data from CAISO, LCG consulting.Prices are in c/kWh


    

    #We are editing this to see whether it has to do with the csv
    df_cal_solar = pd.read_csv('data/final_solar_csvs/PVGISRealCalFlatsSolarCFs_' + yearsolar + '.csv', index_col=0) #Solar CFs taken from renewables.ninja and google maps location of California Flats (35.854394, -120.304389), though renewables.ninja only does 3 decimal points
    hours_in_solaryear = pd.date_range(yearsolar + '-01-01T00:00:00', yearsolar + '-12-31T23:00:00', freq='H') #We actually need this repeated from yeargrid because the years are different
    df_cal_solar.index = hours_in_solaryear #Converts to a datetimes series
    if yearsolar == '2020': #Cuts year 2020 down
        df_cal_solar = df_cal_solar[(np.in1d(df_cal_solar.index.date, [datetime.date(2020, 2, 29)], invert = True))] #Remember, we don't care about the year of the original once we have the data. We need it to be the same year as the others

    df_cal_solar.index = hours_in_year #Now this should be the right size and the same year as grid, no matter what

    df_cal_biogas = df_cal_solar['biogas'][[hour.strftime("%Y-%m-%dT%H:%M:%S") for hour in network.snapshots]] #This is only assuming a constant generator, which I added to the original data from renewables.ninja
    df_cal_solar = df_cal_solar['solar'][[hour.strftime("%Y-%m-%dT%H:%M:%S") for hour in network.snapshots]] #capacity factor time series 



    network.add("Generator", "Solar PV", bus="local elec",p_nom_extendable = True,#We can't put p_nom here because p_nom is for free. We need p_nom_extendable to be True, and then set a max
        carrier = 'solar', capital_cost = 0, #Eur/kW/yr
        marginal_cost = 0, p_nom = 130000, p_nom_max = 130000, p_max_pu = df_cal_solar) #Max installation of 130 MW, which is Apple's share of Cal Flats https://www.apple.com/newsroom/2021/03/apple-powers-ahead-in-new-renewable-energy-solutions-with-over-110-suppliers/

    network.add("Generator", "Biogas", bus="biogas", p_nom_extendable = True, 
        carrier = 'biogas', capital_cost = 0,
        marginal_cost = 0, p_max_pu = df_cal_biogas) # In reality, there is a marginal cost for biogas. What is it? 


    return network



def add_generators_sol_spain(network):

    '''
    21 February 2023
    
    We are adding functionality to do similar tests to 
    The purpose of this function is to be able to do a sensitivity analysis based on the 
    year of electricity/wind data at 'cal flats'. So, this is not present in the base case,
    but it is present when modifying the network.
    
    It takes a string for year. 
    
    It is almost a copy of add_generators in buildnetwork.py'''
    gridpresent = False #if the grid is not present already, then we don't want to add it back in
    solpresent = False
    if "Solar PV" in network.generators.index:
        network.remove("Generator", "Biogas")
        network.remove("Generator", "Solar PV")
        solpresent = True


    if 'Grid' in network.generators.index:
        network.remove("Generator", 'Grid')

        gridpresent = True


    
    hours_in_year = pd.date_range('2019-01-01T00:00:00', '2019-12-31T23:00:00', freq='H') #I changed the date rate from Z
    network.set_snapshots(hours_in_year)

    #We are editing this to see whether it has to do with the csv
    df_cal_solar = pd.read_csv('data/Spain/PVGISRealSpainSolarCFS_2019.csv', index_col=0) #Solar CFs taken from renewables.ninja and google maps location of California Flats (35.854394, -120.304389), though renewables.ninja only does 3 decimal points
    df_cal_solar.index = pd.to_datetime(df_cal_solar.index)
    df_cal_biogas = df_cal_solar['biogas'][[hour.strftime("%Y-%m-%dT%H:%M:%S") for hour in network.snapshots]] #This is only assuming a constant generator, which I added to the original data from renewables.ninja
    df_cal_solar = df_cal_solar['solar'][[hour.strftime("%Y-%m-%dT%H:%M:%S") for hour in network.snapshots]] #capacity factor time series 

    if gridpresent == True:
        gridprice = pd.read_csv("data/Spain/2019UTCDayAheadPrice.csv", index_col = 0) #From http://www.energyonline.com/Data/GenericData.aspx?DataId=20, which is taken from CAISO. Units of /MWh
        gridprice.index = pd.to_datetime(gridprice.index)
        gridprice = gridprice['price'][[hour.strftime("%Y-%m-%d %H:%M:%S") for hour in network.snapshots]]
        gridprice = gridprice/1000 #Before, I used to divide by 100. But I believe that I should have divided by 1000, because we want per kWh, and we had per MWh 
        gridprice = gridprice * 1.07 # The csv is in euro, so we need to convert to dollars. Assume 1.07 dollars = 1 euro
        gridgen = pd.DataFrame(index = range (8760))

        gridgen = gridgen.set_index(hours_in_year)
        gridgen['grid'] = 1#in kW, so 100GW


        network.add("Generator", "Grid", bus = 'grid', p_nom = 100000000,#100 GW. The capacity is for free. However, we still pay marginal cost
            carrier = "grid", capital_cost = 0, marginal_cost = gridprice, p_max_pu = gridgen['grid'])#The datafile gives US cents/kWh. I wanted dollars (or euros) per kWh.     # This is using 2019 (UTC) data from CAISO, LCG consulting.Prices are in c/kWh

    if solpresent == True:
        if gridpresent == True:
    #dispatch, use for gridsolar and mindf
            network.add("Generator", "Solar PV", bus="local elec",p_nom_extendable = True,#We can't put p_nom here because p_nom is for free. We need p_nom_extendable to be True, and then set a max
                carrier = 'solar', capital_cost = 0, #USD/kW/yr
                marginal_cost = 0, p_nom = 130000, p_nom_max = 130000, p_max_pu = df_cal_solar) #Max installation of 130 MW, which is Apple's share of Cal Flats https://www.apple.com/newsroom/2021/03/apple-powers-ahead-in-new-renewable-energy-solutions-with-over-110-suppliers/
        if gridpresent == False:
            network.add("Generator", "Solar PV", bus="local elec",p_nom_extendable = True,#We can't put p_nom here because p_nom is for free. We need p_nom_extendable to be True, and then set a max
                carrier = 'solar', capital_cost = annual_cost('solar-utility-eur'), #USD/kW/yr
                marginal_cost = 0,  p_nom_max = 130000, p_max_pu = df_cal_solar) #Max installation of 130 MW, which is Apple's share of Cal Flats https://www.apple.com/newsroom/2021/03/apple-powers-ahead-in-new-renewable-energy-solutions-with-over-110-suppliers/
        network.add("Generator", "Biogas", bus="biogas", p_nom_extendable = True, 
            carrier = 'biogas', capital_cost = 0,
            marginal_cost = 0, p_max_pu = df_cal_biogas) # In reality, there is a marginal cost for biogas. What is it? 


    return network


def add_generators_wind_yrs(network, year):

    '''
    21 February 2023
    
    We are adding functionality to do similar tests to 
    The purpose of this function is to be able to do a sensitivity analysis based on the 
    year of electricity/wind data at 'cal flats'. So, this is not present in the base case,
    but it is present when modifying the network.
    
    It takes a string for year. 
    
    It is almost a copy of add_generators in buildnetwork.py
    
    Note: if you want to use this function again, you will need to change the capacity'''
    gridpresent = False #if the grid is not present already, then we don't want to add it back in
    network.remove("Generator", "Biogas")
    network.remove("Generator", 'Onshore wind')
    if 'Grid' in network.generators.index:
       
        network.remove("Generator", 'Grid')
        gridpresent = True

    
    
    hours_in_year = pd.date_range(year + '-01-01T00:00:00', year + '-12-31T23:00:00', freq='H') #I changed the date rate from Z
    network.set_snapshots(hours_in_year)

    df_cal_solar = pd.read_csv('data/final_wind_csvs/RealCalFlatsWindCFs_' + year + '.csv', index_col=0) #Solar CFs taken from renewables.ninja and google maps location of California Flats (35.854394, -120.304389), though renewables.ninja only does 3 decimal points
    df_cal_solar.index = pd.to_datetime(df_cal_solar.index)
    df_cal_biogas = df_cal_solar['biogas'][[hour.strftime("%Y-%m-%dT%H:%M:%S") for hour in network.snapshots]] #This is only assuming a constant generator, which I added to the original data from renewables.ninja
    df_cal_solar = df_cal_solar['wind'][[hour.strftime("%Y-%m-%dT%H:%M:%S") for hour in network.snapshots]] #capacity factor time series 

    if gridpresent == True:
        gridprice = pd.read_csv("data/elecprice_csvs/" + year + "UTCCAISOprice.csv", index_col = 0) #From http://www.energyonline.com/Data/GenericData.aspx?DataId=20, which is taken from CAISO. Units of /MWh
        gridprice.index = pd.to_datetime(gridprice.index)
        gridprice = gridprice['price'][[hour.strftime("%Y-%m-%d %H:%M:%S") for hour in network.snapshots]]
        gridprice = gridprice/1000 #Before, I used to divide by 100. But I believe that I should have divided by 1000, because we want per kWh, and we had per MWh 

        if int(year) % 4 != 0:
            gridgen = pd.DataFrame(index = range (8760))
        else:
            gridgen = pd.DataFrame(index = range(8784))

        gridgen = gridgen.set_index(hours_in_year)
        gridgen['grid'] = 1 #in kW, so 100GW
       
        network.add("Generator", "Grid", bus = 'grid', p_nom = 100000000,#100 GW. The capacity is for free. However, we still pay marginal cost
            carrier = "grid", capital_cost = 0, marginal_cost = gridprice, p_max_pu = gridgen['grid'])#The datafile gives US cents/kWh. I wanted dollars (or euros) per kWh.     # This is using 2019 (UTC) data from CAISO, LCG consulting.Prices are in c/kWh

    


    network.add("Generator", "Onshore wind", bus="local elec",p_nom_extendable = True,#We can't put p_nom here because p_nom is for free. We need p_nom_extendable to be True, and then set a max
        carrier = 'wind', capital_cost = 0, #Eur/kW/yr
        marginal_cost = 0, p_nom = 130000, p_nom_max = 130000, p_max_pu = df_cal_solar) #Max installation of 130 MW, which is Apple's share of Cal Flats https://www.apple.com/newsroom/2021/03/apple-powers-ahead-in-new-renewable-energy-solutions-with-over-110-suppliers/

    

    network.add("Generator", "Biogas", bus="biogas", p_nom_extendable = True, 
        carrier = 'biogas', capital_cost = 0,
        marginal_cost = 0, p_max_pu = df_cal_biogas) # In reality, there is a marginal cost for biogas. What is it? 


    return network


def add_wind(network):
    '''
    15 June 2023




    '''
    hours_in_year = pd.date_range('2019-01-01T00:00:00', '2019-12-31T23:00:00', freq='H') #I changed the date rate from Z
    network.set_snapshots(hours_in_year)

    df_cal_wind = pd.read_csv('data/final_wind_csvs/AltamontPassWindCFs_2019.csv', index_col=0) #Solar CFs taken from renewables.ninja and google maps location of California Flats (35.854394, -120.304389), though renewables.ninja only does 3 decimal points
    df_cal_wind.index = pd.to_datetime(df_cal_wind.index)
    df_cal_wind = df_cal_wind['wind'][[hour.strftime("%Y-%m-%dT%H:%M:%S") for hour in network.snapshots]] #capacity factor time series 

    network.add("Generator", "Onshore wind", bus="local elec",p_nom_extendable = True,
        carrier = 'wind', capital_cost = 0, #Eur/kW/yr
        marginal_cost = 0, p_nom = 101023, p_nom_max = 101023, p_max_pu = df_cal_wind) #Assuming that 




    return network




def add_loads_yrs(network, year):
    network.remove("Load", 'Gas Load')
    gridpres = False
    if "Grid" in network.generators.index:
        network.remove("Load", 'Grid Load')
        gridpres = True

    
    gasdf = pd.read_csv('data/gasdem_csvs/' + year + 'AppleGas.csv', index_col = 0)
    gasdf.index = pd.to_datetime(gasdf.index)

    network.add("Load", #Why are there two loads here? Which is the name?
        "Gas Load", 
        bus="gas", 
        p_set=gasdf["All_in_one_demand"])

    if gridpres == True:
        network.add("Load", 
            "Grid Load", 
            bus="grid", 
            p_set=gasdf["Constant_MW_methane"] * 300)#Assuming 3 GW of demand from the grid
        
    return network

def add_loads_gridsolar_yrs(network, year):
    '''
    27 June 2023
    
    The purpose of this is that when we are doing the gridsolar years variation, 
    we may want to put a leapyear dataset with a non leapyear dataset. So, everything
    is 8760 in length (2020 is minus Feb 29). This is for the loads as well'''
    network.remove("Load", 'Gas Load')
    network.remove("Load", 'Grid Load')


    
    gasdf = pd.read_csv('data/gasdem_csvs/' + year + 'AppleGas.csv', index_col = 0)
    gasdf.index = pd.to_datetime(gasdf.index)
    if year == 2020:
        gasdf = gasdf[(np.in1d(gasdf.index.date, [datetime.date(2020, 2, 29)], invert = True))]

    network.add("Load", #Why are there two loads here? Which is the name?
        "Gas Load", 
        bus="gas", 
        p_set=gasdf["All_in_one_demand"] * 0) #this is to make a mindf run


    network.add("Load", 
        "Grid Load", 
        bus="grid", 
        p_set=gasdf["Constant_MW_methane"] * 300)#Assuming 3 GW of demand from the grid
        
    return network
'''These two functions are for an experiment on 21 November, to see what happens to the grid
and the solar if the other is removed. That being said, the solar will need to be expanded'''




def add_sol_cost(network):
    '''26 May 2023
    
    Since the only solar scenario prices do not make sense if we only force in 130 MW, we change it
    
    Now has cost. P_nom is 0'''

    network.generators.loc['Solar PV', 'capital_cost'] = annual_cost('solar-utility')

    network.generators.loc['Solar PV', 'p_nom'] = 0

    return network

def add_wind_cost(network):
    '''17 July 2023
    
    Since the only solar scenario prices do not make sense if we only force in 130 MW, we change it
    
    Now has cost. P_nom is 0'''

    network.generators.loc['Onshore wind', 'capital_cost'] = annual_cost('onwind')

    network.generators.loc['Onshore wind', 'p_nom'] = 0

    return network


def remove_grid(network):

    network.remove("Load", "Grid Load")
    network.remove("Generator", "Grid")

    #We also need to change the p_nom_max, as now solar needs to supply everything for the methane
    # if 'Solar PV' in network.generators.index:
    #     network.generators.loc["Solar PV", "p_nom_max"] = np.inf
    # elif 'Onshore wind' in network.generators.index:
    #     network.generators.loc['Onshore wind', 'p_nom_max'] = np.inf

    return network


def remove_solar(network):


    network.remove("Generator", "Solar PV")


    return network

def change_loads_costs(network, sweep, sweep_mult, megen_mult):
    '''This function used to change the gasload, in addition to the methanogen cost. 
    Now, it still changes the methanogen cost, but it also can sweep the electrolyzer cost'''



    network.links.loc['methanogens', 'capital_cost'] = annual_cost("methanation") * megen_mult

    if sweep == "electrolyzer":
        network.links.loc['H2 Electrolysis', 'capital_cost'] = annual_cost("electrolysis") * sweep_mult
    
    elif sweep == 'battery':
        network.stores.loc['battery', 'capital_cost'] = annual_cost('battery storage') * sweep_mult
    
    elif sweep == 'H2 store':
        network.stores.loc['H2 store', 'capital_cost'] = annual_cost('hydrogen storage tank type 1 including compressor') * sweep_mult


    elif sweep == 'grid-sol-year':

        if 'Solar PV' in network.generators.index: #This needs 
            network = add_grid_solar_yrs(network, sweep_mult[0], sweep_mult[1]) #We cannot actually use this particular function for grid-sol-year because 
        network = add_loads_gridsolar_yrs(network, sweep_mult[0])

    elif sweep == 'grid_inverter':
        network.links.loc['High to low voltage', 'p_nom_max'] = 14667 * sweep_mult

    elif sweep == "gi_cost":
        network.links.loc['High to low voltage', 'capital_cost'] = annual_cost('electricity grid connection') * sweep_mult

    elif sweep == 'spain_electrolyzer':
        # network = add_generators_sol_spain(network)
        network.links.loc['H2 Electrolysis', 'capital_cost'] = annual_cost("electrolysis") * sweep_mult
    
    # elif sweep == ''


        

    return network






def solve_network(network, sweep, sweep_mult, megen_mult):

    n = change_loads_costs(network, sweep, sweep_mult, megen_mult)

        
    n.lopf(n.snapshots, 
             pyomo=False,
             solver_name='gurobi')


    return n


def to_netcdf(network, sweep, sweep_mult, megen_mult, path):
    n = solve_network(network, sweep, sweep_mult, megen_mult)

   # With all the talk of multipliers, in reality gas_mult is the average gas demand in kW, 
   #the megen_mult becomes modified
    
    #The real cost is not rounded--this is only for documentation and plotting

    if sweep == "electrolyzer":
        sweep_mult = sweep_mult * annual_cost('electrolysis')
        sweep_mult = round (sweep_mult)


    if sweep != 'grid-sol-year':
        path = path + "/" + sweep + f"_{sweep_mult}_megen_cost_{megen_mult}.nc"
    else:
        path = path + '/grid'  + f"_{sweep_mult[0]}_sol_{sweep_mult[1]}.nc"# For el-sol-year, we don't actually care about the methanation sweep
    
    n.export_to_netcdf(path)

