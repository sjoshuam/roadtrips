##########==========##########==========##########==========##########==========

## github.com/sjoshuam/roadtrips
Repo creation date: 2023-12-25

#### Overview

Builds an information dashboard that depicts my travels across the United States,
tracks progress towards achieving travel goals, and and provides tools to assist
future travel planning.

Project is actively under development.  This GitHub Kanban board tracks the work: 
https://github.com/users/sjoshuam/projects/2/views/1

Project code consists of a main execution script (0_execute_project.py), py files
that generate different project components, and an html file (readtrips.html) to
fuse components together into a unified data display.  The components are:

+ d1_weather: Download NOAA weather data and compile it into information on the
        best time to visit each destination.
+ p1_progress: Tally basic statistics on progress achieving travel goals and depict
        as html-based visualizations.  Packge visualization code so it can slot into
        a div section within the project's main html page.
+ p2_proximity: Place destinations into hierarchical groups that are close together
        and depict those relationships visually.  This provides a planning tool for
        future roadtrips. In general, the closer destinations are, the more suitable
        they are for being visited in the same trip.  Packge visualization so it can
        slot into a div section within the project's main html page.
+ p3_map: Generates html map displays to show information about the typical weather
        conditions in each destination at different periods throughout the year
        (planning tool).  Also, depicts information about past travels, including
        routes and visits.  This displays, linked together with a slider bar, generate
        the core panel of this project's html page.
+ p4_oconus: Depicts the four destinations outside the contiguous United States (in DC
        parlance, those destinations are OCONUS) as well as a map key. Packge
        visualization so it can slot into a div section within the project's main html
        page.

The main outputs from this project are roadtrips.html and roadtrips.css, which together
fuse all data visualizations into a data dashboard.

#### Weather (Climate Normals) Data Source

https://www.ncei.noaa.gov/data/normals-hourly/1991-2020/doc/hly_inventory_30yr.txt

https://www.ncei.noaa.gov/data/normals-hourly/1991-2020/doc/Readme_By-Variable_By-Station_Normals_Files.txt

https://www.ncei.noaa.gov/data/normals-hourly/1991-2020/access/*.csv

