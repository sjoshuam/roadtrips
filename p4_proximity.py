##########==========##########==========##########==========##########==========##########==========
## INITIALIZE

## import packages
import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go

## 
from scipy.cluster import hierarchy
from scipy.spatial.distance import pdist
from sklearn.metrics.pairwise import haversine_distances
from math import radians, degrees, pi

## 

params = dict(
    width = 1300 * 0.97, height = 400 * 0.97,
    figure_colors = dict(
        bg= 'hsv(000,00,00)', fg= 'hsv(000,00,80)', mg= 'hsv(000,00,40)'),
    )


##########==========##########==========##########==========##########==========##########==========
## COMPONENT FUNCTIONS


def calculate_haversine_distance(a, b):
    """
        TODO
    """
    a = a.reshape(1, -1) * (pi/180)
    b = b.reshape(1, -1) * (pi/180)
    return haversine_distances(a, b) * 3958.8 # distance in miles


def import_city_list():
    """ TODO """
    return pd.read_excel(os.path.join('io_in', 'city_list.xlsx'), index_col = 0)


def decode_merges(the_linkage):
    """
        TODO
    """
    prox_tree = hierarchy.to_tree(the_linkage, rd = True)
    tree_data = list()
    def safely_get_kids(x):
        try: left, right = x.get_left().get_id(), x.get_right().get_id()
        except: left, right = -1, -1
        return [left, right]
    for iter_node in prox_tree[1]:
        tree_data.append([iter_node.get_id()] + safely_get_kids(iter_node))
    tree_data = pd.DataFrame(tree_data).astype(int)
    tree_data.columns = ['Node', 'Left', 'Right']
    return tree_data


def decode_dend(dend):
    """
        TODO
    """
    dend_data = list()
    for iter_xy in range(0, len(dend['icoord'])):
        dend_now = pd.DataFrame({
            'bracket': iter_xy,
            'icoord': dend['icoord'][iter_xy],
            'dcoord': dend['dcoord'][iter_xy],
            'label': ''
            })
        dend_data.append(dend_now)
    dend_data = pd.concat(dend_data)
    dend_data.loc[dend_data['dcoord'] == 0, 'label'] = dend['ivl']
    dend_data.loc[dend_data['dcoord'] == 0, 'leaves'] = dend['leaves']
    dend_data = dend_data.fillna({'leaves': -1}).astype({'leaves': int}).reset_index(drop = True)
    return dend_data

def calculate_proximity_hierarchy(city_list):
    """
        TODO
    """

    ## generate basic dendrogram material
    prox_link = hierarchy.linkage(
        y = city_list[['lon', 'lat']],
        method = 'complete', optimal_ordering = True,
        metric = calculate_haversine_distance
        )
    prox_dendrogram = hierarchy.dendrogram(
        prox_link, no_plot = True, labels = city_list['city'].values
        )
    
    ## extract data from dendrogram objects
    prox_merges = decode_merges(the_linkage = prox_link)
    prox_dend = decode_dend(dend = prox_dendrogram)
    return prox_merges, prox_dend


def make_figure():
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
        yaxis = dict(visible = True, range = [-380, 1000]),
        margin = dict(l = 0, r = 0, t = 0, b = 0),
        font = dict(size = 11),
        )
    return fig


def draw_dendrogram(trace_dict, prox_dend):
    """
        TODO
    """
    dend_dict = dict()

    for i in set(prox_dend['bracket']):
        idx = prox_dend['bracket'] == i
        trace_dict['bracket ' + str(i)] = go.Scatter(
            x = prox_dend.loc[idx, 'icoord'],
            y = prox_dend.loc[idx, 'dcoord'],
            hoverinfo = 'none',
            showlegend = False,
            mode = 'lines',
            line = dict(color = params['figure_colors']['fg'])
            )

    trace_dict.update(dend_dict)
    return trace_dict


def annotate_dendeogram(annote_dict, prox_dend):
    """
        TODO
    """
    dend_annotation = dict()
    max_pad = max([len(i) for i in prox_dend['label']])
    for iter_idx in prox_dend.index:
        if prox_dend.loc[iter_idx, 'label'] != '':
            dend_annotation[prox_dend.loc[iter_idx, 'label']] = go.layout.Annotation(
                x = prox_dend.loc[iter_idx, 'icoord'],
                y = prox_dend.loc[iter_idx, 'dcoord'],
                text = prox_dend.loc[iter_idx, 'label'].ljust(max_pad),
                font = dict(size = 10, color = params['figure_colors']['fg']),
                showarrow = False,
                textangle = 90,
                yshift = -50,
                )
    return dend_annotation


def write_figure(fig, trace_dict, annote_dict):
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
    city_list = import_city_list().reset_index()
    prox_hierarchy = calculate_proximity_hierarchy(city_list)
    fig = make_figure()
    trace_dict, annote_dict = dict(), dict()
    trace_dict = draw_dendrogram(trace_dict = trace_dict, prox_dend = prox_hierarchy[1])
    annote_dict = annotate_dendeogram(annote_dict = trace_dict, prox_dend = prox_hierarchy[1])
    write_figure(fig, trace_dict = trace_dict, annote_dict = annote_dict)




##########==========##########==========##########==========##########==========##########==========
## CODE TESTS
    
if __name__ == '__main__':
    draw_proximity_panel()

##########==========##########==========##########==========##########==========##########==========