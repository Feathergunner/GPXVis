#!usr/bin/python
# -*- coding: utf-8 -*-import string

BASE_LINEWIDTH = 1

# default colors:
LINECOLORS = ["red", "blue", "green", "purple", "magenta", "orange", "cyan", "pink", "olive"]

COLOR_KEYS_CATEGORICAL = [
	"singular",			# everything the same color
	"athlete",			# color by athlete
	"activitytype",		# color by activity type
	"activity"			# each activity unique color
]
COLOR_KEYS_CONTINUOUS = [
	#"elevation",		# not yet implemented
	"date"				# color by date
]

DATA_KEYS_CATEGORICAL = [
	"athlete",
	"activitytype",
	"date",
	"avg pace",
	"avg speed",
	"total distance",
	"total duration",
	"total elevation",
]

# for html form creation:
AXIS_DIM_CONT = [
	{"value" : "distance", "label": "Distance"},
	{"value" : "time", "label": "Time"},
	{"value" : "elevation", "label": "Elevation"},
	{"value" : "elevation relative", "label": "Elevation relative to start"},
	{"value" : "elevation gain", "label": "Elevation Gain"},
	{"value" : "slope", "label": "Slope"},
	{"value" : "pace", "label": "Pace"},
	{"value" : "speed", "label": "Speed"}
]

AXIS_DIM_CAT = [
	{"value" : "date", "label": "Date"},
	{"value" : "avg pace", "label": "Average Pace"},
	{"value" : "avg speed", "label": "Average Speed"},
	{"value" : "total distance", "label": "Total Distance"},
	{"value" : "total duration", "label": "Duration"},
	{"value" : "total elevation", "label": "Total Elevation"}
]

AXIS_DOM_COLOR = [
	{"value" : "singular", "label" : "Everything in the same color"},
	{"value" : "activity" , "label" : "Activity"},
	{"value" : "athlete" , "label" : "Athlete"},
	{"value" : "activitytype", "label" : "Activity Type"},
	{"value" : "date", "label" : "Date"}
]

# graph parameters:
PLOT_WIDTH = 16
PLOT_HEIGHT = 9
PLOT_DPI = 100

KEY_UNITS = {
	"distance" : "km",
	"time" : "h:min",
	"elevation" : "m",
	"elevation relative" : "m",
	"elevation gain" : "m",
	"slope" : "%",
	"pace" : "min/km",
	"avg pace" : "min/km",
	"speed" : "km/h",
	"avg speed" : "km/h",
	"date" : "YYYY-MM-DD",
	"total distance" : "km",
	"total duration" : "h:min:sec",
	"total elevation" : "m",
}

KEY_RANGE_MIN = {
	"distance" : None,
	"time" : None,
	"elevation" : None,
	"elevation relative" : None,
	"elevation gain" : 0,
	"slope" : -0.5,
	"pace" : 2,
	"avg pace" : 2,
	"speed" : 4,
	"avg speed" : 4,
	"date" : None,
	"total distance" : 0,
	"total duration" : 0,
	"total elevation" : 0,
}

KEY_RANGE_MAX = {
	"distance" : None,
	"time" : None,
	"elevation" : None,
	"elevation relative" : None,
	"elevation gain" : None,
	"slope" : 0.5,
	"pace" : 15,
	"avg pace" : 15,
	"speed" : 30,
	"avg speed" : 30,
	"date" : None,
	"total distance" : None,
	"total duration" : None,
	"total elevation" : None,
}