# GPX Visualiser
Successor of https://github.com/Feathergunner/Activisualizer

Visualizing data from gpx-files:
- plotting routes on maps: supports plotting multiple routes on a single map, and different colors for sets of routess
- freely configurable plots of distance, height, elevation gain, slope, and (if timestamps are contained in gpx-files) time, speed, pace

![example_animation](examples_and_screenshots/example_animation.mp4 "Animation")

![example_map](examples_and_screenshots/example_map.png "Map")

![example_profile_height](examples_and_screenshots/example_plot_distance_height.png "Plot height")
![example_profile_elevation](examples_and_screenshots/example_plot_time_elevationgain.png "Plot elevation")
![example_profile_pace](examples_and_screenshots/example_plot_distance_pace.png "Plot pace")

![screenshot_upload](examples_and_screenshots/screenshot_upload.png "Upload")
![screenshot_database](examples_and_screenshots/screenshot_database.png "Database")
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

and ffmpeg.