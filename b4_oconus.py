"""
    Purpose: Depicts the four destinations outside the contiguous United States (in DC parlance,
        those destinations are OCONUS) as well as a map key. Packge visualization so it can
        slot into a div section within the project's main html page.
    Inputs: 
        b3_map: imports functions function b3_map in order to keep the two displays synced.
        io_in/color.xlsx: centralized color palette for the project
    Outputs:
        io_mid/OCONUS.html: self-contained, fully-functional html file with all data displays.
            Used during development to inspect data displays.  Is not tied into the project
            css file, so some stylistic elements will be of lower quality.
        io_mid/OCONUS.div: html code contained inside a <div> tag, suitable for injection into
            the project's main html product.
    Open GitHub Issues:
        #14 Add doc strings to all functions
        #16 Wire module into a run-everything execute_project() function in 0_execute_project.py
        #21 Rerender dots are part of the main panel and make this one purely a centralized key.
"""
##########==========##########==========##########==========##########==========##########==========
## INITIALIZE

## import packages
import os, sys
if not sys.prefix.endswith('.venv'): raise Exception('Virtual Environment Not Detected')  
import pandas as pd
import plotly.graph_objects as go
import b3_map

## define parameters
params = dict()
params['width']  = 500 - 10
params['height'] = 118 - 10
params['color'] = pd.read_excel(os.path.join('io_in', 'colors.xlsx'), index_col = 0)
params['visit_colors'] =  {'Photographed': 50, 'Visited': 25, 'Unvisited': 0}
params['visit_borders'] = {'Photographed': 100, 'Visited': 50, 'Unvisited': 25}
params['city_size'] = b3_map.params['city_size']


##########==========##########==========##########==========##########==========##########==========
## COMPONENT FUNCTIONS

def extract_oconus_data(city_list):
    """
        TODO
    """

    ## limit to just oconus destination
    city_list = city_list.fillna({'not': ''}).sort_values('state')
    city_list = city_list.loc[city_list['not'].str.endswith('conus')].reset_index(drop = True)
    city_list['x'] = 20
    city_list['y'] = [(params['height'] - 40) - (20 * i) for i in range(0, city_list.shape[0])]

    ## ensure legend is complete
    fallback = pd.DataFrame({'status': list(params['visit_colors'].keys())})
    fallback['x'] = -20
    fallback['y'] = -20
    fallback['city'] = 'NULL'
    city_list = pd.concat([city_list, fallback])

    return city_list


def create_figure(city_list):
    """Creates a plotly figure object with suitable parameters"""
    fig = go.Figure()
    fig = fig.update_layout(
        template = 'plotly_dark',
        xaxis = dict(range = [0, params['width']], visible = False),
        yaxis = dict(range = [0, params['height']], visible = False),
        margin = dict(l = 0, r = 0, t = 0, b = 0),
        font = dict(color = params['color'].loc[100,1]),
        showlegend = True,
        width = params['width'], height = params['height'],
        plot_bgcolor = params['color'].loc[0,1],
        paper_bgcolor = params['color'].loc[0,1],
        dragmode = False,
        legend = dict(
            x = 0.4, y = 0.8, yanchor = 'top', xanchor = 'left',
            title = 'KEY: Destinations',
            )
    )

    return fig


def build_oconus_trace(city_list):
    """
        TODO
    """
    trace_dict = dict()
    for iter_status in params['visit_colors'].keys():
        idx = city_list['status'] == iter_status
        name_now = iter_status + ' Cities'
        trace_dict[name_now] = go.Scatter(
            x = city_list.loc[idx, 'x'],
            y = city_list.loc[idx, 'y'],
            text = city_list.loc[idx, 'city'],
            customdata = city_list.loc[idx, 'hover_label'],
            hovertemplate = '%{customdata}<extra></extra>',
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
                    width = 1),
                ),
            name = name_now, mode = 'markers+text',
            textfont = dict(color = params['color'].loc[params['visit_borders'][iter_status], 1]),
            textposition = 'middle right'
            )
    return trace_dict


def write_figure(fig, trace_dict):
    """
        TODO
    """
    fig = fig.add_traces([trace_dict[i] for i in trace_dict.keys()])
    fig.write_html('io_mid/OCONUS.html', full_html = True, include_plotlyjs = True)
    fig.write_html('io_mid/OCONUS.div', full_html = False, include_plotlyjs = False)
    div = '\n'.join(open('io_mid/OCONUS.div', 'rt').readlines())
    return div


##########==========##########==========##########==========##########==========##########==========
## TOP-LEVEL FUNCTIONS

def draw_oconus_panel():
    """
        TODO
    """
    city_list = b3_map.import_city_list()
    city_list = extract_oconus_data(city_list)
    fig = create_figure(city_list)
    trace_dict = build_oconus_trace(city_list)
    div = write_figure(fig, trace_dict)
    return div

##########==========##########==========##########==========##########==========##########==========
## CODE TESTS
    
if __name__ == '__main__':
    draw_oconus_panel()

##########==========##########==========##########==========##########==========##########==========