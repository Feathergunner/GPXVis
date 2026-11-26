#!usr/bin/python
# -*- coding: utf-8 -*-import string

import numpy as np
import matplotlib as mpl

from src.plotting.AxisSpecs import AxisDataSource, AXIS_NOAXIS
from src.plotting.org_plotting import LINECOLORS, COLOR_KEYS_CONTINUOUS

from src.misc import get_sanitized_value

COLORS_CATEGORICAL = LINECOLORS

class ColorManager():
	def __init__(self, plotter, so):
		self.plotter = plotter # ActivityPlotter
		self.color_key = so.key_color # AxisSpecs

		self.element_id_to_color_id = {}
		self.min_value = None
		self.max_value = None
		self.colormap_name = "turbo"
		self.continuous_ticks = []
		self.continuous_ticks_labels = []

		self._setup()

	def __str__(self):
		retstr = "ColorManager:\n"
		retstr += "  element_id_to_color_id:"+str(self.element_id_to_color_id)
		return retstr

	def _setup(self) -> None:
		'''
		parses the activities to determine parameters by which colors are decided
		'''
		if self.color_key.color_cat:
			# case categorical color:
			number_of_unique_elements = 0
			if self.color_key == AXIS_NOAXIS:
				number_of_unique_elements = 1
				self.element_id_to_color_id = {activity.activity_dto.id : 0 for activity in self.plotter.activities}
			else:
				for activity in self.plotter.activities:
					element = None
					if self.color_key.datasource == AxisDataSource.ACTIVITY_DTO:
						element_id = getattr(activity.activity_dto, self.color_key.key)
						if element_id not in self.element_id_to_color_id:
							self.element_id_to_color_id[element_id] = number_of_unique_elements
							number_of_unique_elements += 1

		elif self.color_key.color_cont:
			self.colormap_name = "viridis"
			# find range of values:
			if self.color_key.key == "date":
				for activity in self.plotter.activities:
					activity_value = activity.activity_dto.datetime
					if self.min_value is None or activity_value < self.min_value:
						self.min_value = activity_value
					if self.max_value is None or activity_value > self.max_value:
						self.max_value = activity_value
			else:
				for activity in self.plotter.activities:
					activity_min_value = min([getattr(split, self.color_key.key) for split in activity.splits])
					if self.min_value is None or activity_min_value < self.min_value:
						self.min_value = activity_min_value
					activity_max_value = max([getattr(split, self.color_key.key) for split in activity.splits])
					if self.max_value is None or activity_max_value > self.max_value:
						self.max_value = activity_max_value
			# sanitize bounds:
			if self.color_key.range_min is not None:
				self.min_value = max(self.min_value, self.color_key.range_min)
			if self.color_key.range_max is not None:
				self.max_value = min(self.max_value, self.color_key.range_max)
			# construct ticks and labels for colorbar:
			tick_stepsize = (self.max_value-self.min_value)/10
			self.continuous_ticks = [self.min_value+i*tick_stepsize for i in range(11)]
			self.continuous_ticks_labels = [self.color_key.format(t) for t in self.continuous_ticks]
			self.continuous_ticks = [self.get_sanitized_value(ct) for ct in self.continuous_ticks]

	def _get_color_categorical(self, color_id):
		return COLORS_CATEGORICAL[color_id%len(COLORS_CATEGORICAL)]

	def _get_color_continuous(self, value):
		# determine relative value using lower and upper bound of value range
		relative_value = (self.get_sanitized_value(value)-self.get_sanitized_value(self.min_value))/(self.get_sanitized_value(self.max_value)-self.get_sanitized_value(self.min_value))
		# use colormap to get a color
		color = mpl.colormaps[self.colormap_name](relative_value)
		return color

	def get_sanitized_value(self, value):
		return get_sanitized_value(value)	
		#if self.color_key.key == "time_since_start":
		#	return value.total_seconds()
		#elif self.color_key.key == "date":
		#	return value.toordinal()
		#else:
		#	return value

	def get_color_legend_data(self):
		#if self.color_key.key in COLOR_KEYS_CONTINUOUS:
		return (self.continuous_ticks, self.continuous_ticks_labels)
		#else:
		#	return ([],[])

	def get_color(self, x):
		return "blue"

	def get_color_by_activity(self, activity):
		if self.color_key == AXIS_NOAXIS:
			return "red"
		elif self.color_key.datasource == AxisDataSource.ACTIVITY_DTO:
				element_id = getattr(activity.activity_dto, self.color_key.key)
				return self._get_color_categorical(self.element_id_to_color_id[element_id])
		elif self.color_key.datasource == AxisDataSource.ACTIVITY:
			value = getattr(activity, self.color_key.key)
			return self._get_color_continuous(value)
		else:
			print ("unknwon datasource:",self.color_key.datasource)
			return "blue"
		#else:
		#	# something went wrong
		#	print ("unknwon color_key:",self.color_key.key)
		#	return "blue"
		
	def get_color_by_split(self, split):
		return self._get_color_continuous(getattr(split, self.color_key.key))