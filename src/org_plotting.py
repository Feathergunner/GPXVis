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