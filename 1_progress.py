"""
    TODO
"""
##########==========##########==========##########==========##########==========##########==========
## INITIALIZE

## import packages
import os
import pandas as pd
import plotly.graph_objects as go

## set parameters
params = {
    'bar_colors': {
        'Photographed': 'hsv(120,30,20)',
        'Visited': 'hsv(90,30,20)',
        'Unvisited': 'hsv(0,0,15)',
        },
    'bar_borders': {
        'Photographed': 'hsv(150,70,70)',
        'Visited': 'hsv(90,70,70)',
        'Unvisited': 'hsv(0,0,55)',
        },
    'bg_color': 'hsv(0,0,0)',
    'fg_color': 'hsv(0,0,80)',
    'margin': 2**5,
    'initial_slider': 'Cities, By Region',
    'dimensions': (800 - 5, 400 - 5)
}

##########==========##########==========##########==========##########==========##########==========
## COMPONENT FUNCTIONS: Manipulate Data


def import_data():
    """
        TODO
    """

    ## import and merge data
    city_list   = pd.read_excel('io_in/city_list.xlsx', sheet_name = "Cities")
    region_list = pd.read_excel('io_in/city_list.xlsx', sheet_name = "Regions")
    city_list = city_list.merge(
        right = region_list[['state', 'region', 'width', 'theta']],
        how = 'left', on = 'state')
    
    ## derived unvisited/ visited/ photographed counts
    city_list['Photographed'] = (~city_list['photo_date'].isna()).astype(int)
    city_list['Visited'] = city_list['visit'].copy() - city_list['Photographed']
    city_list['Unvisited'] = 1 - city_list['Visited'] - city_list['Photographed']

    return city_list


def refine_data(city_list):
    """
        TODO
    """
    ##
    group_cols = ['region']
    stat_cols = {
        'Photographed': 'sum', 'Visited': 'sum', 'Unvisited': 'sum', 'width': 'min', 'theta': 'min'}
    state_agg = stat_cols.copy()
    state_agg.update({
        'Photographed': 'mean', 'Visited': 'mean', 'Unvisited': 'mean'})

    ## sum by state
    state_list = city_list.copy().loc[city_list['not'].isna()]
    state_list = state_list[group_cols + list(stat_cols.keys()) +['state']]
    state_list = state_list.groupby(group_cols +['state']).agg(state_agg)
    state_list = state_list.reset_index().groupby(group_cols).agg(stat_cols).round(1)

    ## sum by city at the regional and national levels
    city_list = city_list[group_cols + list(stat_cols.keys())].groupby(group_cols).agg(stat_cols)
    sum_list = pd.DataFrame({'USA':city_list.sum()}).T
    sum_list.index = sum_list.index.set_names(city_list.index.names)

    ## return
    progress = {
        'States, By Region': state_list.reset_index(),
        'Cities, By Region': city_list.reset_index(),
        'Cities, Nationwide': sum_list.reset_index(),

    }
    return progress


##########==========##########==========##########==========##########==========##########==========
## COMPONENT FUNCTIONS: Draw Figure


def make_figure(city_list, params = params):
    """
        TODO
    """
    tick_names = city_list[['region', 'theta']].groupby('region').agg('min').sort_values('theta')
    fig = go.Figure()
    fig = fig.update_layout(
        width = params['dimensions'][0], height = params['dimensions'][1],
        plot_bgcolor = params['bg_color'],
        paper_bgcolor = params['bg_color'],
        polar = dict(bgcolor = params['bg_color']),
        font = dict(color = params['fg_color']),
        template = 'plotly_dark',
        margin = dict(
            r = params['margin'],
            l = params['margin'] * 2**1,
            t = params['margin'],
            b = params['margin']
            ),
        polar_angularaxis = dict(direction = 'clockwise',
            gridcolor = params['fg_color'], showgrid = True, showticklabels = True,
            ticktext = tick_names.reset_index()['region'],
            tickvals = tick_names['theta'],
            tickmode = 'array'
            ),
        polar_radialaxis = dict(
            gridcolor = params['fg_color'], showgrid = False, showticklabels = True)

    )
    return fig


def draw_bars(progress, params = params):
    """
        TODO
    """
    trace_dict = dict()
    for iter_trace in progress.keys():
        for iter_bar in ['Photographed', 'Visited', 'Unvisited']:
            trace_dict[iter_trace + '_' + iter_bar] = go.Barpolar(
                theta = progress[iter_trace]['theta'],
                width = progress[iter_trace]['width'],
                r = progress[iter_trace][iter_bar],
                name = iter_bar,
                visible = iter_trace == params['initial_slider'],
                text = progress[iter_trace]['region'],
                marker_color = params['bar_colors'][iter_bar],
                marker_line = dict(color = params['bar_borders'][iter_bar], width = 1),
                hovertemplate = iter_trace + ': %{r}'
                )
    return trace_dict


def draw_slider(trace_dict, params = params):
    """
        TODO
    """

    trace_keys = list()
    for iter_key in trace_dict.keys():
        key_iter = iter_key.split('_')[0]
        if key_iter not in trace_keys: trace_keys.append(key_iter)

    steps = list()
    for iter_key in trace_keys:
        steps.append(
            dict(
                method = 'update', label = iter_key,
                args = [{'visible':[i.startswith(iter_key) for i in trace_dict.keys()]}]
                ))
        
    return [
        dict(
            active = trace_keys.index(params['initial_slider']),
            steps = steps,
            currentvalue = {'prefix':'Progress Towards Achieving Travel Goals: '}
            )]

def write_figure(fig, trace_dict, slider_bar):
    """
        TODO
    """
    fig = fig.add_traces([trace_dict[i] for i in trace_dict.keys()])
    fig = fig.update_layout(sliders = slider_bar)
    fig.write_html('io_out/PROGRESS.html', full_html = True, include_plotlyjs = True)
    fig.write_html('io_mid/PROGRESS.div', full_html = False, include_plotlyjs = False)
    div = '\n'.join(open('io_mid/PROGRESS.div', 'rt').readlines())
    return div


##########==========##########==========##########==========##########==========##########==========
## TOP-LEVEL FUNCTIONS

def draw_progress_panel():
    """
        TODO
    """

    ## import and refine data
    city_list = import_data()
    progress = refine_data(city_list)

    ## draw progress figure
    fig = make_figure(city_list)
    trace_dict = draw_bars(progress)
    slider_bar = draw_slider(trace_dict)
    div = write_figure(fig, trace_dict, slider_bar)

    return div


##########==========##########==========##########==========##########==========##########==========
## CODE TESTS

if __name__ == '__main__':
    draw_progress_panel()



##########==========##########==========##########==========##########==========##########==========