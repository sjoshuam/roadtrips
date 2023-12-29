##########==========##########==========##########==========##########==========##########==========
## INITIALIZE

## import packages
import os
import pandas as pd
import plotly.graph_objects as go
from xml.dom.minidom import parse as xml_parse

## define parameters
params = dict(
    width = 1200 * 0.95, height = 720 * 0.95,
    figure_colors = dict(bg= 'hsv(000,00,00)', fg= 'hsv(000,00,100)', mg= 'hsv(000,00,40)'),
    map_colors = dict(
        land = 'hsv(000,00,05)', water = 'hsv(000,00,00)',
        coast = 'hsv(000,00,20)', border= 'hsv(000,00,20)',
        ),
    visit_colors = dict(
        Unvisited    = ('hsv(030,00,00)', 'hsv(030,00,55)'),
        Visited      = ('hsv(090,20,30)', 'hsv(090,70,70)'),
        Photographed = ('hsv(150,20,30)', 'hsv(150,70,70)')
        ),
    city_size = 2**3
    )

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


def add_weather_to_city(city_list):
    """
        TODO
    """
    weather_data = pd.read_excel(os.path.join('io_mid', 'weather_data.xlsx'), index_col = 0)
    weather_data.columns = 'weather_' + weather_data.columns
    city_list = city_list.merge(
        right = weather_data, how = 'left', left_on = 'noaa_station', right_index = True)
    ##city_list = city_list.fillna({i:0 for i in weather_data.columns})
    return city_list


def import_routes():
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
        elem = elem.getElementsByTagName('Placemark')[1::]
        elem_name = [i.getElementsByTagName('name')[0].firstChild.nodeValue for i in elem]
        elem_xy = [refine_xy(i) for i in elem]
        return {elem_name[i]:elem_xy[i] for i in range(0, len(elem_name))}
    x = {i.getElementsByTagName('name')[0].firstChild.nodeValue: extract_elements(i) for i in x}

    ## flatten extract data
    x = {i:x[i] for i in x.keys() if i != 'Travels'}
    x = {i:pd.concat(x[i]) for i in x.keys()}
    x = pd.concat([x[i].assign(**{'trip': i}) for i in x.keys()]).reset_index()
    x = x.rename(columns = {'level_0': 'segments', 'level_1': 'order'})
    x['segments'] = 'segment_' + x['segments']

    ## simplify data
    x['dedup'] = x['trip'] + x['segments'] + (
        x['lon'].round(2).astype(str) + x['lat'].round(2).astype(str))
    x = x.loc[~x['dedup'].duplicated(), x.columns != 'dedup']


    print(x)
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


def build_route_trace(routes, params = params):
    """
        TODO
    """
    route_traces = dict()
    for iter_segment in set(routes['segments']):
        idx = routes['segments'] == iter_segment
        route_traces[iter_segment] = go.Scattergeo(
            lat = routes.loc[idx, 'lat'],
            lon = routes.loc[idx, 'lon'],
            customdata = routes.loc[idx, 'trip'],
            hovertemplate = 'Trip: %{customdata}<extra></extra>',
            hoverlabel = dict(
                align = 'right',
                font_color = params['visit_colors']['Photographed'][1],
                bgcolor = params['figure_colors']['bg']
                ),
            marker = dict(
                color = params['visit_colors']['Photographed'][1],
                size = 0.1,
                line = dict(color = params['visit_colors']['Photographed'][1], width = 0.1),
                ),
            name = routes.loc[idx, 'trip'].values[0],
            mode = 'lines',
            visible = True
        )
    return route_traces


def build_city_trace(city_list, trace_dict):
    """
        TODO
    """
    city_trace = dict()
    for iter_status in params['visit_colors'].keys():
        idx = city_list['status'] == iter_status
        name_now = iter_status + ' Cities'
        city_trace[name_now] = go.Scattergeo(
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
                size = params['city_size'],
                line = dict(color = params['visit_colors'][iter_status][1], width = 1),
                ),
            name = name_now,
            mode = 'markers'
            )
    trace_dict.update(city_trace)
    return trace_dict


def build_weather_trace(city_list, trace_dict, params = params):
    """
        TODO
    """
    ## prepare needed objects
    weather_traces = dict()
    weather_cols = city_list.columns[city_list.columns.str.startswith('weather_')].to_list()

    ## iteratively add traces for each weather score
    for iter_weather in weather_cols:

        ## generate iteration specific data
        city_list['weather_label'] = city_list['hover_label'].copy()
        new_text = '<br>Temperate Hours: ' + city_list[iter_weather].astype(str)
        city_list['weather_label'] = city_list['weather_label'] + new_text
        city_list['weather_color'] = city_list[iter_weather] / 12
        city_list['weather_color'] = (city_list['weather_color'] / (1/6)).round() * (1/6)

        ## render weather-based traces
        weather_traces[iter_weather] = go.Scattergeo(
            lat = city_list['lat'],
            lon = city_list['lon'],
            customdata = city_list['weather_label'],
            hovertemplate = '%{customdata}<extra></extra>',
            hoverlabel = dict(
                align = 'right',
                font_color = params['figure_colors']['fg'],
                bgcolor = params['figure_colors']['bg']
                ),
            marker = dict(
                color = city_list['weather_color'],
                colorscale = ['hsv(330,00,00)', 'hsv(330,80,80)'],
                size = params['city_size'],
                line = dict(color = params['figure_colors']['mg'], width = 1),
                ),
            name = iter_weather.replace('weather_', '')[3::],
            mode = 'markers',
            visible = False
        )

    trace_dict.update(weather_traces)
    return trace_dict


def formulate_slider_bar(trace_dict):
    """
        TODO
    """
    
    ## generate slider layers for for places visited
    places_visited = dict(method = 'update', label = 'Travels',
        args = [dict(
            visible = [i.endswith('Cities') or i.startswith('segment_') for i in trace_dict.keys()]
            )])
    
    ## generate slide layers for weather
    weather_steps = list(trace_dict.keys())
    weather_steps = [i for i in weather_steps if i.startswith('weather_')]
    weather_slides = list()
    for iter_weather in weather_steps:
        weather_slides.append(
            dict(
                method = 'update', label = iter_weather.replace('weather_', '')[3::],
                args = [dict(visible = [i == iter_weather for i in trace_dict.keys()])]
                )
        )

    
    ## compile slider layers
    steps = [places_visited] + weather_slides

    return [dict(currentvalue = dict(prefix = 'Travels and Weather Conditions: '),
        active = 0, steps = steps, pad = dict(b = 4, l = 16, r = 20))]


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
    trace_dict = build_route_trace(routes = routes)
    trace_dict = build_city_trace(city_list = city_list, trace_dict= trace_dict)
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