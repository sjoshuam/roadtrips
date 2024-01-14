"""
    Purpose: Place destinations into hierarchical groups that are close together and depict
        those relationships visually.  This provides a planning tool for future roadtrips. In
        general, the closer destinations are, the more suitable they are for being visited in
        the same trip.  Packge visualization so it can slot into a div section within
        the project's main html page.
    Inputs:
        io_in/city_list.xlsx: provides information on the destinations I seek to visit and my
            progress visiting them.
    Outputs:
        io_mid/PROXIMITY.html: self-contained, fully-functional html file with all data displays.
            Used during development to inspect data displays.  Is not tied into the project
            css file, so some stylistic elements will be of lower quality.
        io_mid/PROXIMITY.div: html code contained inside a <div> tag, suitable for injection into
            the project's main html product.
    Open GitHub Issues:
        #14 Add doc strings to all functions
        #16 Wire module into a run-everything execute_project() function in 0_execute_project.py
        #19 Tie colors into centralized color scheme where possible (proximity uses a unique
            rainbow pallete, but can still be synced more).
"""
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
    width = 1300 - 10, height = 720 - 10,
    figure_colors = dict(
        bg= 'hsv(000,00,00)', fg= 'hsv(000,00,80)', mg= 'hsv(000,00,40)'),
    too_high = 2400,
    label_height = 250,
    )

##########==========##########==========##########==========##########==========##########==========
## COMPONENT FUNCTIONS - generate hierarchical clustering data


def import_city_list() -> pd.DataFrame:
    """ TODO """
    city_list = pd.read_excel(os.path.join('io_in', 'city_list.xlsx'), index_col = 0)
    idx = city_list['photo_date'].isna() | (city_list['city'] == 'Washington DC')
    city_list = city_list.loc[idx]
    return city_list


def project_coordinates(city_list: pd.DataFrame) -> pd.DataFrame:
    """
        TODO
    """
    project_lcc = Proj(proj = 'lcc +lon_0=-99.58 +lat_1=24.54 +lat_2=49.38', ellsp = 'WGS84')
    city_list['x'] = 0.0
    city_list['y'] = 0.0
    for iter_row in city_list.index:
        city_list.loc[iter_row, ['x','y']] = project_lcc(
            max(city_list.loc[iter_row, 'lon'], -179),
            max(city_list.loc[iter_row, 'lat'], 0),
            )
    city_list['x'] = (city_list['x'] / 1609.34).round().astype(int)
    city_list['y'] = (city_list['y'] / 1609.34).round().astype(int)
    return city_list


def make_hierarchy_linkage(city_list: pd.DataFrame) -> pd.DataFrame:
    """
        TODO
    """
    city_names = {i:city_list['city'].iat[i] for i in range(0, city_list.shape[0])}
    linkage = hierarchy.linkage(y = city_list[['x', 'y']], method = 'ward', optimal_ordering = True)
    linkage = pd.DataFrame(linkage, columns = ['left', 'right', 'distance', 'leaves'])
    linkage['up'] = linkage.index + city_list.shape[0]
    linkage = linkage.astype({'left': int, 'right': int, 'leaves': int})
    linkage['left_name'] = linkage['left'].copy().replace(city_names)
    linkage['right_name'] = linkage['right'].copy().replace(city_names)
    return linkage


def name_composite_nodes(city_list: pd.DataFrame, linkage: pd.DataFrame) -> pd.DataFrame:
    """
        TODO
    """
    ## compile all cities for each merge
    linkage['up_name'] = ''
    for iter_row in linkage.index:
        linkage.loc[iter_row, 'up_name'] = (
            linkage.loc[iter_row, 'left_name'] + ',' + linkage.loc[iter_row, 'right_name'])
        linkage['left_name'] = linkage['left_name'].replace({
            linkage.loc[iter_row, 'up']: linkage.loc[iter_row, 'up_name']})
        linkage['right_name'] = linkage['right_name'].replace({
            linkage.loc[iter_row, 'up']: linkage.loc[iter_row, 'up_name']})
        
    ## simplify composite names to most central city plus count
    for iter_row in linkage.index:
        city_now = linkage.loc[iter_row, 'up_name'].split(',')
        xy_now = city_list.loc[city_list['city'].isin(city_now), ['city', 'x', 'y']]
        xy_now[['x', 'y']] = xy_now[['x', 'y']] - xy_now[['x', 'y']].median()
        xy_now['centrality'] = (xy_now[['x', 'y']] ** 2).sum(axis = 1)
        label_now = xy_now.loc[xy_now['centrality'] == xy_now['centrality'].min(), 'city'].values[0]
        label_now = label_now + ' +' + str(xy_now.shape[0] - 1)
        linkage.loc[iter_row, 'up_name'] = label_now
    
    return linkage


def make_hierarchy_dendrogram(city_list: pd.DataFrame, linkage: pd.DataFrame, params = params):
    """
        TODO
    """

    ## extract bracket coordiantes
    dendrogram = hierarchy.dendrogram(linkage[['left', 'right', 'distance', 'leaves']].values,
        no_plot = True, labels = city_list['city'].values, get_leaves = True)
    extract_xy = lambda x: pd.DataFrame(dendrogram[x], columns = [x + str(i) for i in range(0, 4)])
    dendrogram = pd.concat([extract_xy('icoord'), extract_xy('dcoord')], axis = 1)

    ## attach city information to brackets and filter out the highest brackets
    dendrogram = dendrogram.merge(right = linkage[['distance', 'left_name', 'right_name', 'up_name']],
        left_on = 'dcoord1', right_on = 'distance', how = 'left').drop(columns = 'distance')
    
    ## normalize icoord and formulate colors
    icoords = ['icoord' + str(i) for i in range(0, 4)]
    dendrogram[icoords] =  dendrogram[icoords] / dendrogram[icoords].max().max()
    dendrogram['color'] = (dendrogram['icoord1'] + dendrogram['icoord2']) / 2
    dendrogram['color'] = ((dendrogram['color'] / dendrogram['icoord2'].max()) * 330).astype(int)
    dendrogram['color'] = 'hsv(' + dendrogram['color'].astype(str) + ',50,80)'
    dendrogram.loc[dendrogram['dcoord1'] >= params['too_high'], 'color'] = 'hsv(000,00,50)'

    return dendrogram


def extract_leaf_nodes(hierarchy_dendrogram: pd.DataFrame) -> pd.DataFrame:
    """
        TODO
    """

    ## extract terminal node coordinates
    def get_node_coords(num, hd = hierarchy_dendrogram):
        """X"""
        i = [['left_name', '', '', 'right_name'][num]]
        i = i + ['icoord' + str(num), 'dcoord' + str(num)]
        hd = hd.copy()[i]
        hd.columns = ['name', 'icoord', 'dcoord']
        return hd
    dendrogram_nodes = pd.concat([get_node_coords(num = 0), get_node_coords(num = 3)])
    dendrogram_nodes = dendrogram_nodes.loc[dendrogram_nodes['dcoord'] == 0]

    ## formulate colors
    dendrogram_nodes['hue'] = (dendrogram_nodes['icoord'] * 330).astype(int)
    dendrogram_nodes['color_line'] = 'hsv(' + dendrogram_nodes['hue'].astype(str) + ',50,80)'
    dendrogram_nodes['color_fill'] = 'hsv(' + dendrogram_nodes['hue'].astype(str) + ',50,20)'
    return dendrogram_nodes.reset_index(drop = True)

def extract_merge_nodes(hierarchy_dendrogram, params = params):
    """
        TODO
    """

    ## extract merge node coordinates
    merge_nodes = hierarchy_dendrogram[['up_name']].copy().rename(columns = {'up_name':'name'})
    merge_nodes['icoord']= (hierarchy_dendrogram['icoord1'] + hierarchy_dendrogram['icoord2']) * 0.5
    merge_nodes['dcoord'] = hierarchy_dendrogram['dcoord1'].copy()

    ## formulate colors
    merge_nodes['hue'] = (merge_nodes['icoord'] * 330).astype(int)
    merge_nodes['color_line'] = 'hsv(' + merge_nodes['hue'].astype(str) + ',50,80)'
    merge_nodes['color_fill'] = 'hsv(' + merge_nodes['hue'].astype(str) + ',50,20)'
    merge_nodes['label_type'] = 'hover'
    merge_nodes.loc[merge_nodes['dcoord'] >= params['label_height'], 'label_type'] = 'text'
    merge_nodes = merge_nodes.loc[merge_nodes['dcoord'] < params['too_high']]
    return merge_nodes.reset_index(drop = True)


##########==========##########==========##########==========##########==========##########==========
## COMPONENT FUNCTIONS - render figure

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
        yaxis = dict(visible = False, autorange = 'reversed'),
        xaxis = dict(
            visible = True, 
            range = [-400, 2400],
            tickmode = 'array', 
            ticktext = [str(i) + 'mi' for i in range(0, 2400, 400)],
            tickvals = list(range(0, 2400, 400)),
            ),
        hoverlabel = dict(align = 'left'),
        margin = dict(l = 0, r = 0, t = 0, b = 0),
        font = dict(size = 11),
        )
    return fig, dict()


def draw_dendrogram(trace_dict, hierarchy_dendrogram):
    """
        TODO
    """
    icoords = ['icoord' + str(i) for i in range(0, 4)]
    dcoords = ['dcoord' + str(i) for i in range(0, 4)]
    new_traces = dict()
    for iter_row in hierarchy_dendrogram.index:
        name_now = hierarchy_dendrogram.loc[iter_row, 'up_name']
        new_traces[name_now + 'bracket'] = go.Scatter(
            x = hierarchy_dendrogram.loc[iter_row, dcoords],
            y = hierarchy_dendrogram.loc[iter_row, icoords],
            hoverinfo = 'none', showlegend = False, mode = 'lines',
            line = dict(color = hierarchy_dendrogram.loc[iter_row, 'color']),
            name = name_now
        )
    trace_dict.update(new_traces)
    return trace_dict


def label_nodes(trace_dict, leaf_nodes, merge_nodes):
    """
        TODO
    """
    new_traces = dict()

    ## draw leaf nodes
    new_traces['leaf_nodes'] = go.Scatter(
        x = leaf_nodes['dcoord'],
        y = leaf_nodes['icoord'],
        text = leaf_nodes['name'],
        name = 'leaf_nodes',
        hoverinfo = 'none', showlegend = False, mode = 'markers+text',
        textfont = dict(color = leaf_nodes['color_line']),
        marker = dict(
            line = dict(color = leaf_nodes['color_line'], width = 1.5),
            color = leaf_nodes['color_fill'],
            size = 8
            ),
        textposition = 'middle left'
        )
    
    ## upper merges
    idx = merge_nodes['label_type'] == 'text'
    new_traces['upper_merge_nodes'] = go.Scatter(
        x = merge_nodes.loc[idx, 'dcoord'],
        y = merge_nodes.loc[idx, 'icoord'],
        text = merge_nodes.loc[idx, 'name'],
        name = 'upper_merge_nodes',
        hoverinfo = 'text', showlegend = False, mode = 'markers+text',
        textfont = dict(color = merge_nodes.loc[idx, 'color_line']),
        hoverlabel = dict(
            align = 'left',
            font_color = merge_nodes.loc[idx, 'color_line'],
            bgcolor = merge_nodes.loc[idx, 'color_fill'],
            bordercolor = merge_nodes.loc[idx, 'color_line'],
            ),
        marker = dict(
            line = dict(color = merge_nodes.loc[idx, 'color_line'], width = 1.5),
            color = merge_nodes.loc[idx, 'color_fill'],
            size = 8
            ),
        textposition = 'middle left'
        )

    ## lower merges
    idx = merge_nodes['label_type'] == 'hover'
    new_traces['lower_merge_nodes'] = go.Scatter(
        x = merge_nodes.loc[idx, 'dcoord'],
        y = merge_nodes.loc[idx, 'icoord'],
        text = merge_nodes.loc[idx, 'name'],
        name = 'lower_merge_nodes',
        hoverinfo = 'text', showlegend = False, mode = 'markers',
        textfont = dict(color = merge_nodes.loc[idx, 'color_line']),
        hoverlabel = dict(
            align = 'left',
            font_color = merge_nodes.loc[idx, 'color_line'],
            bgcolor = merge_nodes.loc[idx, 'color_fill'],
            bordercolor = merge_nodes.loc[idx, 'color_line'],
            ),
        marker = dict(
            line = dict(color = merge_nodes.loc[idx, 'color_line'], width = 1.5),
            color = merge_nodes.loc[idx, 'color_fill'],
            size = 8
            ),
        textposition = 'middle left'
        )

    trace_dict.update(new_traces)
    return trace_dict


def write_figure(fig, trace_dict):
    """
        TODO
    """
    fig = fig.add_traces([i for i in trace_dict.values()])
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

    ## prepare data for hierarchical clustering
    city_list = import_city_list().reset_index()
    city_list = project_coordinates(city_list = city_list)

    ## generate cluster hierarchy and dendrogram components
    hierarchy_linkage = make_hierarchy_linkage(city_list = city_list)
    hierarchy_linkage = name_composite_nodes(city_list = city_list, linkage = hierarchy_linkage)
    hierarchy_dendrogram = make_hierarchy_dendrogram(
        city_list = city_list, linkage = hierarchy_linkage)
    leaf_nodes = extract_leaf_nodes(hierarchy_dendrogram = hierarchy_dendrogram)
    merge_nodes = extract_merge_nodes(hierarchy_dendrogram = hierarchy_dendrogram)
    
    ## generate visualization
    fig, trace_dict = make_figure()
    trace_dict = draw_dendrogram(trace_dict= trace_dict, hierarchy_dendrogram= hierarchy_dendrogram)
    trace_dict=label_nodes(trace_dict= trace_dict, leaf_nodes= leaf_nodes, merge_nodes= merge_nodes)
    write_figure(fig = fig, trace_dict = trace_dict)
    return None


##########==========##########==========##########==========##########==========##########==========
## CODE TESTS
    
if __name__ == '__main__':
    draw_proximity_panel()



##########==========##########==========##########==========##########==========##########==========