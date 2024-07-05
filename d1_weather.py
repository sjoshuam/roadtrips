"""
    Purpose: Download NOAA weather data and compile it into information on the best time to visit
        each destination.
    Inputs:
        io_in/city_list.xlsx: provides information on the destinations I seek to visit and my
            progress visiting them.
        www.ncei.noaa.gov: code downloads weather data from this site and stores it in
            io_mid/weather_data
    Outputs:
        io_mid/weather_data.xlsx: records the average number of temperate hours per day in each
            destination for periods throughout the year.
    Open GitHub Issues:
        #26 Add doc strings, type hints, module doc strings, etc. as needed
"""
##########==========##########==========##########==========##########==========##########==========
## INITIALIZE

## import packages
import os, multiprocessing
from urllib import request
import pandas as pd
import numpy as np
import plotly.graph_objects as go

## set parameters
params = dict(
    parallel_workers = 4,
    months = [
        '01_Jan', '02_Feb', '03_Mar', '04_Apr', '05_May', '06_Jun', '07_Jul', '08_Aug',
        '09_Sep', '10_Oct', '11_Nov', '12_Dec']
)
os.environ['no_proxy'] = '*'


##########==========##########==========##########==========##########==========##########==========
## REUSABLE FUNCTIONS


def split_list(the_list, splits = params['parallel_workers']):
    """
        TODO
    """
    split_index = {i:[] for i in range(0, params['parallel_workers'])}
    for i in range(0, len(the_list)): split_index[i%splits] = split_index[i%splits] + [the_list[i]]
    return split_index


##########==========##########==========##########==========##########==========##########==========
## COMPONENT FUNCTIONS - download raw data


def import_weather_stations():
    """Import city data and extract weather station list from it"""
    weather_stations = pd.read_excel('io_in/city_list.xlsx', sheet_name= 'Cities')
    return sorted(weather_stations['noaa_station'].dropna().to_list())


def rwe_worker(idx, weather_stations):
    """
        TODO
    """
    data_dir = os.path.join('io_mid', 'weather_data')
    #source_url = 'https://www.ncei.noaa.gov/data/normals-hourly/1991-2020/access/{0}.csv'
    source_url = 'https://www.ncei.noaa.gov/data/normals-hourly/2006-2020/access/{0}.csv'
    for iter_idx in idx:
        source_url_iter = source_url.format(weather_stations[iter_idx])
        dest_url_iter = os.path.join(data_dir, weather_stations[iter_idx] + '.csv')
        if os.path.exists(dest_url_iter): continue

        try:
            data_iter = request.urlretrieve(source_url_iter)[0]
            data_iter = '\n'.join(open(data_iter, 'rt').readlines())
        except Exception as except_msg:
            print('DOWNLOAD FAILED:', source_url_iter)
            continue
        open(dest_url_iter, 'wt').writelines(data_iter)
    return None


def retrieve_weather_data(weather_stations, params = params):
    """
        TODO
    """
    ## prepare for data transfer
    data_dir = os.path.join('io_mid', 'weather_data')
    if not os.path.exists(data_dir): os.mkdir(data_dir)

    ## divide stations among parallel workers
    station_idx = np.arange(0, len(weather_stations))
    station_worker = np.mod(station_idx, params['parallel_workers'])
    station_idx = [station_idx[station_worker==i] for i in np.arange(0, params['parallel_workers'])]

    ## download data files in parallel
    parallel_workers = multiprocessing.Pool(params['parallel_workers'])
    parallel_output = list()
    for iter_worker in range(0, params['parallel_workers']):
        parallel_output.append(
            parallel_workers.apply_async(
                func = rwe_worker,
                kwds = dict(
                    idx = station_idx[iter_worker],
                    weather_stations = weather_stations
                    )
                )
            )
    [i.get() for i in parallel_output]
    parallel_workers.close()
    return None


def refine_weather_data():
    """
       TODO 
    """

    ## read in data files and compile
    data_dir = os.path.join('io_mid', 'weather_data')
    all_files = os.listdir(data_dir)
    all_data = list()
    cols = ['STATION', 'LATITUDE', 'LONGITUDE', 'NAME', 'month', 'day', 'hour', 'HLY-TEMP-NORMAL']
    for iter in range(0, len(all_files)):
        if not all_files[iter].endswith('csv'): continue
        all_data.append(
            pd.read_csv(
                os.path.join(data_dir, all_files[iter]),
                encoding_errors = 'replace',
                usecols = cols
                ))
    all_data = pd.concat(all_data)
    all_data.columns = all_data.columns.str.lower()

    ## refine data
    all_data['temp'] = (all_data['hly-temp-normal'] >= 50) & (all_data['hly-temp-normal'] < 75)
    all_data = all_data.astype({'temp': int})
    all_data = all_data.drop(columns = ['hly-temp-normal'])
    all_data = all_data.groupby(['station','latitude','longitude','name','month','day','hour'])
    all_data = all_data.agg('mean').reset_index()
    all_data = all_data.loc[(all_data['hour'] >= 8) & (all_data['hour'] <= 19)]
    all_data = all_data.groupby(['station','latitude','longitude','name','month','day']).agg('sum')
    all_data = all_data.drop(columns = ['hour']).reset_index()
    
    ## bin time - early, mid months
    all_data['month'] = all_data['month'].replace({i:params['months'][i-1] for i in range(1, 13)})
    day_bins = {i:'EXCLUDE' for i in range(0, 32)}
    #day_bins.update({i:' (Early)' for i in range(1, 11)})
    day_bins.update({i:' (Mid)' for i in range(7, 30-7)})
    all_data['day'] = all_data['day'].replace(day_bins)
    all_data['period'] = all_data['month'] + all_data['day']
    all_data = all_data.loc[all_data['day'] != 'EXCLUDE', ~all_data.columns.isin(['day', 'month'])]
    cols = all_data.columns[~all_data.columns.isin(['temp'])].to_list()
    all_data = all_data.groupby(cols).agg('mean').reset_index()
    all_data = all_data.pivot(index = 'station', columns = 'period', values = 'temp')

    ## export as excell
    all_data.to_excel(os.path.join('io_mid', 'weather_data.xlsx'))
    return None


##########==========##########==========##########==========##########==========##########==========
## TOP-LEVEL FUNCTIONS


def download_weather_data():
    """
        TODO
    """
    weather_stations = import_weather_stations()
    retrieve_weather_data(weather_stations = weather_stations)
    weather_data = refine_weather_data()
    return weather_data


##########==========##########==========##########==========##########==========##########==========
## CODE TESTS

if __name__ == '__main__':
    weather_data = download_weather_data()

##########==========##########==========##########==========##########==========##########==========