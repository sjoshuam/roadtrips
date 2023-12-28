##########==========##########==========##########==========##########==========##########==========
## INITIALIZE

## import packages
import pandas as pd
import plotly.graph_objects as go

## define parameters
params = dict(
    width = 1200, height = 720,
    figure_colors = dict(bg= 'hsv(000,00,00)', fg= 'hsv(000,00,100)', mg= 'hsv(000,00,40'),
    map_colors = dict(
        land = 'hsv(000,00,05)', water = 'hsv(000,00,0)',
        coast = 'hsv(000,00,20)', border= 'hsv(000,00,20)',
        ),
    visit_colors = dict(
        Unvisited    = ('hsv(030,00,00)', 'hsv(030,00,55)'),
        Visited      = ('hsv(090,20,20)', 'hsv(090,70,70)'),
        Photographed = ('hsv(150,20,20)', 'hsv(150,70,70)')
        )
    )

## TODO: Add routes (under city layers)
## TODO: propagate import_city_list(), build_city_trace() and params to 3_oconus.py

##########==========##########==========##########==========##########==========##########==========
## COMPONENT FUNCTIONS

def import_city_list():
    """
        TODO
    """
    ## import data
    city_list = pd.read_excel('io_in/city_list.xlsx', sheet_name= 'Cities', index_col= 0)

    ## formulate colors
    city_list['status'] = 'Unvisited'
    city_list.loc[city_list['visit'].astype(bool), 'status'] = 'Visited'
    city_list.loc[~city_list['photo_date'].isna(), 'status'] = 'Photographed'

    ## fill in missing data and format
    ## TODO
    city_list = city_list.fillna({'miles': 'TODO', 'photo_date': 'Never'}).reset_index(drop = True)
    city_list['state_criteria'] = city_list['state_criteria'].str.capitalize()

    ## formulate hover labels
    htxt = '<br>'.join([
        '<b>{city}</b>',
        'Inclusion Criteria: {state_criteria}',
        'Miles Walked: {miles}',
        'Last Photographed: {photo_date}'
        ])
    for iter_row in city_list.index:
        city_list.loc[iter_row, 'hover_label'] = htxt.format(**dict(city_list.loc[iter_row]))
    
    return city_list


def make_figure(params = params):
    """
        TODO
    """

    ## define standard figure parameters
    fig = go.Figure(go.Scattergeo())
    fig = fig.update_layout(
        template = 'plotly_dark',
        margin = dict(l = 0, r = 0, t = 0, b = 0),
        plot_bgcolor = params['figure_colors']['bg'],
        paper_bgcolor = params['figure_colors']['bg'],
        width = params['width'], height = params['height'],
        showlegend = False

    )

    ## define map-specific figure parameters
    parallel_offset = (49.38 - 24.54) * 1/6
    fig = fig.update_geos(

        ## specify map
        resolution = 50, scope = 'north america',
        center = dict(lat = 39.83 - 1.0, lon = -99.58),

        ## define map color sceme
        showcountries = False, 
        showcoastlines = True, coastlinecolor = params['map_colors']['coast'],
        showland = True, landcolor = params['map_colors']['land'],
        showocean = True, oceancolor = params['map_colors']['water'],
        showsubunits = True, subunitcolor = params['map_colors']['border'],
        showlakes = True, lakecolor = params['map_colors']['water'],

        ## define projection
        projection = dict(
            parallels = [49.38 - parallel_offset, 24.54 + parallel_offset],
            rotation = dict(lat = 39.83, lon = -99.58, roll = 0),
            type = 'conic conformal',
            scale = 3
        )
    )
    return fig

def build_city_trace(city_list):
    """
        TODO
    """
    trace_dict = dict()
    for iter_status in params['visit_colors'].keys():
        idx = city_list['status'] == iter_status
        name_now = iter_status + ' Cities'
        trace_dict[name_now] = go.Scattergeo(
            lat = city_list.loc[idx, 'lat'],
            lon = city_list.loc[idx, 'lon'],
            customdata = city_list.loc[idx, 'hover_label'],
            hovertemplate = '%{customdata}<extra></extra>',
            hoverlabel = dict(
                align = 'right',
                font_color = params['visit_colors'][iter_status][1],
                bgcolor = params['figure_colors']['bg']
                ),
            marker = dict(
                color = params['visit_colors'][iter_status][0],
                size = 2**4,
                line = dict(color = params['visit_colors'][iter_status][1], width = 1),
                ),
            name = name_now
            )
    return trace_dict


def write_figure(fig, trace_dict = None, slider_bar = None):
    """
        TODO
    """
    fig = fig.add_traces([trace_dict[i] for i in trace_dict.keys()])
    fig.write_html('io_out/MAP.html', full_html = True, include_plotlyjs = True)
    fig.write_html('io_mid/MAP.div', full_html = False, include_plotlyjs = False)
    div = '\n'.join(open('io_mid/MAP.div', 'rt').readlines())
    return div

##########==========##########==========##########==========##########==========##########==========
## TOP-LEVEL FUNCTIONS

##########==========##########==========##########==========##########==========##########==========
## CODE TESTS
    
if __name__ == '__main__':
    city_list = import_city_list()
    trace_dict = build_city_trace(city_list)
    fig = make_figure()
    write_figure(fig = fig, trace_dict = trace_dict, slider_bar = None)

##########==========##########==========##########==========##########==========##########==========