##########==========##########==========##########==========##########==========##########==========
## INITIALIZE

## import packages
import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.cluster import hierarchy
from pyproj import Proj

## set parameters
params = dict(
    width = 1000 - 10, height = 400 - 10,
    figure_colors = dict(
        bg= 'hsv(000,00,00)', fg= 'hsv(000,00,80)', mg= 'hsv(000,00,40)'),
    )

##########==========##########==========##########==========##########==========##########==========
## COMPONENT FUNCTIONS - data shaping


def import_city_list():
    """ TODO """
    city_list = pd.read_excel(os.path.join('io_in', 'city_list.xlsx'), index_col = 0)
    idx = city_list['photo_date'].isna() | (city_list['city'] == 'Washington DC')
    city_list = city_list.loc[idx]
    return city_list

def project_coordinates(city_list):
    """
        TODO
    """
    project_lcc = Proj(proj = 'lcc +lon_0=-99.58 +lat_1=24.54 +lat_2=49.38', ellsp = 'WGS84')
    city_list['x'] = 0.0
    city_list['y'] = 0.0
    for iter_row in city_list.index:
        city_list.loc[iter_row, ['x','y']] = project_lcc(
            max(city_list.loc[iter_row, 'lon'], -130),
            max(city_list.loc[iter_row, 'lat'], 20)
            )
    city_list['x'] = (city_list['x'] / 1609.34).round().astype(int)
    city_list['y'] = (city_list['y'] / 1609.34).round().astype(int)
    return city_list


def make_merge_data(city_list, params = params):
    """
        TODO
    """

    ## generate scipy hierarchy objects
    linkage = hierarchy.linkage(y = city_list[['x', 'y']], method = 'ward', optimal_ordering = True)
    dendrogram = hierarchy.dendrogram(
        linkage, no_plot = True, labels = city_list['city'].values, get_leaves = True)
    
    ## extract merges
    def get_nodes(x):
        try: left, right = x.get_left().get_id(), x.get_right().get_id()
        except: left, right = -1, -1
        dist = x.dist
        return {'node': x.get_id(), 'left': left, 'right': right, 'dist': x.dist, 'count': x.count}

    merges = hierarchy.to_tree(linkage, rd = True)[1]
    merges = [get_nodes(merges[iter_node]) for iter_node in range(0, len(merges))]
    merges = pd.DataFrame(merges)
    merges['type'] = 'leaf'
    merges.loc[merges['left'] != -1, 'type'] = 'branch'
    merges = merges.merge(
        right = city_list[['city']].rename(columns = {'city': 'left_name'}),
        how = 'left', left_on = 'left', right_index = True
    )
    merges = merges.merge(
        right = city_list[['city']].rename(columns = {'city': 'right_name'}),
        how = 'left', left_on = 'right', right_index = True
    )

    ## extract coordinates
    extract_xy = lambda x: pd.DataFrame(dendrogram[x], columns = [x + str(i) for i in range(0, 4)])
    leaves = dendrogram['ivl']
    dendrogram = pd.concat([extract_xy('icoord'),extract_xy('dcoord')], axis = 1)
    dendrogram['order'] = list(range(0, dendrogram.shape[0]))
    dendrogram['order'] = dendrogram['order'] + len(leaves)
    dendrogram = dendrogram.sort_values('icoord0')
    dendrogram['leaf0'] = ''
    dendrogram['leaf3'] = ''
    leaves_pop = leaves.copy()
    for iter_row in dendrogram.index:
        if dendrogram.loc[iter_row, 'dcoord0'] == 0:
            dendrogram.loc[iter_row, 'leaf0'] = leaves_pop.pop(0)
        if dendrogram.loc[iter_row, 'dcoord3'] == 0:
            dendrogram.loc[iter_row, 'leaf3'] = leaves_pop.pop(0)
    dendrogram = dendrogram.sort_values(by = 'order')

    ## generate leaf colors
    dendrogram['color'] = (dendrogram['icoord1'] + dendrogram['icoord2']) / 2
    dendrogram['color'] = (360 * dendrogram['color'] / dendrogram['icoord2'].max()).round().astype(int)
    dendrogram['color'] = 'hsv(' + dendrogram['color'].astype(str) + ',50,70)'
    too_high = dendrogram['dcoord1'] > 1400
    dendrogram.loc[too_high, 'color'] = 'hsv(0,0,70)'

    return dendrogram


##########==========##########==========##########==========##########==========##########==========
## COMPONENT FUNCTIONS - figure rendition


def make_figure(params = params):
    """
        TODO
    """
    fig = go.Figure()
    fig = fig.update_layout(
        template = 'plotly_dark',
        showlegend = False,
        width = params['width'], height = params['height'],
        plot_bgcolor = params['figure_colors']['bg'],
        paper_bgcolor = params['figure_colors']['bg'],
        xaxis = dict(visible = False),
        yaxis = dict(
            visible = True, 
            range = [-440, 1200],
            tickmode = 'array', 
            ticktext = [str(i) + 'mi' for i in range(0, 1200, 200)],
            tickvals = list(range(0, 1200, 200))
            ),
        margin = dict(l = 0, r = 0, t = 0, b = 0),
        font = dict(size = 11),
        )
    return fig


def draw_dendrogram(trace_dict, merge_data, params = params):
    """
        TODO
    """
    dend_dict = dict()
    icol = ['icoord' + str(i) for i in range(0, 4)]
    dcol = ['dcoord' + str(i) for i in range(0, 4)]
    for iter_row in merge_data.index:
        dend_dict['bracket ' + str(iter_row)] = go.Scatter(
            x = merge_data.loc[iter_row, icol], y = merge_data.loc[iter_row, dcol],
            hoverinfo = 'none', showlegend = False, mode = 'lines',
            line = dict(color =  merge_data.loc[iter_row, 'color'])
            )
    trace_dict.update(dend_dict)
    return trace_dict


def annotate_dendeogram(annote_dict, merge_data, params = params):
    """
        TODO
    """
    dend_annotation = dict()

    for iter_row in merge_data.index:

        leaf0 = merge_data.loc[iter_row, 'leaf0']
        leaf3 = merge_data.loc[iter_row, 'leaf3']


        if leaf0 != '':
            dend_annotation[leaf0] = go.layout.Annotation(
                x = merge_data.loc[iter_row, 'icoord0'],
                y = merge_data.loc[iter_row, 'dcoord0'],
                text = merge_data.loc[iter_row, 'leaf0'].ljust(20),
                font = dict(size = 10, color = merge_data.loc[iter_row, 'color']),
                showarrow = False, textangle = 90, yshift = -55,
                )
        
        if leaf3 != '':
            dend_annotation[leaf3] = go.layout.Annotation(
                x = merge_data.loc[iter_row, 'icoord3'],
                y = merge_data.loc[iter_row, 'dcoord3'],
                text = merge_data.loc[iter_row, 'leaf3'].ljust(20),
                font = dict(size = 10, color = merge_data.loc[iter_row, 'color']),
                showarrow = False, textangle = 90, yshift = -55,
                )

    annote_dict.update(dend_annotation)
    return annote_dict


def write_figure(fig, annote_dict, trace_dict, params = params):
    """
        TODO
    """
    fig = fig.add_traces([i for i in trace_dict.values()])
    fig = fig.update_layout(annotations = [i for i in annote_dict.values()])
    fig.write_html(
        os.path.join('io_mid', 'PROXIMITY.html'), full_html = True, include_plotlyjs = True)
    fig.write_html(
        os.path.join('io_mid', 'PROXIMITY.div'), full_html = False, include_plotlyjs = False)
    div = '\n'.join(open('io_mid/PROXIMITY.div', 'rt').readlines())
    return div


##########==========##########==========##########==========##########==========##########==========
## TOP-LEVEL FUNCTIONS
    
def draw_proximity_panel():
    """
        TODO
    """

    ## prepare data
    city_list = import_city_list().reset_index()
    city_list = project_coordinates(city_list)
    merge_data = make_merge_data(city_list)

    ## generate traces
    fig = make_figure()
    trace_dict, annote_dict = dict(), dict()
    trace_dict = draw_dendrogram(trace_dict = trace_dict, merge_data = merge_data)
    annote_dict = annotate_dendeogram(annote_dict = annote_dict, merge_data = merge_data)

    ## make figure
    div = write_figure(fig, trace_dict = trace_dict, annote_dict = annote_dict)
    return div


##########==========##########==========##########==========##########==========##########==========
## CODE TESTS
    
if __name__ == '__main__':
    draw_proximity_panel()



##########==========##########==========##########==========##########==========##########==========