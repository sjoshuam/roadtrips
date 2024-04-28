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
    'margin': 2**0,#5,
    'initial_slider': 'By Region',
    'dimensions': (750 - 10, 392 - 10),
    'shading': { ## TODO: replace this!!!
        'border': {'Photographed':'L', 'Visited':'LM', 'Unvisited':'M', 'EMPTY': 'S'},
        'fill':   {'Photographed':'LM', 'Visited':'M', 'Unvisited':'S', 'EMPTY': 'S'}
    },
    'status_order': {'Photographed':2,'Visited':1,'Unvisited':0}
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

def make_waffle(var, dim, city_list, colors, params=params):
    """
        TODO
    """

    ## create coordinates for each box
    waffle_data = pd.DataFrame({'x':range(1, dim[0]+1)})
    waffle_data = waffle_data.merge(pd.Series(range(1, dim[1]+1), name = 'y'), how = 'cross')
    waffle_data['x'] = (waffle_data['x'] / (dim[0] + 1)).round(3)
    waffle_data['y'] = (waffle_data['y'] / (dim[1] + 1)).round(3)
    waffle_data['x'] = waffle_data['x'] * 0.8
    waffle_data = waffle_data.sort_values(['x', 'y'])

    ## create empty slots for needed data
    waffle_data['label'] = 'EMPTY'
    waffle_data['status'] = 'EMPTY'
    waffle_data['var'] = 'grey'
    waffle_data['unused'] = True

    ## enhance city list
    city_list['count_status'] = city_list['status'].replace(params['status_order'])
    city_list = city_list.merge(
            city_list[var].value_counts(), how = 'left', left_on = var, right_index = True)
    city_list=city_list.sort_values(['count_status', 'count', 'city'], ascending=[False,False,True])

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
    waffle_data['border'] = waffle_data['status'].replace(params['shading']['border'])
    waffle_data['fill'] = waffle_data['status'].replace(params['shading']['fill'])
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
    return waffle_data


def make_label(waffle_data, params=params):
    """
        TODO
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
    label_data= waffle_data.copy().drop(columns=['x','label'])
    label_data['status_order']= label_data['status'].replace(params['status_order'])
    label_data= label_data.sort_values(['status_order','y'], ascending=False)
    label_data= label_data.loc[label_data['status'] != '', label_data.columns != 'y']

    ## find unique status and var
    idx_status = label_data.loc[label_data['var'] == label_data.loc[0,'var']].copy()
    idx_status = idx_status.loc[~idx_status['status'].duplicated()].index.values
    idx_var = label_data.loc[~label_data['var'].duplicated()].index.values
    label_data['type'] = 0
    label_data.loc[idx_status, 'type'] += 1
    label_data.loc[idx_var, 'type']    += 3
    label_data = label_data.loc[label_data['type'] > 0]
    label_data['type'] = label_data['type'].replace({4:2})

    ## assign y coordinates
    label_data['xy'] = 0.
    label_data.loc[label_data['type'] < 3,'y'] = y_values[0:sum(label_data['type'] < 3)]
    label_data.loc[label_data['type'] > 1,'y'] = y_values[0:sum(label_data['type'] > 1)]

    ## assign x coordinates
    label_data = label_data.loc[[label_data.index.tolist()[0]]+label_data.index.tolist()]
    label_data.loc[label_data['type'] == 2,'type'] = [1,3]
    label_data['x'] = label_data['type'].replace({3:0.9, 1:1.3})

    ## assign labels
    label_data['label']= label_data['status']
    label_data.loc[label_data['type']==3,'label']= label_data.loc[label_data['type']==3,'var']

    return label_data.reset_index(drop=True)


def calculate_stats():
    """
        TODO
    """
    print('TODO: COMPLETE STATISTICS FUNCTION; ADD TO LABELS')
    return None

##########==========##########==========##########==========##########==========##########==========
## COMPONENT FUNCTIONS: Draw Figure


def make_figure(params=params):
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
        xaxis = dict(
            range = (0, params['dimensions'][0]/params['dimensions'][1]),
            visible = False
            ),
        yaxis = dict(
            range = (0, 1),
            visible = False
            ),
        dragmode = False

    )
    return fig


def write_figure(fig, trace_dict, slider = None):
    """
        TODO
    """
    fig = fig.add_traces([trace_dict[i] for i in trace_dict.keys()])
    fig = fig.update_layout(sliders = slider)
    fig.write_html('io_mid/PROGRESS.html', full_html = True, include_plotlyjs = True)
    fig.write_html('io_mid/PROGRESS.div', full_html = False, include_plotlyjs = False)
    div = '\n'.join(open('io_mid/PROGRESS.div', 'rt').readlines())
    return div


def draw_waffle(name, waffle, trace_dict, size=20, visible=False):
    """
        TODO
    """

    trace = go.Scatter(
        x= waffle['x'],
        y= waffle['y'],
        mode= 'markers',
        text= waffle['label'] + '<br>' + name.title() + ': ' + waffle['var'],
        customdata= waffle['status'],
        hovertemplate= '%{text}<br>Status: %{customdata}<extra></extra>',
        marker= dict(
            color= waffle['fill'], size=size, symbol = 'square',
            line= dict(width=2, color=waffle['border'])),
        showlegend= False,
        visible = visible
    )
    trace_dict.update({name + '∆waffle':trace})

    return trace_dict


def draw_legend(name, legend, trace_dict, colors, size=20, visible=False):
    """
        TODO
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


def add_slider(trace_dict, colors, order=['Total','Region','Criteria']):
    """
        TODO
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

def draw_figure():
    """
        TODO
    """

    ## import and refine data
    city_list = import_data()
    colors = import_color()
    #write_stats(city_list = city_list)  ## FIX THIS!!
    ##progress = refine_data(city_list)
    
    ## generate waffle data
    status_waffle=   make_waffle(var='one', dim=(11,11), city_list=city_list, colors=colors)
    region_waffle=   make_waffle(var='region', dim=(11,11), city_list=city_list, colors=colors)
    criteria_waffle= make_waffle(var='state_criteria', dim=(11,11), city_list=city_list, colors=colors)
    
    ## generate legend data
    status_legend=   make_label(waffle_data=status_waffle)
    region_legend=   make_label(waffle_data=region_waffle)
    criteria_legend= make_label(waffle_data=criteria_waffle)

    ## draw figure
    trace_dict= dict()
    trace_dict= draw_waffle(name='Total', waffle=status_waffle, trace_dict=trace_dict, visible=True)
    trace_dict= draw_waffle(name='Region', waffle=region_waffle, trace_dict=trace_dict)
    trace_dict= draw_waffle(name= 'Criteria', waffle=criteria_waffle, trace_dict=trace_dict)

    ## draw legend
    trace_dict= draw_legend(name='Total', legend=status_legend, trace_dict=trace_dict, colors=colors, visible=True)
    trace_dict= draw_legend(name='Region', legend=region_legend, trace_dict=trace_dict, colors=colors)
    trace_dict= draw_legend(name='Criteria', legend=criteria_legend, trace_dict=trace_dict, colors=colors)

    ## add slider
    slider= add_slider(trace_dict, colors=colors)
    calculate_stats()

    ## write figure
    fig = make_figure()
    write_figure(fig=fig, trace_dict=trace_dict, slider=slider)


##########==========##########==========##########==========##########==========##########==========
## CODE TESTS

if __name__ == '__main__':
    draw_figure()

##########==========##########==========##########==========##########==========##########==========