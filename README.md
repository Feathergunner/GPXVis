# GPX Visualiser
Successor of https://github.com/Feathergunner/Activisualizer

Visualizing data from gpx-files:
- Plotting routes on maps: supports plotting multiple routes on a single map, and different colors for sets of routess.
- Freely configurable plots of distance, height, elevation gain, slope, and (if timestamps are contained in gpx-files) time, speed, pace.
- Animations of GPS-tracked activities.

## Examples
### Animation of a Single Activity
![example_animation](examples_and_screenshots/example_animation.gif "Animation")

### Map of Multiple Activities
Activities from two different athletes are displayed, one in red, the other in blue.
![example_map](examples_and_screenshots/example_map.png "Map")

### Plotting Activity Data
For example: elevation profile, total elevation gain, or pace. The x- and y-axes can be specified individually.
![example_profile_height](examples_and_screenshots/example_plot_distance_height.png "Plot height")
![example_profile_elevation](examples_and_screenshots/example_plot_time_elevationgain.png "Plot elevation")
![example_profile_pace](examples_and_screenshots/example_plot_distance_pace.png "Plot pace")

## The User Interface
All scripts can be used via a webinterface, with a local python-flask-server as backend.
To visualize an activity, gpx-files have to be added to the database in the "Upload" tab:
![screenshot_upload](examples_and_screenshots/screenshot_upload.png "Upload")
In the "Database" tab, you can see all database-entries:
![screenshot_database](examples_and_screenshots/screenshot_database.png "Database")
To create a plot, a subset of activities can be selected. This is simply done via the UI by specifying an athlete, an activity-type (e.g. 'running', 'hiking' or 'cycling'), and a date-range.
You also restrict the location of the activities, so you don't accidentally create a huge map that contains all of your hiking trips from all over the world (but if you really want to, you still can generate such a map).
![screenshot_map](examples_and_screenshots/screenshot_maps.png "Map")

## How To Start
1) Run `python App.py` to start a local flask server.
2) Open `127.0.0.1:5000` in a webbrowser.
3) Load your gpx-files (see instructions in webfrontend)
4) Create plots from your data (see instructions in webfrontend)

## Requirements
python 3.10-ish with packages:
- flask
- flask_sqlalchemy
- sqlalchemy
- gpxpy
- matplotlib
- numpy
- PIL
- shutil
- subprocess
- threading

and ffmpeg (to generate the animations).

## Future Features
- Support for more gpx-annotations, like heartrate.
- Improved plots.
- More options for creating animations (multiple activities at once, zoomed-in map).
- QOL features: storing default parameters.
- Improved progress bar.
- Progress bar for uploading activities.
