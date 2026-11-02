#!usr/bin/python
# -*- coding: utf-8 -*-import string

# Directory where gpx files are stored:
GPX_DIR = "gpxdata"
GPX_DIR_TEST = "gpxdata_test"

# approximation of meters per gps-degree.
# We only need a rough approximation, the values are only used to bound the order of magnitude of error when rounding lat/lon data
# value for latitude holds everywhere:
METER_PER_DEG_LAT = 110000
# value for longitude holds at approx 51 degree,
# maybe adjust for approx 1500m per degree if longitude is +/- 10 degrees,
# further away approximation might become to rough
# formula: meters = earth_radius*cos(lon)/360 (with earth_radius approx. 40.000.000m)
METER_PER_DEG_LON = 70000

# The node-merge-precision describes in meter, up to which distance two nodes from different paths might be merged into one.
NODE_MERGE_PRECISION = 5

# this value bounds the degree up to which a sequence of two adjacent edges is considered straight,
# and therefore the middle node might be contracted.
STRAIGHT_PATH_MAX_DEGREE = 5

# reference point for activities:
LAT_HOME = 50.8823
LON_HOME = 11.6109