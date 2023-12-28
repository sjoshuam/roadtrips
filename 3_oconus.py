"""
    TODO
"""
##########==========##########==========##########==========##########==========##########==========
## INITIALIZE

## import packages
import pandas as pd
import plotly.graph_objects as go

## define parameters
params = {
    'colors': {
        'bg_color': 'hsv(000,00,00)', 'mg_color': 'hsv(000,00,40)', 'fg_color': 'hsv(000,00,99)'},
        'visit_colors': ['hsv(30,30,00)', 'hsv(150,30,20)'],
        'visit_line_colors': ['hsv(30,00,55)', 'hsv(150,70,70)'],
    'dimensions': (400 - 5, 720 - 5)
    }
##########==========##########==========##########==========##########==========##########==========
## COMPONENT FUNCTIONS

def extract_oconus_data():
    """
        TODO
    """

    ## import data
    city_list = pd.read_excel('io_in/city_list.xlsx', sheet_name= 'Cities', index_col= 0)

    ## extract and refine data on oconus cities
    city_list = city_list.fillna({'not': ''}).sort_values('state')
    city_list = city_list.loc[city_list['not'].str.endswith('conus')].reset_index(drop = True)
    city_list['visit_color'] = 0.00
    city_list.loc[city_list['visit'].astype(bool), 'visit_color'] = 0.4
    city_list.loc[~city_list['photo_date'].isna(), 'visit_color'] = 1.00

    ## generate coordinates
    city_list['x'] = 0.2
    city_list['y'] = 1 - (city_list.index.values + 1)  / (city_list.index.values.max() + 2)

    ## fill in missing data and format
    ## TODO
    city_list = city_list.fillna({'miles': 'TODO', 'photo_date': 'Never'})
    city_list['state_criteria'] = city_list['state_criteria'].str.capitalize()

    ## formulate hover labels
    htxt = '<br>'.join([
        'Inclusion Criteria: {state_criteria}',
        'Miles Walked: {miles}',
        'Last Photographed: {photo_date}'
        ])
    for iter_row in city_list.index:
        city_list.loc[iter_row, 'hover_label'] = htxt.format(**dict(city_list.loc[iter_row]))
    

    return city_list


def create_figure(city_list):
    """Creates a plotly figure object with suitable parameters"""
    fig = go.Figure()
    fig = fig.update_layout(
        template = 'plotly_dark',
        xaxis = dict(range = [0, 1], visible = False),
        yaxis = dict(range = [0, 1], visible = False),
        margin = dict(l = 0, r = 0, t = 0, b = 0),
        legend = dict(visible = False),
        width = params['dimensions'][0], height = params['dimensions'][1],
        plot_bgcolor = params['colors']['bg_color'],
        paper_bgcolor = params['colors']['bg_color'],
    )

    return fig


def draw_oconus_list(city_list, params = params):
    """
        TODO
    """
    trace_dict = dict()
    trace_dict['cities'] = go.Scatter(
        x = city_list['x'], y = city_list['y'],
        marker = dict(
            color = city_list['visit_color'], size = 2**4,
            colorscale = params['visit_colors'],
            cmin = 0, cmax = 1,
            line = dict(
                color = city_list['visit_color'],
                colorscale = params['visit_line_colors'],
                width = 1)
            ),
        text = city_list['city'],
        mode = 'markers+text',
        textposition = 'middle right',
        textfont = dict(size = 12, color = params['colors']['fg_color']),
        customdata = city_list['hover_label'].fillna('Never'),
        hovertemplate = '<b>%{text}</b><br>%{customdata}',
        hoverlabel = dict(
            align = 'right',
            font_color = params['colors']['fg_color'],
            bgcolor = params['colors']['bg_color']
            ),
        name = 'Destinations'

        )
    return trace_dict


def write_figure(fig, trace_dict):
    """
        TODO
    """
    fig = fig.add_traces([trace_dict[i] for i in trace_dict.keys()])
    fig.write_html('io_out/OCONUS.html', full_html = True, include_plotlyjs = True)
    fig.write_html('io_mid/OCONUS.div', full_html = False, include_plotlyjs = False)
    div = '\n'.join(open('io_mid/OCONUS.div', 'rt').readlines())
    return div


##########==========##########==========##########==========##########==========##########==========
## TOP-LEVEL FUNCTIONS

def draw_oconus_panel():
    pass

##########==========##########==========##########==========##########==========##########==========
## CODE TESTS
    
if __name__ == '__main__':
    city_list = extract_oconus_data()
    trace_dict = draw_oconus_list(city_list)
    fig = create_figure(city_list)
    write_figure(fig, trace_dict = trace_dict)

##########==========##########==========##########==========##########==========##########==========