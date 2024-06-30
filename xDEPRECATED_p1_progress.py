"""
    Purpose: Tally basic statistics on progress achieving travel goals and depict as html-based
        visualizations.  Packge visualization code so it can slot into a div section within
        the project's main html page.
    Inputs:
        io_in/city_list.xlsx: provides information on the destinations I seek to visit and my
            progress visiting them.
        io_in/color.xlsx: centralized color palette for the project
    Outputs:
        io_mid/PROGRESS.html: self-contained, fully-functional html file with all data displays.
            Used during development to inspect data displays.  Is not tied into the project
            css file, so some stylistic elements will be of lower quality.
        io_mid/PROGRESS.div: html code contained inside a <div> tag, suitable for injection into
            the project's main html product.
        io_mid/STATS.txt: plain text file containing statistics to be injected into the text of
            the project's main html product.  Currently, only used to modify one sentence.
    Open GitHub Issues:
        #2 Resolve a minor code weakpoint arising from PR being both not a state and part of the
            contiguous USA.  Currently doesn't cause problems; this is just preventative.
        #14 Add doc strings to all functions
        #16 Wire module into a run-everything execute_project() function in 0_execute_project.py

"""
##########==========##########==========##########==========##########==========##########==========
## INITIALIZE

## import packages
import os
import pandas as pd
import plotly.graph_objects as go

## set parameters
params = {
    'bar_colors': {'Photographed': 50, 'Visited': 25, 'Unvisited': 0},
    'bar_borders': {'Photographed': 100, 'Visited': 50, 'Unvisited': 25},
    'margin': 2**5,
    'initial_slider': 'By Region',
    'dimensions': (750 - 10, 392 - 10)
}

params['color'] = pd.read_excel(os.path.join('io_in', 'colors.xlsx'), index_col = 0)
params['visit_colors'] =  {'Photographed': 50, 'Visited': 25, 'Unvisited': 0}
params['visit_borders'] = {'Photographed': 100, 'Visited': 50, 'Unvisited': 25}

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


    ## sum by city at the regional level
    city_list = city_list[group_cols + list(stat_cols.keys())].groupby(group_cols).agg(stat_cols)
    city_list['total'] = city_list[['Photographed','Visited','Unvisited']].sum(axis = 1)

    ### sum by city at the national level
    sum_list = pd.DataFrame({'USA':city_list.sum()}).T
    sum_list.index = sum_list.index.set_names(city_list.index.names)

    ## return
    progress = {
        'By Region': city_list.reset_index(),
        'Total': sum_list.reset_index(),

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
        width = params['dimensions'][0],
        height = params['dimensions'][1],
        plot_bgcolor = params['color'].loc[0,1],
        paper_bgcolor = params['color'].loc[0,1],
        polar = dict(bgcolor = params['color'].loc[0,1]),
        font = dict(color = params['color'].loc[100,1]),
        margin = dict(
            r = params['margin'],
            l = params['margin'] * 2**1,
            t = params['margin'],
            b = params['margin']
            ),
        polar_angularaxis = dict(direction = 'clockwise',
            gridcolor = params['color'].loc[0,1],
            showgrid = False,
            showticklabels = True,
            ticktext = tick_names.reset_index()['region'],
            tickvals = tick_names['theta'],
            tickmode = 'array',
            griddash = 'dash'
            ),
        polar_radialaxis = dict(
            gridcolor = params['color'].loc[0,1],
            showgrid = False,
            showticklabels = False,
            griddash = 'dash',
            showline = False,
            ),
        legend_title_text = 'KEY: Destinations',
        dragmode = False,
        legend = dict(x = 0)

    )
    return fig


def draw_region_bars(city_list, progress, trace_dict, params = params):
    """
        TODO
    """
    bar_traces = dict()
    for iter_bar in ['Photographed', 'Visited', 'Unvisited']:

        radius_now = ((progress['By Region'][iter_bar] / progress['By Region']['total']
            ).round(2) * 100).astype(int)
        label_now = '<b>Destinations in the ' + progress['By Region']['region'] + ' Region</b><br>'
        label_now += iter_bar + ': ' + radius_now.astype(str) + '%'

        bar_traces['By Region_' + iter_bar] = go.Barpolar(
            theta = progress['By Region']['theta'],
            width = progress['By Region']['width'],
            r = radius_now,
            name = iter_bar,
            visible = 'By Region' == params['initial_slider'],
            text = progress['By Region']['region'],
            marker_color = params['color'].loc[params['visit_colors'][iter_bar], 1],
            marker_line = dict(
                color = params['color'].loc[12, 1],
                width = 1
                ),
            hovertemplate = '%{customdata}<extra></extra>',
            customdata = label_now,
            hoverlabel = dict(
                font_color = params['color'].loc[params['bar_borders'][iter_bar], 1],
                bgcolor = params['color'].loc[0,2]
                ),
        )
    trace_dict.update(bar_traces)
    return trace_dict


def draw_bars(progress, trace_dict, params = params):
    """
        TODO
    """
    bar_traces = dict()
    status_names = list(params['visit_colors'].keys())
    status_colors = [params['color'].loc[i, 1] for i in params['visit_colors'].values()]
    status_count = progress['Total'].loc[0, status_names].astype(int)
    status_label = (status_count / status_count.sum() * 100).round().astype(int)
    status_label = status_count.astype(str) + ' (' + status_label.astype(str) + '%)'
    
    bar_traces['Total'] = go.Pie(
        hole = 0.5,
        values = status_count,
        labels = status_names,
        visible = 'Total' == params['initial_slider'],
        marker = dict(
            colors = status_colors,
            line = dict(color = params['color'].loc[12, 1], width = 1),
            ),
        hoverlabel = dict(
            font_color = params['color'].loc[100, 1],
            bgcolor = params['color'].loc[0, 2]
            ),
        hovertemplate = '<b>Destinations Nationwide </b><br>%{hovertext}: %{customdata}<extra></extra>',
        hovertext = status_names,
        customdata = status_label,
        text = status_label, texttemplate = '%{text}',
        textfont = dict(color = params['color'].loc[params['bar_borders'].values(), 1])
        )

    trace_dict.update(bar_traces)
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
            active = trace_keys.index(params['initial_slider'],),
            steps = steps,
            currentvalue = {'prefix':'Progress Towards Achieving Travel Goals: '}
            )]

def write_figure(fig, trace_dict, slider_bar):
    """
        TODO
    """
    fig = fig.add_traces([trace_dict[i] for i in trace_dict.keys()])
    fig = fig.update_layout(sliders = slider_bar)
    fig.write_html('io_mid/PROGRESS.html', full_html = True, include_plotlyjs = True)
    fig.write_html('io_mid/PROGRESS.div', full_html = False, include_plotlyjs = False)
    div = '\n'.join(open('io_mid/PROGRESS.div', 'rt').readlines())
    return div

def write_stats(city_list):
    """
        TODO
    """
    bottomline = 'BOTTOMLINE:{count} ({pct}%)'.format(
        count = int(city_list['Photographed'].sum()),
        pct = int(city_list['Photographed'].mean().round(2)*100)
        )
    open(os.path.join('io_mid', 'stats.txt'), 'wt').writelines(bottomline)


##########==========##########==========##########==========##########==========##########==========
## TOP-LEVEL FUNCTIONS

def draw_progress_panel():
    """
        TODO
    """

    ## import and refine data
    city_list = import_data()
    progress = refine_data(city_list)
    write_stats(city_list = city_list)

    ## generate map traces
    fig = make_figure(city_list)
    trace_dict = dict()
    trace_dict = draw_region_bars(city_list= city_list, progress= progress, trace_dict= trace_dict)
    trace_dict = draw_bars(progress, trace_dict = trace_dict)
    slider_bar = draw_slider(trace_dict)

    ## draw figure
    div = write_figure(fig, trace_dict, slider_bar)

    return div


##########==========##########==========##########==========##########==========##########==========
## CODE TESTS

if __name__ == '__main__':
    draw_progress_panel()

##########==========##########==========##########==========##########==========##########==========