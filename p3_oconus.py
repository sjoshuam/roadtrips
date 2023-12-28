"""
    TODO
"""
##########==========##########==========##########==========##########==========##########==========
## INITIALIZE

## import packages
import pandas as pd
import plotly.graph_objects as go
import p2_map

## define parameters
params = p2_map.params
params['width']  = 400
params['height'] = 120

##########==========##########==========##########==========##########==========##########==========
## COMPONENT FUNCTIONS

def extract_oconus_data(city_list):
    """
        TODO
    """
    city_list = city_list.fillna({'not': ''}).sort_values('state')
    city_list = city_list.loc[city_list['not'].str.endswith('conus')].reset_index(drop = True)
    city_list['x'] = 20
    city_list['y'] = [(params['height'] - 40) - (20 * i) for i in range(0, city_list.shape[0])]
    return city_list


def create_figure(city_list):
    """Creates a plotly figure object with suitable parameters"""
    fig = go.Figure()
    fig = fig.update_layout(
        template = 'plotly_dark',
        xaxis = dict(range = [0, params['width']], visible = False),
        yaxis = dict(range = [0, params['height']], visible = False),
        margin = dict(l = 0, r = 0, t = 0, b = 0),
        showlegend = False,
        width = params['width'], height = params['height'],
        plot_bgcolor = params['figure_colors']['bg'],
        paper_bgcolor = params['figure_colors']['bg'],
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
                font_color = params['visit_colors'][iter_status][1],
                bgcolor = params['figure_colors']['bg']
                ),
            marker = dict(
                color = params['visit_colors'][iter_status][0],
                size = 2**4,
                line = dict(color = params['visit_colors'][iter_status][1], width = 1),
                ),
            name = name_now, mode = 'markers+text',
            textfont = dict(color = params['visit_colors'][iter_status][1]),
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
    city_list = p2_map.import_city_list()
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