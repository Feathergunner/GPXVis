#!usr/bin/python
# -*- coding: utf-8 -*-import string

import matplotlib as mpl

from org import LINECOLORS

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

COLORS_CATEGORICAL = LINECOLORS

class ColorManager():
	def __init__(self, color_key:str, activities:list):
		self.color_key = color_key
		self.is_categorical = self.color_key in COLOR_KEYS_CATEGORICAL

		self.athlete_id_to_color_id = {}
		self.type_id_to_color_id = {}
		self.activity_id_to_color_id = {}
		self.min_value = None
		self.max_value = None
		self.colormap_name = "turbo"

		self._setup(activities)

	def __str__(self):
		retstr = ""
		retstr += "athlete_id_to_color_id:"+str(self.athlete_id_to_color_id)+"\n"
		retstr += "type_id_to_color_id:"+str(self.type_id_to_color_id)+"\n"
		retstr += "activity_id_to_color_id:"+str(self.activity_id_to_color_id)
		return retstr

	def _setup(self, activities:list) -> None:
		'''
		parses the activities to determine parameters by which colors are decided
		'''
		if self.color_key == "athlete":
			# find all athlete_ids, assign each a unique color_id
			number_of_athletes = 0
			for activity in activities:
				if activity["athlete_id"] not in self.athlete_id_to_color_id:
					self.athlete_id_to_color_id[activity["athlete_id"]] = number_of_athletes
					number_of_athletes += 1

		elif self.color_key == "activitytype":
			# find all activitytype_ids, assign each a unique color_id
			number_of_types = 0
			for activity in activities:
				if activity["activitytype_id"] not in self.type_id_to_color_id:
					self.type_id_to_color_id[activity["activitytype_id"]] = number_of_types
					number_of_types += 1

		elif self.color_key == "activity":
			# assign unique color id to each activity:
			# (note that actual colors are not unique, since only colors from COLORS_CATEGORICAL are used)
			self.activity_id_to_color_id = {activities[k]["id"] : k for k in range(len(activities))}

		elif self.color_key == "date":
			self.colormap_name = "viridis"
			# find range of values:
			for activity in activities:
				if self.min_value is None:
					self.min_value = activity["datetime"].date()
				elif activity["datetime"].date() < self.min_value:
					self.min_value = activity["datetime"].date()
				if self.max_value is None:
					self.max_value = activity["datetime"].date()
				elif activity["datetime"].date() > self.max_value:
					self.max_value = activity["datetime"].date()
		else:
			return

	def _get_color_categorical(self, color_id):
		return COLORS_CATEGORICAL[color_id%len(COLORS_CATEGORICAL)]

	def _get_color_continuous(self, value):
		# determine relative value using lower and upper bound of value range
		relative_value = (value-self.min_value)/(self.max_value-self.min_value)
		# use colormap to get a color
		color = mpl.colormaps[self.colormap_name](relative_value)
		return color

	def get_color(self, datapoint):
		if self.color_key == "athlete":
			return self._get_color_categorical(self.athlete_id_to_color_id[datapoint["athlete_id"]])

		elif self.color_key == "activitytype":
			return self._get_color_categorical(self.type_id_to_color_id[datapoint["activitytype_id"]])

		elif self.color_key == "activity":
			return self._get_color_categorical(self.activity_id_to_color_id[datapoint["id"]])

		elif self.color_key == "date":
			return self._get_color_continuous(datapoint["datetime"].date())

		elif self.color_key == "singular":
			return "red"

		else:
			# something went wrong
			print ("unknwon color_key:",self.color_key)
			return "blue"
		
