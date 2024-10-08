""" Determines which destinations have the least bad weather in each month and displays the 
distances between them in dendrogram format.  These figures are a trip planning tool, enabling
me to see at a glance where there are clusters of unphotographed locations currently experiencing
the country's most decent weather.
Input:
    import_data() reads in destination-wise data on my past travels, as well as the color
    pallette for this project.  Both are tabs in the io_in/city_list.xlsx spreadsheet.
Output: write_figure() writes an html file to io_mid/PROMIXITY.div. the execute_project.py module
    injects this code into an html data dashboard.
Open GitHub Issues:
    #22 refactor to streamline and pay down technical debt. (Low priority)
"""
##########==========##########==========##########==========##########==========##########==========
## INITIALIZE

## import packages
import os, sys, datetime
if not sys.prefix.endswith('.venv'): raise Exception('Virtual Environment Not Detected')  
import pandas as pd
import plotly.graph_objects as go
from scipy.cluster import hierarchy
from pyproj import Proj

## set parameters
params = dict(
    width = 1000 - 10, height = 900 - 10,
    too_high = 2400,
    label_height = 250,
    first_visible = datetime.datetime.now().month + round(datetime.datetime.now().day/30.5),
    shading = {
        'border':{'Photographed':'M' , 'Visited':'LM', 'Unvisited':'LM', 'Bracket':'LM'},
        'fill':  {'Photographed':'MS', 'Visited':'MS', 'Unvisited':'S' , 'Bracket':'MS' }
        },
    )

##########==========##########==========##########==========##########==========##########==========
## COMPONENT FUNCTIONS - import and enrich data

def import_data() -> pd.DataFrame:
    """ Imports a dataset of my travels plus the color palette for the project.  Both come from
    tabs in the io_in/city_list.xlsx file.
    Outputs:
        city_list = destination-wise data on my travels and travel goals
        best_months = a simplified matrix of weather data indicating cities are in top weather
            quartile for each month.
        colors = the color pallette for this project.
    """
    ## import color matrix
    colors = pd.read_excel('io_in/city_list.xlsx', sheet_name = "Color", index_col = 0)
    color_map = pd.read_excel('io_in/city_list.xlsx', sheet_name = "ColorMap").dropna()
    for iter_row in color_map.index:
        colors[color_map.loc[iter_row, 'key']] = colors[color_map.loc[iter_row, 'hue']]

    ## import city data and calculate useful variables
    city_list = pd.read_excel(os.path.join('io_in', 'city_list.xlsx'), index_col = 0)
    city_list['status'] = 'Unvisited'
    city_list.loc[city_list['visit'].astype(bool), 'status'] = 'Visited'
    city_list.loc[~city_list['photo_date'].isna(), 'status'] = 'Photographed'

    ## import weather data and identify best months to visit each city
    weather_data = pd.read_excel(os.path.join('io_mid', 'weather_data.xlsx'), index_col=0)
    best_quantile = weather_data.quantile(0.75, axis=0).values
    best_quantile = pd.DataFrame(
        data={i:best_quantile for i in weather_data.index}, index=weather_data.columns).T
    best_months = (weather_data >= best_quantile) & (weather_data >= 4)

    ## align weather data to city_list
    best_months = best_months.loc[city_list['noaa_station'].values]
    best_months.index = city_list.index
    return city_list, best_months, colors


def assign_colors(city_list:pd.DataFrame, colors:pd.DataFrame, params=params) -> pd.DataFrame:
    """ Allocates colors from the project color palette matrix to city_list.  Function assigns
    each city the project's main color or main gray, depending on whether I have already 
    photographed that destination.
    Inputs:
        city_list = project's main dataset.  Provides destination-wise information about my travels
            and travel goals
        colors = project's color palette matrix.  Projects the standard colors used across the
            project.
        params = The parameters dictionary defined at the top of this script.  Provides easy
            access to parameters that might need adjustment.
    """
    city_list['color_line'] = city_list['status'].replace(params['shading']['border'])
    city_list['color_fill'] = city_list['status'].replace(params['shading']['fill'])
    city_list['highlight'] = 'main'
    city_list.loc[city_list['status']=='Photographed', 'highlight'] = 'grey'
    for iter_row in city_list.index:
        city_list.loc[iter_row, 'color_line'] = colors.loc[
            city_list.loc[iter_row, 'color_line'], city_list.loc[iter_row, 'highlight']]
        city_list.loc[iter_row, 'color_fill'] = colors.loc[
            city_list.loc[iter_row, 'color_fill'], city_list.loc[iter_row, 'highlight']]
    city_list = city_list.drop(columns='highlight')
    return city_list


##########==========##########==========##########==========##########==========##########==========
## COMPONENT FUNCTIONS - generate distance hierarchy


def project_coordinates(city_list: pd.DataFrame) -> pd.DataFrame:
    """ scipy's dendrogram generation code does not filly support geographic coordinates. This
    function converts destination coordinates to something approximating Euclidean coordinates
    so that the scipy code can use Ward's method to determine linkages
    Inputs:
        city_list = project's main dataset.  Provides destination-wise information about my travels
            and travel goals
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
    """ Calculates the hierarchy of merges that clusters my travel destinations into geographically
    proximate groups.
    Inputs:
        city_list = project's main dataset.  Provides destination-wise information about my travels
            and travel goals
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
    """ Recevies a hierarchy of merges that clusters my travel destinations into geographically
    proximate groups from make_hierarchy_linkage(). Generates names for each merge group, based
    on the most central city in each group.
    Inputs:
        city_list = project's main dataset.  Provides destination-wise information about my travels
            and travel goals
        linkage = a merge hierarchy that lumps destinations into sucessfully larger groups based
            on geographic proximity.  Is the output from make_hierarchy_linkage()
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


def make_hierarchy_dendrogram(city_list:pd.DataFrame, linkage:pd.DataFrame, colors:pd.DataFrame,
                              params=params) -> pd.DataFrame:
    """ Uses the merge hierarchy that make_hierarchy_linkage() generated to represent proximity
    among destinations.  Formulates a dendrogram representation of the merge hierarchy. 
    Inputs:
        city_list = project's main dataset.  Provides destination-wise information about my travels
            and travel goals
        linkage = a merge hierarchy that lumps destinations into sucessfully larger groups based
            on geographic proximity.  Is the output from make_hierarchy_linkage()
        colors = project's color palette matrix.  Projects the standard colors used across the
            project.
        params = The parameters dictionary defined at the top of this script.  Provides easy
            access to parameters that might need adjustment.
    """

    ## extract bracket coordiantes
    dendrogram = hierarchy.dendrogram(linkage[['left', 'right', 'distance', 'leaves']].values,
        no_plot = True, labels = city_list['city'].values, get_leaves = True)
    extract_xy = lambda x: pd.DataFrame(dendrogram[x], columns = [x + str(i) for i in range(0, 4)])
    dendrogram = pd.concat([extract_xy('icoord'), extract_xy('dcoord')], axis = 1)

    ## attach city information to brackets and filter out the highest brackets
    dendrogram = dendrogram.merge(right = linkage[['distance', 'left_name', 'right_name', 'up_name']],
        left_on = 'dcoord1', right_on = 'distance', how = 'left').drop(columns = 'distance')
    
    ## normalize icoord
    icoords = ['icoord' + str(i) for i in range(0, 4)]
    dendrogram[icoords] =  dendrogram[icoords] / dendrogram[icoords].max().max()

    ## compile color information
    dendrogram['color'] = colors.loc[params['shading']['border']['Bracket'], 'grey']
    dendrogram = dendrogram.merge(
        right=city_list[['city', 'color_line','status']].rename(
            columns={'color_line':'left_color','status':'left_status'}),
        how='left', left_on='left_name', right_on='city'
        ).drop(columns='city')
    dendrogram = dendrogram.merge(
        right=city_list[['city', 'color_line', 'status']].rename(
            columns={'color_line':'right_color','status':'right_status'}),
        how='left', left_on='right_name', right_on='city'
        ).drop(columns='city')
    
    ## determine line color
    idx = (dendrogram['left_status'] != 'Photographed') & (~dendrogram['left_status'].isna())
    dendrogram.loc[idx, 'color'] = dendrogram.loc[idx, 'left_color']
    idx = (dendrogram['right_status'] != 'Photographed') & (~dendrogram['right_status'].isna())
    dendrogram.loc[idx, 'color'] = dendrogram.loc[idx, 'right_color']

    return dendrogram


def extract_leaf_nodes(hierarchy_dendrogram:pd.DataFrame, city_list:pd.DataFrame) -> pd.DataFrame:
    """ Extracts info. about terminal nodes ("leaves"; the destinations) from dendrogram object"
    Inputs:
        hierarchy_dendrogram = Coordinates needed to draw a dendrogram representation of a 
            the distances between destinations
        city_list = project's main dataset.  Provides destination-wise information about my travels
            and travel goals
    """
    ## extract terminal node coordinates
    def get_node_coords(num, hd = hierarchy_dendrogram):
        """helper function to extract coordinates for each destination in the dendrogram"""
        i = [['left_name', '', '', 'right_name'][num]]
        i = i + ['icoord' + str(num), 'dcoord' + str(num)]
        hd = hd.copy()[i]
        hd.columns = ['name', 'icoord', 'dcoord']
        return hd
    dendrogram_nodes = pd.concat([get_node_coords(num = 0), get_node_coords(num = 3)])
    dendrogram_nodes = dendrogram_nodes.loc[dendrogram_nodes['dcoord'] == 0]

    ## formulate colors
    dendrogram_nodes = dendrogram_nodes.merge(right = city_list[['city','color_line','color_fill']],
        how='left', left_on='name', right_on='city')
    return dendrogram_nodes.reset_index(drop = True)


def extract_merge_nodes(hierarchy_dendrogram:pd.DataFrame, colors:pd.DataFrame, params=params):
    """ Extracts info. about non-terminal nodes "branches" from dendrogram object". These
    nodes are groups of destinations that are geographically proximate.
    Inputs:
        hierarchy_dendrogram = Coordinates needed to draw a dendrogram representation of a 
            the distances between destinations
        colors = project's color palette matrix.  Projects the standard colors used across the
            project.
        params = The parameters dictionary defined at the top of this script.  Provides easy
            access to parameters that might need adjustment.
    """

    ## extract merge node coordinates
    merge_nodes = hierarchy_dendrogram[['up_name']].copy().rename(columns = {'up_name':'name'})
    merge_nodes['icoord']= (hierarchy_dendrogram['icoord1'] + hierarchy_dendrogram['icoord2']) * 0.5
    merge_nodes['dcoord'] = hierarchy_dendrogram['dcoord1'].copy()

    ## formulate colors
    merge_nodes['color_line'] = colors.loc[params['shading']['border']['Bracket'],'grey']
    merge_nodes['color_fill'] = colors.loc[params['shading']['fill']['Bracket'],  'grey']
    merge_nodes['label_type'] = 'hover'
    merge_nodes.loc[merge_nodes['dcoord'] >= params['label_height'], 'label_type'] = 'text'
    merge_nodes = merge_nodes.loc[merge_nodes['dcoord'] < params['too_high']]
    return merge_nodes.reset_index(drop = True)


def make_dendrogram(city_list:pd.DataFrame, colors:pd.DataFrame) -> list:
    """Wrapper function that executes the other functions in this section. Calculates a distance
    dendrogram for a set of points and returns the coordinate data necessary to draw that
    dendrogram.
        city_list = project's main dataset.  Provides destination-wise information about my travels
            and travel goals
        colors = project's color palette matrix.  Projects the standard colors used across the
            project.
    """
    hierarchy_linkage = make_hierarchy_linkage(city_list = city_list)
    hierarchy_linkage = name_composite_nodes(city_list = city_list, linkage = hierarchy_linkage)
    hierarchy_dendrogram = make_hierarchy_dendrogram(
        city_list=city_list, linkage=hierarchy_linkage, colors=colors)
    leaf_nodes = extract_leaf_nodes(hierarchy_dendrogram=hierarchy_dendrogram, city_list=city_list)
    merge_nodes = extract_merge_nodes(hierarchy_dendrogram=hierarchy_dendrogram, colors=colors)
    return hierarchy_dendrogram, leaf_nodes, merge_nodes

##########==========##########==========##########==========##########==========##########==========
## COMPONENT FUNCTIONS - render figure

def make_figure(params = params):
    """ Generates a blank Plotly figure with suitable parameters for this script's dendrograms.
    Inputs:
        params = The parameters dictionary defined at the top of this script.  Provides easy
            access to parameters that might need adjustment.
    """
    fig = go.Figure()
    fig = fig.update_layout(
        template = 'plotly_dark',
        showlegend = False,
        width = params['width'], height = params['height'],
        plot_bgcolor  = 'hsv(0,0,0)',
        paper_bgcolor = 'hsv(0,0,0)',
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


def draw_dendrogram(trace_dict:dict, hierarchy_dendrogram:pd.DataFrame, prefix:str, params=params) -> dict:
    """ Converts dendrogram coordinates to plotly traces, and appends them to a dict of traces.
    Inputs:
        trace_dict = a dict object to be filled with plotly traces.  These traces will be
            drawn in the plotly figure during write_figure() and also tied into a slider
            bar in add_slider().
        hierarchy_dendrogram = Coordinates needed to draw a dendrogram representation of a 
            the distances between destinations
        prefix = an identifying string added to the dict keys for the traces generated.
        params = The parameters dictionary defined at the top of this script.  Provides easy
            access to parameters that might need adjustment.
    """
    icoords = ['icoord' + str(i) for i in range(0, 4)]
    dcoords = ['dcoord' + str(i) for i in range(0, 4)]
    new_traces = dict()
    for iter_row in hierarchy_dendrogram.index:
        name_now = hierarchy_dendrogram.loc[iter_row, 'up_name']
        new_traces[prefix + '∆' + name_now + '∆bracket'] = go.Scatter(
            x = hierarchy_dendrogram.loc[iter_row, dcoords],
            y = hierarchy_dendrogram.loc[iter_row, icoords],
            hoverinfo = 'none', showlegend = False, mode = 'lines',
            line = dict(color = hierarchy_dendrogram.loc[iter_row, 'color']),
            name = name_now,
            visible = params['first_visible'] == int(prefix.split('_')[0])
        )
    trace_dict.update(new_traces)
    return trace_dict


def label_nodes(trace_dict, leaf_nodes, merge_nodes, prefix:str, params=params):
    """ Adds traces to a dict of traces.  Traces depict destinations at the terminal edge
    of the dendrograms.
    Inputs:
        trace_dict = a dict object to be filled with plotly traces.  These traces will be
            drawn in the plotly figure during write_figure() and also tied into a slider
            bar in add_slider().
        leaf_nodes = Information on the terminal nodes (destinations).  Extracted from the 
            dendrogram coordinates object.
        merge_nodes = Information on the non-terminal nodes (destination groups).  Extracted from
            the dendrogram coordinates object.
        prefix = an identifying string added to the dict keys for the traces generated.
        params = The parameters dictionary defined at the top of this script.  Provides easy
            access to parameters that might need adjustment.
    """
    new_traces = dict()

    ## draw leaf nodes
    new_traces[prefix + '∆leaf_nodes'] = go.Scatter(
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
        textposition = 'middle left',
        visible = params['first_visible'] == int(prefix.split('_')[0])
        )

    ## upper merges
    idx = merge_nodes['label_type'] == 'text'
    new_traces[prefix + '∆upper_merge_nodes'] = go.Scatter(
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
        textposition = 'middle left',
        visible = params['first_visible'] == int(prefix.split('_')[0])
        )

    ## lower merges
    idx = merge_nodes['label_type'] == 'hover'
    new_traces[prefix + '∆lower_merge_nodes'] = go.Scatter(
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
        textposition = 'middle left',
        visible = params['first_visible'] == int(prefix.split('_')[0])
        )

    trace_dict.update(new_traces)
    return trace_dict


def add_slider(trace_dict:dict, colors:pd.DataFrame, params=params) -> list:
    """ Generates slider specifications for the plotly object.
    Input:
        trace_dict = A dict containing all of the plotly traces drawn so far. The slider controls
            which traces are visible.
        colors = project's color palette matrix.  Projects the standard colors used across the
            project.
        params = The parameters dictionary defined at the top of this script.  Provides easy
            access to parameters that might need adjustment.
    """

    ## generate visibility information
    visible= sorted(list(set([i.split('∆')[0] for i in trace_dict.keys()])))
    visible= {i:[j.startswith(i) for j in trace_dict.keys()] for i in visible}

    ## package visibility information in step format
    for iter_step in visible.keys():
        visible[iter_step] = dict(
            method= 'update',
            label = iter_step[3::].replace(' (Mid)', '<br>(Mid)').upper(),
            args = [dict(visible=visible[iter_step])]
        )
    visible = [visible[i] for i in visible.keys()]

    ## package visibility information in slider format
    slider = [dict(
        font = dict(size=10, color=colors.loc['L','grey']),
        currentvalue=dict(font=dict(size=12), prefix='Month: '),
        active=params['first_visible'] - 1, steps=visible, pad=dict(b=0, l=8, r=8, t=0)
        )]
    return slider


def write_figure(fig:go.Figure, trace_dict:dict, slider:list):
    """ Add sliders and traces to a plotly figure.  Write figure as both a self-contained html
    file and also as an html div section.  The self-contained file is for testing / trouble-
    shooting.  0_executve_project.py injects the div code into a data dashboard.
    Inputs:
        fig = a blank, suitably formatted plotly figure
        trace_dict = a dict of plotly traces, ready to write into the figure
        slider = a plotly slider object, defining the relationship between trace visibility
            and the slider's current state.
    """
    fig = fig.add_traces([i for i in trace_dict.values()])
    fig = fig.update_layout(sliders = slider)
    fig.write_html(
        os.path.join('io_mid', 'PROXIMITY.html'), full_html = True, include_plotlyjs = True)
    fig.write_html(
        os.path.join('io_mid', 'PROXIMITY.div'), full_html = False, include_plotlyjs = False)
    div = '\n'.join(open('io_mid/PROXIMITY.div', 'rt').readlines())
    return div


##########==========##########==========##########==========##########==========##########==========
## TOP-LEVEL FUNCTIONS


def draw_proximity_panel():
    """ draw_proximity_panel() is the main function for this script.  It executes all of the other
    functions.  execute_project.py imports this function to execute the project from start to
    finish.
    """
    ## initialize plotly figure
    fig, trace_dict = make_figure()

    ## import data
    city_list, best_months, colors = import_data()
    city_list = assign_colors(city_list=city_list, colors=colors)
    city_list = project_coordinates(city_list=city_list)

    ## generate dendrograms for each month
    for iter_month in best_months.columns:
        hierarchy_dendrogram, leaf_nodes, merge_nodes = make_dendrogram(
            city_list=city_list.loc[best_months[iter_month].values], colors=colors)
        trace_dict = draw_dendrogram(trace_dict=trace_dict,
                                hierarchy_dendrogram=hierarchy_dendrogram, prefix=iter_month)
        trace_dict = label_nodes(trace_dict=trace_dict,
                                leaf_nodes=leaf_nodes, merge_nodes=merge_nodes, prefix=iter_month)

    ## assemble figure and write to disk as html code
    slider = add_slider(trace_dict=trace_dict, colors=colors)
    write_figure(fig=fig, trace_dict=trace_dict, slider = slider)
    return None


##########==========##########==========##########==========##########==========##########==========
## CODE TESTS
    
if __name__ == '__main__':
    draw_proximity_panel()



##########==========##########==========##########==========##########==========##########==========