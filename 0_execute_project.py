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