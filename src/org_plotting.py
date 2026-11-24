#!usr/bin/python
# -*- coding: utf-8 -*-import string

BASE_LINEWIDTH = 1

# default colors:
LINECOLORS = ["red", "blue", "green", "purple", "magenta", "orange", "cyan", "pink", "olive"]

#VALID_KEY_TYPES = ["COLOR_KEYS_CATEGORICAL", "COLOR_KEYS_CONTINUOUS", "DATA_KEYS_CATEGORICAL", "DATA_KEYS_CONTINUOUS"]

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

DATA_KEYS_CONTINUOUS = [
	"distance",
	"time",
	"elevation",
	"elevation relative",
	"elevation gain",
	"speed",
	"pace",
	"slope"
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


'''
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


def format_data(key, value):
	if key == "distance":
		dist_km = value/1000
		return f"{dist_km:03.1f}"
	elif key == "time":
		return format_time_hours(value)
	elif key == "elevation":
		return f"{value:.0f}"
	elif key == "elevation relative":
		return f"{value:.0f}"
	elif key == "elevation gain":
		return f"{value:.0f}"
	elif key == "slope":
		slope_pct = value*100
		return f"{slope_pct:2.0f}"
	elif key == "pace":
		return float_to_pace_str(value)
	elif key == "speed":
		return f"{value:.1f}"
	elif key == "date":
		return datetime.fromtimestamp(value).date()
	elif key == "total distance":
		dist_km = value/1000
		return f"{dist_km:03.1f}"
	elif key == "total duration":
		return format_time_hours(value)
	elif key == "total elevation":
		return f"{value:.0f}"	
'''