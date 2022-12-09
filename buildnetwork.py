'''The goal of this program is to provide functions that allow for the building of the network'''
import pandas as pd
from helpers import annual_cost



def add_buses(network):
    '''This function takes an existing network and adds the buses'''
    network.add("Bus","electricity", carrier = "electricity")

    network.add("Bus","local elec", carrier = "local elec")

    network.add("Bus", "H2 compressed", carrier  = "H2 compressed")

    network.add("Bus", "gas", carrier = "gas")

    network.add("Bus", "CO2 out", carrier = "co2 released") 

    network.add("Bus", "biogas", carrier = "biogas") 

    network.add("Bus", "CO2 compressed", carrier = "co2 compressed") #Note, CO2 compressed is actually only CO2 for the methanogen case 

    network.add("Bus", "grid", carrier = "grid")

    return network


def add_generators(network):
    '''There are three generators: solar, biogas, and grid. The grid is huge and has a 
    marginal cost.
    This also sets the network snapshots'''
    hours_in_2019 = pd.date_range('2019-01-01T00:00:00','2019-12-31T23:00:00', freq='H') #I changed the date rate from Z
    network.set_snapshots(hours_in_2019)

    df_cal_solar = pd.read_csv('data/RealCalFlatsSolarCFs.csv', index_col=0)
    df_cal_solar.index = pd.to_datetime(df_cal_solar.index)
    df_cal_biogas = df_cal_solar['biogas'][[hour.strftime("%Y-%m-%dT%H:%M:%S") for hour in network.snapshots]]
    df_cal_solar = df_cal_solar['solar'][[hour.strftime("%Y-%m-%dT%H:%M:%S") for hour in network.snapshots]] #capacity factor time series


    gridprice = pd.read_csv("data/2019UTCCAISOprice.csv", index_col = 0)
    gridprice.index = pd.to_datetime(gridprice.index)
    gridprice = gridprice['price'][[hour.strftime("%Y-%m-%d %H:%M:%S") for hour in network.snapshots]]
    gridprice = gridprice/100


    gridgen = pd.DataFrame(index = range (8760))
    gridgen = gridgen.set_index(hours_in_2019)
    gridgen['grid'] = 1 #in kW, so 100GW


    network.add("Generator", "Solar PV", bus="local elec",p_nom_extendable = True,#We can't put p_nom here because p_nom is for free. We need p_nom_extendable to be True, and then set a max
        carrier = 'solar', capital_cost = annual_cost('solar-utility'), #Eur/kW/yr
        marginal_cost = 0, p_nom_max = 130000, p_max_pu = df_cal_solar) #

    network.add("Generator", "Biogas", bus="biogas", p_nom_extendable = True, 
        carrier = 'biogas', capital_cost = 0,
        marginal_cost = 0, p_max_pu = df_cal_biogas) 

    network.add("Generator", "Grid", bus = 'grid', p_nom = 100000000,#100 GW. The capacity is for free. However, we still pay marginal cost
        carrier = "grid", capital_cost = 0, marginal_cost = gridprice, p_max_pu = gridgen['grid'])#The datafile gives US cents/kWh. I wanted dollars (or euros) per kWh.     # This is using 2019 (UTC) data from CAISO, LCG consulting.Prices are in c/kWh

    
    return network


def add_loads(network):
    '''There are two loads, one for gas demand, and one ginormous grid demand.
    The grid demand is assumed to be constant and huge. The gas load is assumed to be
    taken at the end of the year. The default for the "all_in_one_demand" for the 
    applegas csv is 3kWh per hour, taken at the last hour of the year. It works because
    there is a free storage that can take all of the gas until the end of the year--this way
    we answer the question "we want this amount of gas per year, what is the optimal config"'''
    gasdf = pd.read_csv('data/AppleGas.csv', index_col = 0)
    gasdf.index = pd.to_datetime(gasdf.index)

    network.add("Load", #Why are there two loads here? Which is the name?
        "Gas Load", 
        bus="gas", 
        p_set=gasdf["All_in_one_demand"])

    network.add("Load", 
        "Grid Load", 
        bus="grid", 
        p_set=gasdf["Constant_MW_methane"] * 1000000)

    return network


def add_stores(network):
    '''This adds three stores: a battery, for the solar generator; a gas store, for the load;
    and a CO2 environment, to capture the CO2 '''

    tech_data = pd.read_csv("data/costs_2025.csv")

    ## ------------------battery---------------------------
    network.add("Bus", "battery", carrier = "battery")
    network.add("Store",
        "battery",
        bus = "battery",
        e_cyclic = True, #NO FREE LUNCH must return back to original position by end of the year
        e_nom_extendable = True,
        e_nom_max = 240000,
        capital_cost = annual_cost("battery storage")) #Eur/kWh/yr
    network.add("Link",
        "battery charger",
        bus0 = "local elec",
        bus1 = "battery",
        carrier = "battery charger",
        efficiency =tech_data.query("technology == 'battery inverter' & parameter == 'efficiency'")['value'].values[0] ** 0.5,
        p_nom_extendable = True,
        capital_cost = annual_cost("battery inverter"))
    network.add("Link",
        "battery discharger",
        bus0 = "battery",
        bus1 = "local elec",
        carrier = "battery discharger",
        efficiency = tech_data.query("technology == 'battery inverter' & parameter == 'efficiency'")['value'].values[0] ** 0.5,
        p_nom_extendable = True,
        ) 

    ## ---------------------gas-----------------------------
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


    ## -------CO2 environment--------------------------
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

    return network


def add_links(network):
    '''This adds links that are not methanogenesis or connecting to stores:
    electrolysis, high to low voltage electricity, solar to electricity, biogas'''
    
    tech_data = pd.read_csv("data/costs_2025.csv")

    ## ---------------Electrolysis--------------------------
    network.add("Link",
        "H2 Electrolysis", #in reality, this is both compression and electrolysis
        bus0 = "electricity",
        bus1 = "H2 compressed",
        #as in, electricity is producing hydrogen
        p_nom_extendable = True,
        carrier = "H2 Electrolysis",
        capital_cost = annual_cost("electrolysis"), #We are assuming that the cost of the compressor is equal to the cost of the electrolysis #Eur/kW/yr
        efficiency = tech_data.query("technology == 'electrolysis' & parameter == 'efficiency'")['value'].values[0], 
        #This efficiency takes in the efficiency of the compression as well as the efficiency of the electrolysis
        )


    ## ---------------Electricity bus to Grid bus--------------------------
    '''This combination of links serves as the transformer to and from the local electricity
    grid and the global electricity grid'''

    network.add("Link",
        "High to low voltage", #in reality, this is both compression and electrolysis
        bus0 = "grid",
        bus1 = "electricity",
        #as in, electricity is producing hydrogen
        p_nom_extendable = True,
        carrier = "electricity",
        capital_cost = 0,
        marginal_cost = 0, 
        efficiency = 1,
        p_min_pu = -1
        )


    ## ---------------local elec bus to electricity bus--------------------------

    network.add("Link",
        "Solar system to electricity", #in reality, this is both compression and electrolysis
        bus0 = "local elec",
        bus1 = "electricity",
        #as in, electricity is producing hydrogen
        p_nom_extendable = True,
        carrier = "electricity",
        capital_cost = 0,
        efficiency = 1)

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
        efficiency = 0.4 * 0.9, #We are assuming that the process efficiency is 90%. Of which 40% goes to CO2
        efficiency2 = 0.6 * 0.9#The rest of the biogas turns into methane, at an efficiency of 0.9
        )

    return network




##-----<<METHANATION>>-------
'''Either add_methanogen OR add_sabatier will be chosen'''

def add_methanogen(network):
    '''Efficiency = sabatier efficiency = 0.8
    gas_CO2_intensity = 0.2 (This is tons of co2)
    CO2 emissions/MW H2= 0.01 
    gas compressor efficiency: 0.9785
    (2.154 kW CH4 / 100 kW CH4)'''
    #Should the sabatier efficiency for methanogen really be a methanogen efficiency? 
    #Is the heat  of enthalpy accounted for in the 0.8? Are we double counting the energy loss with efficiency and 
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
        efficiency=0.8 * 0.9785,    # how much CH4 is produced per H2 input. So 0.8 MW Ch4 produced per MW of H2
        efficiency2= 0.01, #I have no idea how many MW CO2 is emitted per MW of H2. hopefully not much. We are saying 0.01 MW of CO2 per. What are the units for each of these? We need to know whether it is in tons, or energy 
        efficiency3 = - 0.2 * 0.8 * 0.9785, #Let's assume that 0.2 MW of compressed CO2 is used per 1 MW of CH4. Negative.
        lifetime=30)

    return network


def add_sabatier(network):
    '''Efficiency = sabatier efficiency = 0.8
    gas_CO2_intensity = 0.2
    CO2 emissions/MW H2= 0.01 
    CO2 compressor efficiency = 0.98
    H2 compressor efficiency = 0.993 
    (0.695 kW H2/100 kW CH4 2.021 kW CO2/ 100 kW CH4)'''

    network.add("Link",
        "sabatier",
        bus0="H2 compressed",
        bus1="gas",
        bus2= "CO2 out",
        bus3 = "CO2 compressed",
        bus4 = "electricity",
        carrier="methanation",
        marginal_cost=0,
        capital_cost=annual_cost("methanation"),   # annualised capital costs
        p_nom_extendable=True,
        efficiency= 0.993 * 0.8,    # how much CH4 is produced per H2 input. So 0.8 MW Ch4 produced per MW of H2
        efficiency2= 0.01, #I have no idea how many MW CO2 is emitted per MW H2. hopefully not much. We are saying 0.01 MW of CO2 per  
        efficiency3 = - 0.8 * 0.993 * 0.2 * 0.98, #Let's assume that 0.2 MW of compressed CO2 is used per 1 MW of CH4. Negative.
        efficiency4 = - 0.8 * 0.993 * 0.1, #How much electricity is used per 0.8 CH4 produced. Negative. 
        #Let's say that we know that 0.1 MW electricity is used to produce 1 MW CH4. Then, the efficiency is - sabatier efficiency * 0.1
        lifetime=30)

    return network




######################################################################
######################################################################
'''These functions are for experiments with adding hydrogen storage.
Does the presence of hydrogen storage cause the electrolysis and methanation
link to become decoupled? 9 Dec 22'''

def add_hydrogen_store():
    