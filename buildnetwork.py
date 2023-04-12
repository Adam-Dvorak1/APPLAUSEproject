'''The goal of this program is to provide functions that allow for the building of the network'''
import pandas as pd
from helpers import annual_cost



def add_buses(network):
    '''This function takes an existing network and adds the buses'''
    network.add("Bus","electricity", carrier = "electricity")

    network.add("Bus","local elec", carrier = "local elec")

    network.add("Bus", "H2 compressed", carrier  = "H2 compressed") #I believe that the H2 is not necessarily compressed--we just call it that. The multilink adds compression (or not)

    network.add("Bus", "gas", carrier = "gas")

    network.add("Bus", "CO2 out", carrier = "co2 released") 

    network.add("Bus", "biogas", carrier = "biogas") 

    network.add("Bus", "CO2 compressed", carrier = "co2 compressed") #Note, CO2 compressed is actually only CO2 in for the methanogen case 

    network.add("Bus", "grid", carrier = "grid")

    return network


def add_generators(network):
    '''There are three generators: solar, biogas, and grid. The grid is huge and has a 
    marginal cost. The solar generator has a max size of 130 MW. The biogas generator is free and can be infinitely big.



    This also sets the network snapshots'''
    hours_in_2019 = pd.date_range('2019-01-01T00:00:00','2019-12-31T23:00:00', freq='H') #I changed the date rate from Z
    network.set_snapshots(hours_in_2019)

    df_cal_solar = pd.read_csv('data/final_solar_csvs/RealCalFlatsSolarCFs_2019.csv', index_col=0) #Solar CFs taken from renewables.ninja and google maps location of California Flats (35.854394, -120.304389), though renewables.ninja only does 3 decimal points
    df_cal_solar.index = pd.to_datetime(df_cal_solar.index)
    df_cal_biogas = df_cal_solar['biogas'][[hour.strftime("%Y-%m-%dT%H:%M:%S") for hour in network.snapshots]] #This is just assuming a constant generator, which I added to the original data from renewables.ninja
    df_cal_solar = df_cal_solar['solar'][[hour.strftime("%Y-%m-%dT%H:%M:%S") for hour in network.snapshots]] #capacity factor time series 


    gridprice = pd.read_csv("data/elecprice_csvs/2019UTCCAISOprice.csv", index_col = 0) #From http://www.energyonline.com/Data/GenericData.aspx?DataId=20, which is taken from CAISO. Units of /MWh
    gridprice.index = pd.to_datetime(gridprice.index)
    gridprice = gridprice['price'][[hour.strftime("%Y-%m-%d %H:%M:%S") for hour in network.snapshots]]
    gridprice = gridprice/1000 #Before, I used to divide by 100. But I believe that I should have divided by 1000, because we want per kWh, and we had per MWh ##note this is incorrect. 


    gridgen = pd.DataFrame(index = range (8760))
    gridgen = gridgen.set_index(hours_in_2019)
    gridgen['grid'] = 1 #in kW, so 100GW


    network.add("Generator", "Solar PV", bus="local elec",p_nom_extendable = True,#We can't put p_nom here because p_nom is for free. We need p_nom_extendable to be True, and then set a max
        carrier = 'solar', capital_cost = 0, #As of 21 March, we consider solar as a dispatch model, where it is set at 130000. So the model thinks it is free, though we add the costs later
        marginal_cost = 0, p_nom = 130000, p_nom_max = 130000, p_max_pu = df_cal_solar) #Max installation of 130 MW, which is Apple's share of Cal Flats https://www.apple.com/newsroom/2021/03/apple-powers-ahead-in-new-renewable-energy-solutions-with-over-110-suppliers/

    network.add("Generator", "Biogas", bus="biogas", p_nom_extendable = True, 
        carrier = 'biogas', capital_cost = 0,
        marginal_cost = 0, p_max_pu = df_cal_biogas) # In reality, there is a marginal cost for biogas. What is it? 

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
    gasdf = pd.read_csv('data/gasdem_csvs/2019AppleGas.csv', index_col = 0)
    gasdf.index = pd.to_datetime(gasdf.index)

    network.add("Load", #Why are there two loads here? Which is the name?
        "Gas Load", 
        bus="gas", 
        p_set=gasdf["All_in_one_demand"]) #An average of 10 MW of demand, all at the end of the year

    network.add("Load", 
        "Grid Load", 
        bus="grid", 
        p_set=gasdf["Constant_MW_methane"] * 3000)#Assuming 30 GW of demand from the grid

    return network


def add_stores(network):
    '''This adds three stores: a battery, for the solar generator; a gas store, for the load;
    and a CO2 environment, to capture the CO2 '''

    tech_data = pd.read_csv("data/costs_2025_NRELsolwind.csv")

    ## ------------------battery---------------------------
    network.add("Bus", "battery", carrier = "battery")
    network.add("Store",
        "battery",
        bus = "battery",
        e_cyclic = True, #NO FREE LUNCH must return back to original position by end of the year
        e_nom_extendable = True,
        e_nom_max = 240000, #Because Apple is planning a 240 MWh battery storage. This corresponds to 2 hr storage
        capital_cost =  annual_cost("battery storage")) #Eur/kWh/yr
    network.add("Link",
        "battery charger",
        bus0 = "local elec",
        bus1 = "battery",
        carrier = "battery charger",
        # efficiency = 1,
        efficiency =tech_data.query("technology == 'battery inverter' & parameter == 'efficiency'")['value'].values[0] ** 0.5, #Taking square root because 
        p_nom_extendable = True,
        capital_cost =  annual_cost("battery inverter") )
    network.add("Link",
        "battery discharger",
        bus0 = "battery",
        bus1 = "local elec",
        carrier = "battery discharger",
        #efficiency = 1,
        efficiency = tech_data.query("technology == 'battery inverter' & parameter == 'efficiency'")['value'].values[0] ** 0.5,
        p_nom_extendable = True,
        ) 





    ## ---------------------gas-----------------------------
    #We want a completely free gas storage, as its only purpose is to serve as flexibility for the load
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
    #The purpose of this store is to keep track of any CO2 emissions, if any
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
    


    ## -------H2 Store--------------------------
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



    return network


def add_links(network):
    '''This adds links that are not methanogenesis or connecting to stores:
    electrolysis, high to low voltage electricity, solar to electricity, biogas'''
    
    tech_data = pd.read_csv("data/costs_2025_NRELsolwind.csv")

    ## ---------------Electrolysis--------------------------
    '''Compression is taken in during the methanogenesis link'''
    network.add("Link",
        "H2 Electrolysis", 
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
    grid and the global electricity grid. It is bidirectional, lossless, and free'''

    network.add("Link",
        "High to low voltage", 
        bus0 = "grid",
        bus1 = "electricity",
        p_nom_extendable = True,
        carrier = "electricity",
        capital_cost = annual_cost('electricity grid connection'),#From the Danish Energy agency, let's assume that the inverter from the grid is between the 2020 and 2030 price of the solar inverter--0.025 MEur per MW, or 25 Eur per kW
        marginal_cost = 0, 
        efficiency = 1,
        p_min_pu = -1
        )


    ## ---------------local elec bus to electricity bus--------------------------

    network.add("Link",
        "Solar system to electricity", 
        bus0 = "local elec",
        bus1 = "electricity",
        p_nom_extendable = True,
        carrier = "electricity",
        capital_cost = 0,
        efficiency = 1)

    ## ---------------Biogas bus to CO2 compressed and gas bus--------------------------

    network.add("Link",
        "Biogas upgrading", 
        bus0 = "biogas", 
        bus1 = "CO2 compressed",
        bus2 = "gas",
        p_nom_extendable = True,
        carrier = "biogas",
        capital_cost = 0, #annual_cost("biogas upgrading")/1000 * 2, 
        efficiency = 0.4 * 0.9, #We are assuming that the process efficiency is 90%. Of which 40% goes to CO2
        efficiency2 = 0.6 * 0.9 #The rest of the biogas turns into methane, at an efficiency of 0.9
        )

    return network




##-----<<METHANATION>>-------
'''Either add_methanogen OR add_sabatier will be chosen'''

def add_methanogen(network):
    '''Efficiency = sabatier efficiency = 0.8
    gas_CO2_intensity = 0.2 
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
        capital_cost=annual_cost("methanation") * 3 ,   # annualised capital costs. it gets overridden in modifynetwork.py change_loads_costs() by  annual_cost("methanation") * megen_mult
        p_nom_extendable=True,
        efficiency=0.8 * 0.9785,    # how much CH4 is produced per H2 input. So 0.8 MW Ch4 produced per MW of H2
        efficiency2= 0.01, #I have no idea how many MW CO2 is emitted per MW of H2. 
        efficiency3 = - 0.2 * 0.8 * 0.9785, #Let's assume that 0.2 MW of compressed CO2 is used per 1 MW of CH4. Negative.
        lifetime=30)

    return network


def add_sabatier(network):
    '''Efficiency = sabatier efficiency = 0.8
    gas_CO2_intensity = 0.2
    CO2 emissions/MW H2= 0.01 
    CO2 compressor efficiency = 0.98
    H2 compressor efficiency = 0.993 
    (0.695 kW H2/ 100 kW CH4; 2.021 kW CO2/ 100 kW CH4)'''

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



