# GPX Visualiser
Successor of https://github.com/Feathergunner/Activisualizer

Visualizing data from gpx-files:
- plotting routes on maps: supports plotting multiple routes on a single map, and different colors for sets of routess
- freely configurable plots of distance, height, elevation gain, slope, and (if timestamps are contained in gpx-files) time, speed, pace

## How To
1) Run `python App.py` to start a local flask server.
2) Open `127.0.0.1:5000` in a webbrowser.
3) Load your gpx-files (see instructions in webfrontend)
4) Create plots from your data (see instructions in webfrontend)

## Requirements
python 3.10-ish with packages:
- flask
- gpxpy
- matplotlib
- numpy
- PIL
- shutil
