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
        #27 recheck weather station assignment cities missing a station. (Low Priority)
"""
##########==========##########==========##########==========##########==========##########==========
## INITIALIZE

## import packages
import os, multiprocessing, sys
from urllib import request
if not sys.prefix.endswith('.venv'): raise Exception('Virtual Environment Not Detected')  
import pandas as pd
import numpy as np

## set parameters
params = dict(
    parallel_workers = 4,
    months = [
        '01_Jan', '02_Feb', '03_Mar', '04_Apr', '05_May', '06_Jun', '07_Jul', '08_Aug',
        '09_Sep', '10_Oct', '11_Nov', '12_Dec']
)
os.environ['no_proxy']='*'


##########==========##########==========##########==========##########==========##########==========
## REUSABLE FUNCTIONS


def split_list(the_list: list, splits = params['parallel_workers']) -> dict:
    """ Splits a list into separate lists contained within a dict object, as a prelude to parallel
    processing.
    """
    split_index = {i:[] for i in range(0, params['parallel_workers'])}
    for i in range(0, len(the_list)): split_index[i%splits] = split_index[i%splits] + [the_list[i]]
    return split_index


##########==========##########==========##########==========##########==========##########==========
## COMPONENT FUNCTIONS - download raw data


def import_weather_stations() -> list:
    """Import city data and extract weather station list from it"""
    weather_stations = pd.read_excel('io_in/city_list.xlsx', sheet_name= 'Cities')
    return sorted(weather_stations['noaa_station'].dropna().to_list())


def rwe_worker(idx:list, weather_stations:list, thirty_year_normals=False) -> None:
    """ Iteratively retrieves data from a list of weather stations.  Designed to be instantiated
    multiple times in parallel in the retrieve_weather_data() function.
    Inputs:
        weather_stations = list of all weather data identification numbers
        idx = index numbers that correspond to positions in the weather_stations list.  Determines
            which weather station identification numbers should be queried.
        thirty_year_normals = bool determining weather rwe_worker() should retrieve data for the
            30 years between 1991 and 20202 (i.e. 30 year climate normals) or just the 15 years
            between 2006 and 2020.  Statistically, a 30-year average is considered more
            accurate than a 15-year average.  However, temperatures have been abnormally high in
            recent decades, so the 15-year average may be more useful for predicting future
            trends.
        Outputs:
            As rwe_worker() downloads data from the NOAA, it writes that data in csv format to
            weather_data directory.  This prevents data from accumulating in RAM.  It also makes
            it easier to start and stop download as needed, rather than having to start over each
            time.  Before downloading a file, rwe_worker() checks to see if the file is already
            in the weather_data directory and will move on without downloading if the file is 
            present. rwe_worker() returns None when it finishes iterating through the download list.
    """
    data_dir = os.path.join('io_mid', 'weather_data')
    source_url = 'https://www.ncei.noaa.gov/data/normals-hourly/2006-2020/access/{0}.csv'
    if thirty_year_normals:
        source_url = 'https://www.ncei.noaa.gov/data/normals-hourly/1991-2020/access/{0}.csv'
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


def retrieve_weather_data(weather_stations:list, params=params) -> None:
    """ Divides a list of weather stations among multiple lists, and then instantiates rwe_worker()
        multiple times in parallel to download data for each station.
        Inputs:
            weather_stations = a list of weather station ids.  rwe_worker queries a NOAA csv
                repository for a corresponding data file to download.
            params = a general parameters file.  Used here to determine how many parallel
                versions of rwe_worker() should be instantiated.
        Outputs: returns None; rwe_worker() saves downloaded data to list.
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


def refine_weather_data(ideal_temp=[50,75], active_hours=[8,17]) -> None:
    """ reads in raw weather data files previously downloaded from NOAA. Simplifies and compiles
    data from them to determine the average number of temperate hours per day for each month. The
    averages are based on data from the 7th day of the month to the 23th day of the month, so they
    better reflect mid-month conditions.
    Input:
        ideal_temp = A temperate hour is defined as having a temperature between those specified
            here.  Temperatures are in degrees Fahrenheit. By default, this range is 50°F to 75°F,
            based on the assumption that ideal walking conditions are cooler than room temperature
            but warmer than jacket weather.  This is very approximately -- people differ in their
            exact temperature preferences, and wind / humidity / cloud cover / etc. decisively
            impact what temperature is actually comfortable.
        active_hours = Temperate hours are only counted for hours of the day that fall in this
            range. By default, this is 8am to 5pm.
    Output:  Outputs a xlsx file to the io_mid directory, called weather_data.xlsx
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
    all_data['temp'] = (all_data['hly-temp-normal'] >= min(ideal_temp))
    all_data['temp'] &= (all_data['hly-temp-normal'] <= max(ideal_temp))
    all_data = all_data.astype({'temp': int})
    all_data = all_data.drop(columns = ['hly-temp-normal'])
    all_data = all_data.groupby(['station','latitude','longitude','name','month','day','hour'])
    all_data = all_data.agg('mean').reset_index()
    all_data = all_data.loc[
        (all_data['hour'] >= min(active_hours)) & (all_data['hour'] <= max(active_hours))]
    all_data = all_data.groupby(['station','latitude','longitude','name','month','day']).agg('sum')
    all_data = all_data.drop(columns = ['hour']).reset_index()
    
    ## bin time - early, mid months
    all_data['month'] = all_data['month'].replace({i:params['months'][i-1] for i in range(1, 13)})
    day_bins = {i:'EXCLUDE' for i in range(0, 32)}
    #day_bins.update({i:' (Early)' for i in range(1, 11)})
    day_bins.update({i:' (Mid)' for i in range(7, 30-6)})
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
    """ Top-level function, loaded and invoked in 0_execute_project.py.  Sequentially executes the 
    other functions in this modules
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