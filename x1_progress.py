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

"""
##########==========##########==========##########==========##########==========##########==========
## INITIALIZE

## import packages
import os
import pandas as pd
import plotly.graph_objects as go

## set parameters
params = {
    'margin': 2**5,
    'initial_slider': 'By Region',
    'dimensions': (750 - 10, 392 - 10)
}

##########==========##########==========##########==========##########==========##########==========
## COMPONENT FUNCTIONS: Manipulate City Visit Data


def import_data():
    """
        TODO
    """

    ## import and merge data
    city_list = pd.read_excel('io_in/city_list.xlsx', sheet_name = "Cities")

    ## derive unvisited/ visited/ photographed counts
    city_list['status'] = 'Unvisited'
    city_list.loc[city_list['visit'].astype(bool), 'status'] = 'Visited'
    city_list.loc[~city_list['photo_date'].isna(), 'status'] = 'Photographed'
    city_list['one'] = 'Total'

    return city_list


def import_color():
    """
        TODO
    """
    colors = pd.read_excel('io_in/city_list.xlsx', sheet_name = "Color", index_col = 0)
    color_map = pd.read_excel('io_in/city_list.xlsx', sheet_name = "ColorMap").dropna()
    for iter_row in color_map.index:
        colors[color_map.loc[iter_row, 'key']] = colors[color_map.loc[iter_row, 'hue']]
    return colors

print('FIX THIS!!!')
'''
def write_stats(city_list):
    """
        TODO
    """
    bottomline = 'BOTTOMLINE:{count} ({pct}%)'.format(
        count = int(city_list['Photographed'].sum()),
        pct = int(city_list['Photographed'].mean().round(2)*100)
        )
    open(os.path.join('io_mid', 'stats.txt'), 'wt').writelines(bottomline)
'''

##########==========##########==========##########==========##########==========##########==========
## COMPONENT FUNCTIONS: Render waffle chart visualizations

def make_waffle(var, dim, city_list, colors):
    """
        TODO
    """

    ## create coordinates for each box
    waffle_data = pd.DataFrame({'x':range(0, dim[0])})
    waffle_data = waffle_data.merge(pd.Series(range(0, dim[1]), name = 'y'), how = 'cross')
    waffle_data['x'] = (waffle_data['x'] / dim[0]).round(3)
    waffle_data['y'] = (waffle_data['y'] / dim[1]).round(3)
    waffle_data = waffle_data.sort_values(['x', 'y'])

    ## create empty slots for needed data
    waffle_data['label'] = 'EMPTY'
    waffle_data['status'] = 'EMPTY'
    waffle_data['var'] = 'grey'
    waffle_data['unused'] = True

    ## enhance city list
    city_list['count_status']=city_list['status'].replace({'Photographed':2,'Visited':1,'Unvisited':0})
    city_list = city_list.merge(
            city_list[var].value_counts(), how = 'left', left_on = var, right_index = True)
    city_list=city_list.sort_values(['count', 'count_status', 'city'], ascending=[False,False,True])

    ## label cells, looping through each city
    var_then = city_list.at[city_list.index[0], var]
    by_x = False
    for iter_row in city_list.index:
        var_now = city_list.at[iter_row, var]

        ## determine fill direction
        if var_now != var_then:
            if by_x: waffle_data = waffle_data.sort_values(['x', 'y'])
            else: waffle_data = waffle_data.sort_values(['y', 'x'])
            by_x = not by_x

        ## fill first available cell
        first_unused = waffle_data.index[waffle_data['unused']][0]
        waffle_data.at[first_unused, 'label'] = city_list.at[iter_row, 'city']
        waffle_data.at[first_unused, 'status'] = city_list.at[iter_row, 'status']
        waffle_data.at[first_unused, 'var'] = city_list.at[iter_row, var]
        waffle_data.at[first_unused, 'unused'] = False
        var_then = var_now

    ## assign colors
    waffle_data['border'] = waffle_data['status'].replace(
        {'Photographed':'L', 'Visited':'LM', 'Unvisited':'M', 'EMPTY': 'MS'})
    waffle_data['fill'] = waffle_data['status'].replace(
        {'Photographed':'LM', 'Visited':'M', 'Unvisited':'MS', 'EMPTY': 'S'})
    for iter_row in waffle_data.index:
        waffle_data.at[iter_row, 'border'] = colors.at[
            waffle_data.at[iter_row, 'border'], waffle_data.at[iter_row, 'var']]
        waffle_data.at[iter_row, 'fill'] = colors.at[
            waffle_data.at[iter_row, 'fill'], waffle_data.at[iter_row, 'var']]
    for iter_var in ['label', 'status', 'var']:
        waffle_data[iter_var] = waffle_data[iter_var].replace({'grey':'', 'EMPTY':''})

    ## clean up and return results
    del waffle_data['unused']
    waffle_data = waffle_data.sort_values(['x', 'y'])
    print(waffle_data)
    return waffle_data


##########==========##########==========##########==========##########==========##########==========
## COMPONENT FUNCTIONS: Draw Figure

def draw_waffle(waffle):
    """
        TODO
    """
    trace = go.Scatter(
        x = waffle['x'],
        y = waffle['y'],
        mode = 'markers',
        hovertext = waffle['label'],
        marker = dict(
            color = waffle['fill'], size = 24, symbol = 'square',
            line = dict(width = 3, color= waffle['border'])
            ),
        #hoverlabel = waffle['label']

    )
    return trace

def make_figure(params = params):
    """
        TODO
    """
    fig = go.Figure()
    fig = fig.update_layout(
        width = params['dimensions'][0],
        height = params['dimensions'][1],
        plot_bgcolor = 'hsva(0,0,0,0)',
        paper_bgcolor = 'hsva(0,0,0,0)',
        font = dict(color = 'hsva(0,0,100,0)'),
        margin = dict(
            r = params['margin'],
            l = params['margin'] * 2**1,
            t = params['margin'],
            b = params['margin']
            ),
        #legend_title_text = 'KEY: Destinations',
        dragmode = False,
        #legend = dict(x = 0)

    )
    return fig

'''

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

'''

##########==========##########==========##########==========##########==========##########==========
## TOP-LEVEL FUNCTIONS

def draw_progress_panel():
    """
        TODO
    """

    ## import and refine data
    city_list = import_data()
    colors = import_color()
    #write_stats(city_list = city_list)  ## FIX THIS!!
    ##progress = refine_data(city_list)
    
    ## generate waffle data
    region_waffle = make_waffle(var= 'region', dim= (15, 8), city_list= city_list, colors= colors)
    status_waffle = make_waffle(var= 'one', dim= (15, 8), city_list= city_list, colors= colors)
    criteria_waffle = make_waffle(
        var= 'state_criteria', dim= (15, 8), city_list= city_list, colors= colors)
    
    fig = make_figure()
    fig = fig.add_trace(draw_waffle(criteria_waffle))
    fig.write_html('io_mid/waffle_TEST.html', full_html = True, include_plotlyjs = True)



    '''
    ## generate map traces
    fig = make_figure(city_list)
    trace_dict = dict()
    trace_dict = draw_region_bars(city_list= city_list, progress= progress, trace_dict= trace_dict)
    trace_dict = draw_bars(progress, trace_dict = trace_dict)
    slider_bar = draw_slider(trace_dict)

    ## draw figure
    div = write_figure(fig, trace_dict, slider_bar)

    return div
    '''


##########==========##########==========##########==========##########==========##########==========
## CODE TESTS

if __name__ == '__main__':
    draw_progress_panel()

##########==========##########==========##########==========##########==========##########==========