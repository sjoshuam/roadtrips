"""
    Purpose: Tally basic statistics on progress achieving travel goals and depict as html-based
        visualizations.  Packge visualization code so it can slot into a div section within
        the project's main html page.
    Inputs:
        io_in/city_list.xlsx: provides information on the destinations I seek to visit and my
            progress visiting them.  Also provides information on color schema for figures.
    Outputs:
        io_mid/PROGRESS.html: self-contained, fully-functional html file with all data displays.
            Used during development to inspect data displays.  Is not tied into the project
            css file, so some stylistic elements will be of lower quality.
        io_mid/PROGRESS.div: html code contained inside a <div> tag, suitable for injection into
            the project's main html product.
    Open GitHub Issues:
        # None.  This file is good to go.
"""

##########==========##########==========##########==========##########==========##########==========
## INITIALIZE

## import packages
import warnings, sys
if not sys.prefix.endswith('.venv'): raise Exception('Virtual Environment Not Detected')  
import pandas as pd
import plotly.graph_objects as go

## set parameters
params = {
    'margin': 2**0,#5,
    'dimensions': (700 - 10, 392 - 10),
    'shading': {
        'border': {'Photographed':'L', 'Visited':'LM', 'Unvisited':'M', 'EMPTY': 'S'},
        'fill':   {'Photographed':'LM', 'Visited':'M', 'Unvisited':'S', 'EMPTY': 'S'}
    },
    'status_order': {'Photographed':'2','Visited':'1','Unvisited':'0'}
}

warnings.simplefilter(action='ignore', category=FutureWarning)

##########==========##########==========##########==========##########==========##########==========
## COMPONENT FUNCTIONS: Manipulate City Visit Data


def import_data() -> pd.DataFrame:
    """Import primary dataset (city_list) from xlsx and construct useful columns.
    output: city_list = a dataset of information about the cities on my travel list.
    """

    ## import and merge data
    city_list = pd.read_excel('io_in/city_list.xlsx', sheet_name = "Cities")

    ## derive unvisited/ visited/ photographed counts
    city_list['status'] = 'Unvisited'
    city_list.loc[city_list['visit'].astype(bool), 'status'] = 'Visited'
    city_list.loc[~city_list['photo_date'].isna(), 'status'] = 'Photographed'
    city_list['one'] = 'Total'

    return city_list


def import_color() -> pd.DataFrame:
    """Import color scheme, which is packaged in two tabs within the main city_list file.
    output: a matrix of colors, specified in hsva format.  Function use this file to 
        determine which colors on the plot.
    """
    colors = pd.read_excel('io_in/city_list.xlsx', sheet_name = "Color", index_col = 0)
    color_map = pd.read_excel('io_in/city_list.xlsx', sheet_name = "ColorMap").dropna()
    for iter_row in color_map.index:
        colors[color_map.loc[iter_row, 'key']] = colors[color_map.loc[iter_row, 'hue']]
    return colors


##########==========##########==========##########==========##########==========##########==========
## COMPONENT FUNCTIONS: Render waffle chart visualizations


def make_waffle(var:str, city_list:pd.DataFrame, colors:pd.DataFrame, params=params) -> pd.DataFrame:
    """Generates a pd.DataFrame with all the data necessary to draw a waffle plot, including
    colors, coordinates, and labels.
    Input:
        var = column name in city_list defining the groups for the plot
        city_list = city-wise dataframe (primary data object for this script)
        colors = matrix defining the color scheme for plots. The groups specified in var match
            columns in the color file
        params = dict of misc. parameters
    """

    ## determine the dimensions for the plot
    dim = city_list.shape[0]**0.5
    dim = (dim // 1) + int((dim % 1) > 0)
    dim = (int(dim), int(dim))

    ## create coordinates for each box
    waffle_data = pd.DataFrame({'x':range(1, dim[0]+1)})
    waffle_data = waffle_data.merge(pd.Series(range(1, dim[1]+1), name = 'y'), how = 'cross')
    waffle_data['x'] = (waffle_data['x'] / (dim[0] + 1)).round(3)
    waffle_data['y'] = (waffle_data['y'] / (dim[1] + 1)).round(3)
    waffle_data['x'] = waffle_data['x'] * 0.8
    waffle_data = waffle_data.sort_values(['x', 'y'], ascending=[True, False])
    waffle_data = waffle_data.reset_index(drop=True)

    ## create empty slots for needed data
    waffle_data['label'] = 'EMPTY'
    waffle_data['status'] = 'EMPTY'
    waffle_data['var'] = 'grey'
    waffle_data['unused'] = True

    ## enhance city list
    city_list['count_status'] = city_list['status'].replace(params['status_order'])
    city_list = city_list.merge(
            city_list[var].value_counts(), how = 'left', left_on = var, right_index = True)
    city_list = city_list.sort_values(
        ['count', 'count_status', 'city'], ascending= [False, False, True])
    city_list = city_list.reset_index(drop = True)

    ## label cells, looping through each city
    var_then = city_list.at[city_list.index[0], var]
    by_x = True
    for iter_row in city_list.index:
        var_now = city_list.at[iter_row, var]

        ## determine fill direction
        if var_now != var_then:
            if by_x: waffle_data = waffle_data.sort_values(['y', 'x'])
            else: waffle_data    = waffle_data.sort_values(['x', 'y'])
            by_x = not by_x
            waffle_data = waffle_data.reset_index(drop=True)

        ## fill first available cell
        first_unused = waffle_data.index[waffle_data['unused']][0]
        waffle_data.at[first_unused, 'label'] = city_list.at[iter_row, 'city']
        waffle_data.at[first_unused, 'status'] = city_list.at[iter_row, 'status']
        waffle_data.at[first_unused, 'var'] = city_list.at[iter_row, var]
        waffle_data.at[first_unused, 'unused'] = False
        var_then = var_now

    ## assign colors
    waffle_data['border'] = waffle_data['status'].replace(params['shading']['border'])
    waffle_data['fill'] = waffle_data['status'].replace(params['shading']['fill'])
    for iter_row in waffle_data.index:
        waffle_data.at[iter_row, 'border'] = colors.at[
            waffle_data.at[iter_row, 'border'], waffle_data.at[iter_row, 'var']]
        waffle_data.at[iter_row, 'fill'] = colors.at[
            waffle_data.at[iter_row, 'fill'], waffle_data.at[iter_row, 'var']]
    for iter_var in ['label', 'status', 'var']:
        waffle_data[iter_var] = waffle_data[iter_var].replace({'grey':'', 'EMPTY':''})

    ## incorporate trace order into waffle_data
    trace_order = city_list.groupby(var).agg({'count':max})
    trace_order = trace_order.reset_index().rename(columns={'count':'order', var:'var'})
    waffle_data = waffle_data.merge(right=trace_order, how='left', on='var')
    waffle_data = waffle_data.fillna({'order':0}).astype({'order':int})

    ## clean up and return results
    del waffle_data['unused']
    waffle_data = waffle_data.sort_values(['x', 'y']).reset_index()
    return waffle_data


def make_legend(waffle_data: pd.DataFrame, params=params) -> pd.DataFrame:
    """ The color scheme for the waffle plot is based on the two variables, requiring a customized
    legend.  This function generates a dataframe with all the information needed to draw it.
    Inputs:
        waffle_data = dataframe with all the information need to draw a waffle plot.
        params = dict of misc. parameters
    """
    ## set boundary conditions on legend
    y_values= list(reversed(sorted(waffle_data['y'].unique())))[1::]
    test_values = {
        'var': len(waffle_data['var'].unique()),
        'status': len(waffle_data['status'].unique()),
        'y': len(y_values)
    }
    assert test_values['status'] <= test_values['y'], 'Too many categories (status)'
    assert test_values['var'] <= test_values['y'], 'Too many categories (var)'

    ## prep waffle_data for filtering
    legend_data= waffle_data.copy().drop(columns=['x','label'])
    legend_data['status_order']= legend_data['status'].replace(params['status_order'])
    legend_data= legend_data.sort_values(['order', 'status_order','y'], ascending=False)
    legend_data= legend_data.loc[legend_data['status'] != '', legend_data.columns != 'y']

    ## find unique status and var
    idx_status = legend_data.loc[legend_data['var'] == legend_data.loc[0,'var']].copy()
    idx_status = idx_status.loc[~idx_status['status'].duplicated()].index.values
    idx_var = legend_data.loc[~legend_data['var'].duplicated()].index.values
    legend_data['type'] = 0
    legend_data.loc[idx_status, 'type'] += 1
    legend_data.loc[idx_var, 'type']    += 3
    legend_data = legend_data.loc[legend_data['type'] > 0]
    legend_data['type'] = legend_data['type'].replace({4:2})

    ## assign y coordinates
    legend_data['xy'] = 0.
    legend_data.loc[legend_data['type'] < 3,'y'] = y_values[0:sum(legend_data['type'] < 3)]
    legend_data.loc[legend_data['type'] > 1,'y'] = y_values[0:sum(legend_data['type'] > 1)]

    ## assign x coordinates
    legend_data = legend_data.loc[[legend_data.index.tolist()[0]]+legend_data.index.tolist()]
    legend_data.loc[legend_data['type'] == 2,'type'] = [1,3]
    legend_data['x'] = legend_data['type'].replace({3:0.9, 1:1.3})

    ## assign labels
    legend_data['label']= legend_data['status']
    legend_data.loc[legend_data['type']==3,'label']= legend_data.loc[legend_data['type']==3,'var']

    return legend_data.reset_index(drop=True)


##########==========##########==========##########==========##########==========##########==========
## COMPONENT FUNCTIONS: Draw Figure


def make_figure(params=params) -> go.Figure:
    """ Initialize an empty plotly object, so that write_figure can append visualization traces
    to it and write it to disk as html code (a div)
    Input: params = misc. parameters
    """
    fig = go.Figure()
    fig = fig.update_layout(
        width=params['dimensions'][0],
        height=params['dimensions'][1],
        plot_bgcolor='hsva(0,0,0,0)',
        paper_bgcolor='hsva(0,0,0,0)',
        font=dict(color='hsva(0,0,100,0)'),
        margin=dict(
            r=params['margin'],
            l=params['margin'] * 2**1,
            t=params['margin'],
            b=params['margin']
            ),
        xaxis=dict(
            range=(0, params['dimensions'][0] / params['dimensions'][1]),
            visible=False
            ),
        yaxis=dict(
            range=(0, 1),
            visible=False
            ),
        dragmode=False
        )
    return fig


def write_figure(fig: go.Figure, trace_dict: dict, slider=None) -> str:
    """ Add sliders and traces to a plotly figure.  Write figure as both a self-contained html
    file and also as an html div section.  The self-contained file is for testing / trouble-
    shooting.  0_executve_project.py injects the div code into a data dashboard.
    Inputs:
        fig = An empty plotly figure
        trace_dict =  a dict of plotly traces, which are added to fig
        slider = plotly slider specifications, which are also added to fig
    """
    fig = fig.add_traces([trace_dict[i] for i in trace_dict.keys()])
    fig = fig.update_layout(sliders = slider)
    fig.write_html('io_mid/PROGRESS.html', full_html=True, include_plotlyjs=True)
    fig.write_html('io_mid/PROGRESS.div', full_html=False, include_plotlyjs=False)
    div = '\n'.join(open('io_mid/PROGRESS.div', 'rt').readlines())
    return div


def draw_waffle(name:str, waffle:pd.DataFrame, trace_dict:dict, size=20, visible=False) -> dict:
    """ Draws a waffle plot, using the plotly scatter plot function.  make_waffle() does all the
    calculations in advance.  draw_waffle() supplies the output from make_waffle() to the scatter
    plot function.  draw_waffle()'s output is a dict, ready to be appended to trace_dict, which
    stores all traces until write_figure() can add them to the plotly figure object.
    Inputs:
        name = a string that will uniquely identify this trace within trace_dict.  Serves as part
            of a dict key.
        waffle = output of make_waffle(); contains all the data needed to draw the waffle plot.
        trace_dict = A dict containing all of the plotly traces drawn so far.  draw_waffle() 
            adds a new trace as a new key-value pair in the dict.
        size = Size of the waffle squares; informs go.Scatter()'s marker size.
        visible = boolean for whether the trace is visible.  The plotly figure employs
            a slider bar, so that the user can toggle between multiple useful data visualizations.
            The slider acts on this setting to make different elements visible or invisible.
    """
    
    ## render waffle plot (scatterplot of squares)
    trace = go.Scatter(
        x=waffle['x'],
        y=waffle['y'],
        mode='markers',
        text=waffle['label'] + '<br>' + name.title() + ': ' + waffle['var'],
        customdata=waffle['status'],
        hoverinfo = None,
        hovertemplate='%{text}<br>Status: %{customdata}<extra></extra>',
        marker=dict(
            color=waffle['fill'], size=size, symbol='square',
            line=dict(width=2, color=waffle['border'])),
        showlegend=False,
        visible=visible
    )
    trace_dict.update({name + '∆waffle':trace})

    return trace_dict


def draw_legend(name:str, legend:pd.DataFrame, trace_dict:dict, colors:pd.DataFrame, size=20,
                visible=False) -> dict:
    """ Draws a waffle plot legend, using the plotly scatter plot function.  make_legend() does
    the calculations in advance.  draw_legend() supplies the output from make_legend() to the
    scatter plot function.  draw_legend()'s output is a dict, ready to be appended to trace_dict.
    Inputs:
        name = a string that will uniquely identify this trace within trace_dict.  Serves as part
            of a dict key.
        legend = output of make_legend(); contains all the data needed to draw the waffle legend.
        trace_dict = A dict containing all of the plotly traces drawn so far. Functions adds a new
            trace as a new key-value pair in the dict.
        colors = dataframe defining the colors used in the figures.
        size = Size of the waffle squares; informs go.Scatter()'s marker size.
        visible = boolean for whether the trace is visible.  The plotly figure employs
            a slider bar, so that the user can toggle between multiple useful data visualizations.
            The slider acts on this setting to make different elements visible or invisible.
    """
    trace = go.Scatter(
        x= legend['x'],
        y= legend['y'],
        mode= 'markers+text',
        text= legend['label'],
        textfont= dict(color=colors.loc['L','grey']),
        textposition= 'middle right',
        hoverinfo= 'skip',
        marker= dict(
            color= legend['fill'], size=size, symbol = 'square',
            line= dict(width=2, color=legend['border'])),
        showlegend= False,
        visible = visible
    )
    trace_dict.update({name + '∆legend':trace})

    return trace_dict


def add_slider(trace_dict:dict, colors:pd.DataFrame, order=['Total','Criteria','Region']) -> list:
    """ Generates slider specifications for the plotly object.
    Input:
        trace_dict = A dict containing all of the plotly traces drawn so far. The slider controls
            which traces are visible.
        colors = dataframe defining the colors used in the figures.
        order = Determines the order in which plots are listed in the figure's slider.
    """

    ## generate visibility information
    if order is None: visible= list(set([i.split('∆')[0] for i in trace_dict.keys()]))
    else: visible= order
    visible= {i:[j.startswith(i) for j in trace_dict.keys()] for i in visible}

    ## package visibility information in step format
    for iter_step in visible.keys():
        visible[iter_step] = dict(
            method= 'update',
            label = iter_step,
            args = [dict(visible=visible[iter_step])]
        )
    visible = [visible[i] for i in visible.keys()]

    ## package visibility information in slider format
    slider = [dict(
        font = dict(size = 10, color = colors.loc['L','grey']),
        currentvalue=dict(font = dict(size = 12), prefix='Destinations Visited: '),
        active = 0, steps = visible, pad = dict(b=0, l=8, r=8, t=0)
        )]

    return slider


##########==========##########==========##########==========##########==========##########==========
## TOP-LEVEL FUNCTIONS


def draw_progress_panel() -> None:
    """ Executes all of the functions defined above.  Loaded in 0_execute_project.py in order
    to execute the full project.
    """

    ## import and refine data
    city_list = import_data()
    colors = import_color()
    
    ## generate waffle data
    status_waffle   = make_waffle(var='one', city_list=city_list, colors=colors)
    criteria_waffle = make_waffle(var='state_criteria', city_list=city_list, colors=colors)
    region_waffle   = make_waffle(var='region', city_list=city_list, colors=colors)
    
    ## generate legend data
    status_legend   = make_legend(waffle_data=status_waffle)
    region_legend   = make_legend(waffle_data=region_waffle)
    criteria_legend = make_legend(waffle_data=criteria_waffle)

    ## draw waffles
    trace_dict = dict()
    trace_dict = draw_waffle(
        name='Total', waffle=status_waffle, trace_dict=trace_dict, visible=True)
    trace_dict = draw_waffle(name='Criteria', waffle=criteria_waffle, trace_dict=trace_dict)
    trace_dict = draw_waffle(name='Region', waffle=region_waffle, trace_dict=trace_dict)

    ## draw legends
    trace_dict = draw_legend(
        name='Total', legend=status_legend, trace_dict=trace_dict, colors=colors, visible=True)
    trace_dict = draw_legend(
        name='Criteria', legend=criteria_legend, trace_dict=trace_dict, colors=colors)
    trace_dict = draw_legend(
        name='Region', legend=region_legend, trace_dict=trace_dict, colors=colors)

    ## generate slider
    slider= add_slider(trace_dict, colors=colors)

    ## attach waffles and legends to figure object, then write to disk as html div code
    fig = make_figure()
    write_figure(fig=fig, trace_dict=trace_dict, slider=slider)
    return None


##########==========##########==========##########==========##########==========##########==========
## CODE TESTS

if __name__ == '__main__':
    draw_progress_panel()

##########==========##########==========##########==========##########==========##########==========