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
	"date",
	"avg pace",
	"total distance",
	"total duration",
	"total elevation",
]