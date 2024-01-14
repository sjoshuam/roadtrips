"""
    Purpose: Compiles all the .div outputs from other py modules into a single html page.
        TODO: Make script trigger modules to run, instead of just passively reading div files
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
        #14 Add doc strings to all functions
        #16 Wire module into a run-everything execute_project() function in 0_execute_project.py
"""
##########==========##########==========##########==========##########==========##########==========
## HEADER

import shutil, os

##########==========##########==========##########==========##########==========##########==========
## DEFINE COMPONENT FUNCTIONS

def import_html():
    """read in empty html dashboard"""
    return '\n'.join(open('io_in/roadtrips.html', 'rt').readlines())


def inject_stats(html):
    """Fill in statistics as needed"""
    stats = open(os.path.join('io_mid', 'STATS.txt'), 'rt').readlines()
    for j in [i.split(':') for i in stats]:
        html = html.replace('<insert>' + j[0] + '</insert>', j[1])
    return html


def inject_div(id, html, div_class):
    find_string = f'<div class="{div_class}"><insert>{id}</insert></div>'
    replace_string = '\n'.join(open(f'io_mid/{id}.div', 'rt').readlines())
    html = html.replace(find_string, replace_string)
    html = html.replace('<div>', f'<div class="{div_class}">')
    return html


def export_html(html):
    """
        TODO
    """
    open('io_out/roadtrips.html', 'wt').writelines(html)
    shutil.copyfile('io_in/roadtrips.css', 'io_out/roadtrips.css')
    shutil.copyfile('io_in/roadtrips.png', 'io_out/roadtrips.png')
    for iter_ext in ['html', 'png', 'css']:
        shutil.copyfile(f'io_out/roadtrips.{iter_ext}', f'../portfolio/p/roadtrips.{iter_ext}')
    return None

##########==========##########==========##########==========##########==========##########==========
## DEFINE TOP-LEVEL FUNCTIONS

##########==========##########==========##########==========##########==========##########==========
## TEST CODE

if __name__ == '__main__':
    html = import_html()
    html = inject_stats(html = html)
    html = inject_div(id = 'PROGRESS',  html = html, div_class = 'facet_panel' )
    html = inject_div(id = 'MAP',       html = html, div_class = 'main_panel'  )
    html = inject_div(id = 'OCONUS',    html = html, div_class = 'oconus_panel')
    html = inject_div(id = 'PROXIMITY', html = html, div_class = 'bottom_panel')
    export_html(html)

##########==========##########==========##########==========##########==========##########==========