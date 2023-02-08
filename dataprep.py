'''The purpose of this file is to show what we do in order to prep the data.

For example, we get solar data from renewables.ninja for the point of (35.854394, -120.304389),
which represents the location of Cal Flats. This gives us a specific capacity factor time series.
We want to strip down the csv to get into a very clean format'''

import pandas as pd
import glob
import datetime as dt
import numpy as np

def prepare_solar_yr(path):
    '''
    7 Feb 2023 
    This function takes in a csv file from renewables.ninja, extracts the time and the solar
    capacity factors, and stores it in the folder final_solar_csvs. 
    
    It assumes that the original path of the csv is renamed to the correct year, as in _2016.csv.
    
    It also assumes the existance of a constant biogas generator. We do not really have a better
    assumption than this as of the moment
    '''
    df = pd.read_csv(path, skiprows = 3)

    df = df.rename(columns = {'time': 'UTC'})
    o = path.split("_")
    yr = o[-1]
    dfnew = pd.DataFrame() 
    dfnew['solar'] = df['electricity']
    dfnew.index = df['UTC']
   
    dfnew['biogas'] = 0.8

    dfnew.to_csv('data/final_solar_csvs/RealCalFlatsSolarCFs_' + yr )


    
    
def prepare_CAISO_elecprices(path):
    '''
    7 Feb 2023
    This function reads in a csv with many year's worth of electricity price data
    from CAISO (ie, from http://www.energyonline.com/Data/GenericData.aspx?DataId=20). It assumes that the data
    is 5-minute resolution, at local time. Then, it cleans and resamples the data to get an hourly
    sampling, filling in missing values
    '''

    df = pd.read_csv(path, index_col = 0)

    # %m = decimal month, %d = decimal day, %y = full year, %I = decimal hour (12h), 
    # %M = decimal minute, %S = decimal second, %p = AM/PM
    # For example, '08/22/2018 01:23:00 PM'
    # I believe that giving python the format makes it read the strings faster
    format = '%m/%d/%Y %I:%M:%S %p'

    df.index = pd.to_datetime(df.index, format = format)
    
    #The CAISO data comes in 5 minute intervals
    index = pd.date_range(start = '12/31/2016', end = '10/26/2022', freq = '5min')

    #Unfortunately there are some missing values, so we fill those with np.nan in themean time
    df = df.reindex(index, fill_value = np.nan)

    #Downsample, we only want the average per hour
    df = df.resample('H').mean()

    #Now, we fill the missing hours using linear interpolation
    df['price'] = df['price'].interpolate()

    #store cleaned data in new csv
    df.to_csv('data/UTCCAISO_allyears.csv')



    
def get_CAISO_year(path, year):
    '''
    8 Feb 2023 
    This function reads in a cleaned, 1-hr sampled csv courtesy of the function prepare_CAISO_elecprices()
    Based on the year of data, '''

    

    # df.index = pd.to_datetime(df.index)

    # #Since we are dealing with local time

    # lowindex = 
    # df = [x for x in df.index if x > dt.strptime(yearbelow + '-12-31 15:55', "%Y-%m-%d %H:%M") and x < dt.strptime(year + '-12-31 16:05', "%Y-%m-%d %H:%M")]
    
    # df = df.groupby([df.index.year, df.index.month, df.index.day, df.index.hour]).mean()
    # newindex = df.index.to_flat_index()
    # newindex = [str(x[0]) + "-" + str(x[1]) + "-" + str(x[2]) + '-' + str(x[3]) for x in newindex]
    # df.index = pd.to_datetime(newindex, format = '%Y-%m-%d-%H')


    # df.to_csv('data/elecprice_csvs/' + year + "UTCCAISOprice.csv")






if __name__ == "__main__":
    # path = "data/og_solar_renewablesninja/*"

    # for apath in glob.glob(path):
    #     prepare_solar_yr(apath)
    path = "data/20161231-20161231 CAISO Average Price.csv"
    prepare_CAISO_elecprices(path)
    

