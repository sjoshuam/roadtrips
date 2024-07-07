## import packages
import os, multiprocessing
from urllib import request
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from sklearn.neighbors import KNeighborsRegressor as sklearn_KNeighborsRegressor
from scipy.spatial import distance as scipy_distance
from math import radians, degrees

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