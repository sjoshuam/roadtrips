"""
    Compiles all the .div outputs from other py modules into a single html page and exports files
        to the portfolio project's code directory for upload to the github.io website.
        See params to True to generate the weather data and html divs used to build this page.
    Inputs:
        PROGRESS.div, PROXIMITY.div, MAP.div, OCONUS.div: output files containing the data
            displays that will be showcased on the project's main html page.
        roadtrips.css, roadtrips.html: the code for the project's main html page.  The div
            outputs from other modules are injected into roadtrips.html
        roadtrips.png: a manual snapshot of roadtrips.html with a 3:5 aspect ratio.  Serves as
            the preview thumbnail for the project.
    Outputs:
        roadtrips.html: the project's main html page, with div element outputs from all other
            modules injected into it.
        Note: roadtrips.html, css, and png are copied over to ../portfolio where will be uploaded
            periodically to sjoshuam.github.io as part of my portfolio of work.
    Open GitHub Issues:
        # None.  This file is good to go.
"""
##########==========##########==========##########==========##########==========##########==========
## HEADER

params = dict(
    download_weather_data = True,
    regenerate_divs = True
)

## functions needed to create assemble the data dashboard html
import shutil, os
import pandas as pd

## functions needed to regenerate the div files injected into the data dashboard
if params['download_weather_data']:
    from d1_weather import download_weather_data
if params['regenerate_divs']:
    from p1_progress import draw_progress_panel
    from p2_proximity import draw_proximity_panel
    from p3_map import draw_map_panel
    from p4_oconus import draw_oconus_panel

##########==========##########==========##########==========##########==========##########==========
## DEFINE COMPONENT FUNCTIONS


def import_html(file_address = os.path.join('io_in', 'roadtrips.html')) -> str:
    """ Reads in an html file as a text string. This html file is a blank set of divs with id
    tags.  Those divs specify dashboard boxes into which other code can inject plotly html figures.
    The html file also has the text narrating those figures.

    Input:  file_address = location of the html file that function will read in
    Output: html_str = an str object containing the raw html code in the file
    """
    html_str = '\n'.join(open(file_address, 'rt').readlines())
    return html_str


def fill_in_statistics(html_str: str, city_list = os.path.join('io_in', 'city_list.xlsx')) -> str:
    """The explanatory text in the html cites statistics that will change over time as I complete
    more trips.  This function calculates the statistics and injects them into the text.  In the
    html file, the statistics are marked with <insert> tags, so replacement is a simple 
    find-replace operation.

    Input:  html_str = html str ready for find-replace statistic injection.
    Output: html_str = html str with statistics injected into the text
    """

    ## extract statistics
    city_list = pd.read_excel(city_list)
    stats = dict(
        GOAL = str(city_list.shape[0]),
        SOFAR = (~city_list['photo_date'].isna()).sum()
    )
    with_pct = lambda x,y: str(x) + ' (' + str(int(100 * x / y)) + '%)'
    stats['SOFAR'] = with_pct(stats['SOFAR'], city_list.shape[0])

    ## inject statistics into file and return
    for i in stats.keys():
        html_str = html_str.replace(
            '<insert>' + i + '</insert>',
            stats[i]
        )
    return html_str


def inject_div(id: str, html_str: str, div_class: str) -> str:
    """Plotly interactive figures can output as html divs.  Function reads in Plotly figures
    contained in divs and injects them into the main html file.  Functional also modifies the
    class and id attributes, tying the divs into the dashboard's css style sheet.

    Input:  id: indicates the div's file name and also which <insert> tag to replace with the
                Plotly figure's code.
            html_str: an html file with <insert> tags indicating slots for plotly divs
            div_class: str indicating the css div class to be used for that figure.  Primary
                        specifies height / width.
    Output: html_str: the html data dashboard, now with Plotly figures
    """
    find_string = f'<div class="{div_class}"><insert>{id}</insert></div>'
    replace_string = '\n'.join(open(f'io_mid/{id}.div', 'rt').readlines())
    html_str = html_str.replace(find_string, replace_string)
    html_str = html_str.replace('<div>', f'<div class="{div_class}">')
    return html_str


def export_outputs(html_str: str, project_name = 'roadtrips') -> str:
    """Writes html file to disk, and then copies the html, css, png files to the portfolio
    project directory.  This directory holds all of the files used to create the github.io
    website, which showcases this project among others.

    Files:
        html: The html webpage that displays the data dashboard for this project.
        css:  The css style sheet supporting the html file.
        png:  A static preview file that represents this project on the github.io project
                portfolio page.  This png must be created manually.  The project does not create
                it.
    """
    open('io_out/{0}.html'.format(project_name), 'wt').writelines(html_str)
    shutil.copyfile('io_in/{0}.css'.format(project_name), 'io_out/{0}.css'.format(project_name))
    shutil.copyfile('io_in/{0}.png'.format(project_name), 'io_out/{0}.png'.format(project_name))
    for iter_ext in ['html', 'png', 'css']:
        shutil.copyfile(
            f'io_out/{project_name}.{iter_ext}', f'../portfolio/p/{project_name}.{iter_ext}')
    return html_str

##########==========##########==========##########==========##########==========##########==========
## DEFINE TOP-LEVEL FUNCTIONS


def regenerate_dashboard_components(params = params):
    """ Function regenerates the data and files that functions in this module use to construct
    the data databoard
    Inputs: params = determines which components to generate
    Results:
        download_weather_data = downloads data from NOAA to the io_mid/weather_data directory
            and then calculates summary statistics to io_mid/weather_data.xlsx
        regenerate_divs = generates div-formatted Plotly figures used to construct the databoard
    """
    if params['download_weather_data']:
        print('Downloading weather data...')
        download_weather_data()
        print('...Done')
    if params['regenerate_divs']:
        print('Regenerating div files...')
        draw_progress_panel()
        draw_proximity_panel()
        draw_map_panel()
        draw_oconus_panel()
        print('...Done')
    return None


def construct_roadtrip_dashboard():
    """Top-level executable function.  Renders an html web page with interactive plotly figures"""

    ## import html file with empty divs to be filled in with figures plus explainatory text
    html_str = import_html()

    ## inject statistics into the explainatory text to match the latest data
    html_str = fill_in_statistics(html_str = html_str)

    ## inject plotly figures into the empty divs, so that web page renders an interactive dashboard
    html_str = inject_div(id = 'PROGRESS',  html_str = html_str, div_class = 'facet_panel' )
    html_str = inject_div(id = 'MAP',       html_str = html_str, div_class = 'main_panel'  )
    html_str = inject_div(id = 'OCONUS',    html_str = html_str, div_class = 'oconus_panel')
    html_str = inject_div(id = 'PROXIMITY', html_str = html_str, div_class = 'bottom_panel')

    ## export html file, which now has plotly figures and statistics
    return export_outputs(html_str = html_str)


##########==========##########==========##########==========##########==========##########==========
## TEST CODE


if __name__ == '__main__':
    regenerate_dashboard_components()
    html_str = construct_roadtrip_dashboard()


##########==========##########==========##########==========##########==========##########==========