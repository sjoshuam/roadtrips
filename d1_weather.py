"""
    TODO
"""
##########==========##########==========##########==========##########==========##########==========
## INITIALIZE

## import packages
import os, multiprocessing
from urllib import request
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from sklearn.neighbors import KNeighborsRegressor as sklearn_KNeighborsRegressor
from scipy.spatial import distance as scipy_distance
from math import radians, degrees

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
    source_url = 'https://www.ncei.noaa.gov/data/normals-hourly/1991-2020/access/{0}.csv'
    for iter_idx in idx:
        source_url_iter = source_url.format(weather_stations[iter_idx])
        dest_url_iter = os.path.join(data_dir, weather_stations[iter_idx] + '.csv')
        if os.path.exists(dest_url_iter): continue

        try:
            data_iter = request.urlretrieve(source_url_iter)[0]
            data_iter = '\n'.join(open(data_iter, 'rt').readlines())
        except:
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
    day_bins.update({i:' (Early)' for i in range(1, 11)})
    day_bins.update({i:' (Mid)' for i in range(16, 26)})
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
## COMPONENT FUNCTIONS - build weather grid for go.Contour
'''
def extract_weather_data():
    """
        TODO
    """
    weather_data =  pd.read_excel(os.path.join('io_mid', 'weather_data.xlsx'), index_col = False)
    months = {i+1:params['months'][i] for i in range(0, len(params['months']))}
    weather_data['mm'] = weather_data['month'].replace(months)
    weather_data['day'] = (weather_data['day'] // 7).replace({0:'early',1:'x',2:'mid',3:'x',4:'x'})
    weather_data = weather_data.loc[weather_data['day'] != 'x']
    weather_data['period'] = weather_data['mm'] + ' (' + weather_data['day'] + ')'
    weather_data = weather_data[['station', 'latitude', 'longitude', 'period', 'month', 'temp']]
    weather_data = weather_data.groupby(['station', 'latitude', 'longitude', 'period'])
    weather_data = weather_data.agg('mean').round(6).reset_index()
    weather_data = weather_data.sort_values(['latitude', 'longitude', 'month'])
    return weather_data.astype({'month':int}).reset_index()


def make_weather_grid(weather_data):
    """
        TODO
    """
    space_coord = lambda x,n: pd.DataFrame({n: np.arange(int(min(x)), int(max(x)) + 1, 1)})
    weather_grid = space_coord(weather_data['longitude'], 'longitude')
    weather_grid = weather_grid.merge(
        right = space_coord(weather_data['latitude'], 'latitude'), how = 'cross')
    return weather_grid


def kpg_worker(periods, weather_data, weather_grid, params = params):
    """
        TODO
    """
    ## prepare for iteration
    weather_data = weather_data.loc[weather_data['period'].isin(periods)].copy()
    weather_grid = weather_grid.copy()
    for iter_col in ['latitude', 'longitude']:
        weather_data[iter_col] = weather_data[iter_col].apply(radians)
        weather_grid[iter_col] = weather_grid[iter_col].apply(radians)
    kpg_output = list()
    knn = sklearn_KNeighborsRegressor(n_neighbors = 8, weights = 'distance',
        metric = 'haversine', n_jobs = 1) # can't parallelize because already using multiprocessing

    ## generate knn predictions for each time period
    for iter_period in periods:
        period_idx = weather_data['period'] == iter_period
        model_iter = knn.fit(
            X = weather_data.loc[period_idx, ['longitude', 'latitude']],
            y = weather_data.loc[period_idx, 'temp'])
        prediction_iter = weather_grid.copy()
        prediction_iter['temp'] = knn.predict(prediction_iter[['longitude', 'latitude']])
        for iter_col in ['latitude', 'longitude']:
            prediction_iter[iter_col] = prediction_iter[iter_col].apply(degrees)
        prediction_iter['period'] = iter_period
        kpg_output.append(prediction_iter)
    
    ## package and return
    kpg_output = pd.concat(kpg_output)
    return kpg_output
    


def knn_predict_grid(weather_data, weather_grid, params = params):
    """
        TODO
    """
    periods = split_list(list(set(weather_data['period'])), splits = params['parallel_workers'])
    parallel_workers = multiprocessing.Pool(params['parallel_workers'])
    parallel_tasks = list()
    for iter_split in periods.keys():
        parallel_tasks.append(
            parallel_workers.apply_async(
                func = kpg_worker,
                kwds = dict(
                    periods = periods[iter_split],
                    weather_data = weather_data,
                    weather_grid = weather_grid
                    )
                )
            )
    parallel_tasks = [i.get() for i in parallel_tasks]
    parallel_tasks = pd.concat(parallel_tasks).sort_values(['period', 'latitude', 'longitude'])
    return parallel_tasks
'''

##########==========##########==========##########==========##########==========##########==========
## COMPONENT FUNCTIONS - spare parts for building a weather contour map

'''
def import_weather_grid():
    """
        TODO
    """
    weather_grid = pd.read_excel(os.path.join('io_mid', 'weather_grid.xlsx'))
    weather_grid = weather_grid.pivot(
        index = ['period', 'latitude'], columns = ['longitude'], values = ['temp'])
    weather_grid = weather_grid.sort_index(ascending = False)
    return weather_grid



def build_weather_trace(weather_grid):
    """
        TODO
    """
    print('TEST MODE')
    periods = sorted(list(set(weather_grid.index.get_level_values('period'))))[0:1]
    trace_dict = dict()
    for iter_period in periods:
        grid_now = weather_grid.loc[iter_period, 'temp']
        trace_dict[iter_period] = go.Contour(
            colorscale = 'Electric', name = iter_period, line_smoothing = 0.50,
            x = grid_now.columns.values, y = grid_now.index.values, z = grid_now
            )
    return trace_dict
'''

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

'''
def build_weather_model(params = params):
    """
        TODO
    """
    weather_data = extract_weather_data()
    #weather_grid = make_weather_grid(weather_data = weather_data)
    #weather_grid = knn_predict_grid(
    #    weather_data = weather_data, weather_grid = weather_grid, params = params)
    #weather_grid.to_excel(os.path.join('io_mid', 'weather_grid.xlsx'), index = False)
    return weather_grid
'''

##########==========##########==========##########==========##########==========##########==========
## CODE TESTS

if __name__ == '__main__':
    weather_data = download_weather_data()

##########==========##########==========##########==========##########==========##########==========