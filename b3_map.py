"""
    Purpose: Generates html map displays to show information about the typical weather conditions
        in each destination at different periods throughout the year (planning tool).  Also,
        depicts information about past travels, including routes and visits.  This displays,
        linked together with a slider bar, generate the core panel of this project's html page.
    Inputs:
        io_in/city_list.xlsx: provides information on the destinations I seek to visit and my
            progress visiting them.
        io_in/color.xlsx: centralized color palette for the project
        io_in/Travels.kml: google earth kml file recording the routes traveled for each trip
            as a line of coordinates.
        io_mid/weather_data.xlsx: records the average number of temperate hours per day in each
            destination for periods throughout the year.

    Outputs:
        io_mid/MAP.html: self-contained, fully-functional html file with all data displays.
            Used during development to inspect data displays.  Is not tied into the project
            css file, so some stylistic elements will be of lower quality.
        io_mid/MAP.div: html code contained inside a <div> tag, suitable for injection into
            the project's main html product.
    Open GitHub Issues:
        #15 Centralize color palette
        #26 Fill in missing doc strings
        #11 Refresh panel when miles-walked data is more complete. (Low priority)
"""
##########==========##########==========##########==========##########==========##########==========
## INITIALIZE

## import packages
import os, sys
from xml.dom.minidom import parse as xml_parse
if not sys.prefix.endswith('.venv'): raise Exception('Virtual Environment Not Detected')  
import pandas as pd
import plotly.graph_objects as go

## define parameters
params = {
    'color': pd.read_excel(os.path.join('io_in', 'colors.xlsx'), index_col = 0)
}

params['visit_colors'] = {'Photographed': 50, 'Visited': 25, 'Unvisited': 0}
params['visit_borders'] = {'Photographed': 100, 'Visited': 50, 'Unvisited': 25}

params.update(dict(
    width = 1000 - 10,
    height = 720 - 10,
    city_size = 2**3,
    route_res = 0.08,
    ))

## TODO: Add routes (under city layers)

##########==========##########==========##########==========##########==========##########==========
## COMPONENT FUNCTIONS - data shaping


def import_city_list():
    """
        TODO
    """
    ## import data
    city_list = pd.read_excel(
        os.path.join('io_in', 'city_list.xlsx'), sheet_name= 'Cities', index_col= 0)

    ## formulate colors
    city_list['status'] = 'Unvisited'
    city_list.loc[city_list['visit'].astype(bool), 'status'] = 'Visited'
    city_list.loc[~city_list['photo_date'].isna(), 'status'] = 'Photographed'

    ## fill in missing data and format
    ## TODO
    city_list['miles'] = city_list['miles'].round(1)
    city_list = city_list.fillna({'miles': 'Data Pending', 'photo_date': 'Never'}).reset_index(drop = True)
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


def add_weather_to_city(city_list):
    """
        TODO
    """
    weather_data = pd.read_excel(os.path.join('io_mid', 'weather_data.xlsx'), index_col = 0)
    weather_data.columns = 'W∆' + weather_data.columns
    city_list = city_list.merge(
        right = weather_data, how = 'left', left_on = 'noaa_station', right_index = True)
    city_list = city_list.round(1)
    ##city_list = city_list.fillna({i:0 for i in weather_data.columns})
    return city_list


def import_routes(params = params):
    """
        TODO
    """

    ## extract route folders
    x =  xml_parse(os.path.join('io_in', 'Travels.kml')).getElementsByTagName('Folder')

    ## extract names and coordinates for each route segment
    def refine_xy(xy):
        """TODO"""
        xy = xy.getElementsByTagName('coordinates')[0].firstChild.nodeValue.strip().split(' ')
        xy = pd.DataFrame([i.split(',')[0:2] for i in xy], columns = ['lon', 'lat']).astype(float)
        return xy

    def extract_elements(elem):
        """TODO"""
        elem = elem.getElementsByTagName('Placemark')
        elem_name = [i.getElementsByTagName('name')[0].firstChild.nodeValue for i in elem]
        elem_xy = [refine_xy(i) for i in elem]
        return {elem_name[i]:elem_xy[i] for i in range(0, len(elem_name))}
    x = {i.getElementsByTagName('name')[0].firstChild.nodeValue: extract_elements(i) for i in x}

    ## flatten extract data
    x = {i:x[i] for i in x.keys() if i != 'Travels'}
    x = {i:pd.concat(x[i]) for i in x.keys()}
    x = pd.concat([x[i].assign(**{'trip': i}) for i in x.keys()]).reset_index()
    x = x.rename(columns = {'level_0': 'segments', 'level_1': 'order'})
    x['segments'] = 'S∆' + x['segments']

    ## simplify data and return
    def tokenize_xy(x, n = params['route_res']):
        return '|' + ((x / n).round(0) * n).round(6).astype(str) + '|'
    x['dedup'] = tokenize_xy(x['lat']) + tokenize_xy(x['lon']) + x['trip'] + x['segments']
    x['last'] = x['segments'] + x['trip']
    x = x.merge(
        right = x[['last', 'order']].groupby(['last']).agg('max'),
        how = 'left', left_on = 'last', right_index = True
        ).rename(columns = {'order_x': 'order'})
    x['last'] = x['order_y'] == x['order']
    x['dedup'] = x['dedup'].duplicated() & ~x['last']
    x = x.loc[~x['dedup'], ~x.columns.isin(['dedup', 'last', 'order_y'])]
    return x


##########==========##########==========##########==========##########==========##########==========
## COMPONENT FUNCTIONS - render image


def make_figure(params = params):
    """
        TODO
    """

    ## define standard figure parameters
    fig = go.Figure()
    fig = fig.update_layout(
        template = 'plotly_dark',
        margin = dict(l = 0, r = 0, t = 0, b = 0),
        plot_bgcolor = params['color'].loc[0,1],
        paper_bgcolor = params['color'].loc[0,1],
        width = params['width'], height = params['height'],
        showlegend = False, dragmode = False
    )

    ## define map-specific figure parameters
    parallel_offset = (49.38 - 24.54) * 1/6
    fig = fig.update_geos(

        ## specify map
        resolution = 50, scope = 'north america',
        center = dict(lat = 39.83 - 1.0, lon = -99.58),

        ## define map color sceme
        showcountries = False, 
        showcoastlines = True, coastlinecolor = params['color'].loc[25,2],
        showland = True, landcolor = params['color'].loc[0,2],
        showocean = True, oceancolor = params['color'].loc[0,2],
        showsubunits = True, subunitcolor = params['color'].loc[25,2],
        showlakes = True, lakecolor = params['color'].loc[0,2],

        ## define projection
        projection = dict(
            parallels = [49.38 - parallel_offset, 24.54 + parallel_offset],
            rotation = dict(lat = 39.83, lon = -99.58, roll = 0),
            type = 'conic conformal',
            scale = 3.3
        )
    )
    return fig


def build_route_trace(routes, trace_dict, hover = True, params = params):
    """
        TODO
    """

    ## set basic parameters
    route_traces = dict()
    hover_template = '<b>{0}</b><br>Segment: {1}<extra></extra>'
    set_linecolor = params['color'].loc[25,1]
    if hover:
        set_hoverinfo = 'all'
        set_prefix = 'R∆'
        set_visible = True
    else:
        set_hoverinfo = 'none'
        set_prefix = 'S∆'
        set_visible = False

    ## iterative add traces for each route segment
    for iter_segment in set(routes['segments']):

        idx = routes['segments'] == iter_segment
        if hover: hover_now = hover_template.format(
            routes.loc[idx, 'trip'].values[0], routes.loc[idx, 'segments'].values[0][2::])
        else: hover_now = None

        route_traces[iter_segment.replace('S∆', set_prefix)] = go.Scattergeo(
            lat = routes.loc[idx, 'lat'],
            lon = routes.loc[idx, 'lon'],
            hoverinfo = set_hoverinfo,
            hovertemplate = hover_now,
            hoverlabel = dict(
                align = 'right',
                font_color = params['color'].loc[50,1],
                bgcolor = params['color'].loc[0,1]
                ),
            marker = dict(
                color = set_linecolor,
                line = dict(width = 0.1)
                ),
            name = routes.loc[idx, 'trip'].values[0],
            mode = 'lines',
            visible = set_visible,
            showlegend = False
        )

    trace_dict.update(route_traces)
    return trace_dict


def build_city_trace(city_list, trace_dict, hover = False):
    """
        TODO
    """

    if hover:
        set_hoverinfo = 'all'
        set_prefix = 'M∆'
        set_visible = False
        set_hovertemplate = '%{customdata}<extra></extra>'
    else:
        set_hoverinfo = 'none'
        set_prefix = 'C∆'
        set_visible = True
        set_hovertemplate = None

    city_trace = dict()
    for iter_status in params['visit_colors'].keys():
        idx = city_list['status'] == iter_status
        name_now = iter_status + ' Cities'
        city_trace[set_prefix + name_now] = go.Scattergeo(
            lat = city_list.loc[idx, 'lat'],
            lon = city_list.loc[idx, 'lon'],
            customdata = city_list.loc[idx, 'hover_label'],
            hoverinfo = set_hoverinfo,
            hovertemplate = set_hovertemplate,
            hoverlabel = dict(
                align = 'right',
                font_color = params['color'].loc[params['visit_borders'][iter_status], 1],
                bgcolor = params['color'].loc[0,1]
                ),
            marker = dict(
                color = params['color'].loc[params['visit_colors'][iter_status], 1],
                size = params['city_size'],
                line = dict(
                    color = params['color'].loc[params['visit_borders'][iter_status], 1],
                    width = 1
                    ),
                ),
            name = name_now,
            mode = 'markers',
            visible = set_visible
            )
    trace_dict.update(city_trace)
    return trace_dict


def build_weather_trace(city_list, trace_dict, params = params):
    """
        TODO
    """
    ## prepare needed objects
    weather_traces = dict()
    weather_cols = city_list.columns[city_list.columns.str.startswith('W∆')].to_list()

    ## iteratively add traces for each weather score
    for iter_weather in weather_cols:

        ## generate iteration specific hover labels
        city_list['weather_label'] = '<b>' + city_list['city'].copy() + '</b>'
        city_list['weather_label'] += '<br>Temperate Hours: ' + city_list[iter_weather].astype(str)
        city_list['weather_label'] += '<br>Climate: ' + city_list['climate_major']
        city_list['weather_label'] += '<br>Summer: ' + city_list['climate_summer']
        city_list['weather_label'] += '<br>Winter: ' + city_list['climate_winter']
        city_list['weather_label'] += '<br>Koppen Type: ' + city_list['koppen']

        ## generate iteration specific colors
        city_list['weather_color'] = city_list[iter_weather] / 12
        city_list['weather_color'] = (city_list['weather_color']).round(1)

        ## render weather-based traces
        weather_traces[iter_weather] = go.Scattergeo(
            lat = city_list['lat'],
            lon = city_list['lon'],
            customdata = city_list['weather_label'],
            hovertemplate = '%{customdata}<extra></extra>',
            hoverlabel = dict(
                align = 'right',
                font_color = params['color'].loc[100, 3],
                bgcolor = params['color'].loc[0, 3]
                ),
            marker = dict(
                color = city_list['weather_color'],
                colorscale = [params['color'].loc[0,3], params['color'].loc[100,3]],
                size = params['city_size'],
                line = dict(color = params['color'].loc[50, 3], width = 1),
                ),
            name = iter_weather.replace('W∆', '')[3::],
            mode = 'markers',
            visible = False
        )

    trace_dict.update(weather_traces)
    return trace_dict


def formulate_slider_bar(trace_dict):
    """
        TODO
    """

    ## determine visibility toggles
    visibility = pd.DataFrame({'Layer': list(trace_dict.keys())})
    visibility['Travels:<br>Cities'] = visibility['Layer'].str.startswith('M∆')
    visibility['Travels:<br>Routes'] = (
        visibility['Layer'].str.startswith('R∆') | visibility['Layer'].str.startswith('C∆'))
    visibility['Temperate:<br>JAN'] = visibility['Layer'].str.startswith('W∆01')
    visibility['Temperate:<br>FEB'] = visibility['Layer'].str.startswith('W∆02')
    visibility['Temperate:<br>MAR'] = visibility['Layer'].str.startswith('W∆03')
    visibility['Temperate:<br>APR'] = visibility['Layer'].str.startswith('W∆04')
    visibility['Temperate:<br>MAY'] = visibility['Layer'].str.startswith('W∆05')
    visibility['Temperate:<br>JUN'] = visibility['Layer'].str.startswith('W∆06')
    visibility['Temperate:<br>JUL'] = visibility['Layer'].str.startswith('W∆07')
    visibility['Temperate:<br>AUG'] = visibility['Layer'].str.startswith('W∆08')
    visibility['Temperate:<br>SEP'] = visibility['Layer'].str.startswith('W∆09')
    visibility['Temperate:<br>OCT'] = visibility['Layer'].str.startswith('W∆10')
    visibility['Temperate:<br>NOV'] = visibility['Layer'].str.startswith('W∆11')
    visibility['Temperate:<br>DEC'] = visibility['Layer'].str.startswith('W∆12')
    visibility = visibility.set_index('Layer')

    ## assemble slider steps
    steps = list()
    for iter_step in visibility.columns:
        steps.append(
            dict(
                method = 'update',
                label = iter_step,
                args = [dict(visible = visibility[iter_step])]
                ))
        
    slider_bar = [dict(
        font = dict(size = 10), currentvalue = dict(font = dict(size = 12)),
        active = 1, steps = steps, pad = dict(b = 4, l = 16, r = 20)
        )]

    return slider_bar


def write_figure(fig, slider_bar, trace_dict):
    """
        TODO
    """
    fig = fig.add_traces([trace_dict[i] for i in trace_dict.keys()])
    fig = fig.update_layout(sliders = slider_bar)
    fig.write_html('io_mid/MAP.html', full_html = True, include_plotlyjs = True)
    fig.write_html('io_mid/MAP.div', full_html = False, include_plotlyjs = False)
    div = '\n'.join(open('io_mid/MAP.div', 'rt').readlines())
    return div

##########==========##########==========##########==========##########==========##########==========
## TOP-LEVEL FUNCTIONS

def draw_map_panel():
    """
        TODO
    """

    ## import and refine data
    city_list = import_city_list()
    city_list = add_weather_to_city(city_list = city_list)
    routes = import_routes()

    ## generate traces
    trace_dict = dict()
    trace_dict = build_route_trace(routes = routes, trace_dict= trace_dict, hover = True)
    trace_dict = build_route_trace(routes = routes, trace_dict= trace_dict, hover = False)
    trace_dict = build_city_trace(city_list = city_list, trace_dict= trace_dict, hover = True)
    trace_dict = build_city_trace(city_list = city_list, trace_dict= trace_dict, hover = False)
    trace_dict = build_weather_trace(city_list= city_list, trace_dict= trace_dict)

    ## formulate slider bar and assemble figure
    slider_bar = formulate_slider_bar(trace_dict = trace_dict)
    fig = make_figure()
    div = write_figure(fig = fig, slider_bar = slider_bar, trace_dict = trace_dict)
    return div

##########==========##########==========##########==========##########==========##########==========
## CODE TESTS
    
if __name__ == '__main__':
    draw_map_panel()

##########==========##########==========##########==========##########==========##########==========