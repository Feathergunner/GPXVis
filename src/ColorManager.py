#!usr/bin/python
# -*- coding: utf-8 -*-import string

import numpy as np
import matplotlib as mpl
import datetime

#from src import ActivityPlotter as AP

from src.org_plotting import LINECOLORS, COLOR_KEYS_CATEGORICAL, COLOR_KEYS_CONTINUOUS
from src.misc import format_time_hours, float_to_pace_str

COLORS_CATEGORICAL = LINECOLORS

class PlotAxisKey():
	def __init__(self,
			key:str,
			label:str,
			unit:str,
			format,
			range_min = None,
			range_max = None):
		
		self.key = key
		self.label = label
		self.unit = unit
		self.format = format
		self.range_min = range_min
		self.range_max = range_max

ALL_KEYS = {
	"distance" : PlotAxisKey(
		"distance_since_start",
		"distance",
		"km",
		lambda val: f"{val/1000:03.1f}",
		0),
	"time" : PlotAxisKey(
		"time_since_start",
		"time",
		"h:min:sec",
		format_time_hours,
		datetime.timedelta(0)),
	"elevation" : PlotAxisKey(
		"elevation",
		"elevation",
		"m",
		lambda val: f"{val:.0f}"),
	"elevation relative" : PlotAxisKey(
		"elevation_relative",
		"elevation relative to start",
		"m",
		lambda val: f"{val:.0f}"),
	"elevation gain" : PlotAxisKey(
		"elevation_gain_since_start",
		"elevation gain",
		"m",
		lambda val: f"{val:.0f}",
		0),
	"slope" : PlotAxisKey(
		"slope",
		"slope",
		"%",
		lambda val: f"{val/100:2.0f}",
		-0.5,
		0.5),
	"slope_max" : PlotAxisKey(
		"slope_max",
		"maximum slope",
		"%",
		lambda val: f"{val/100:2.0f}",
		-0.5,
		0.5),
	"pace" : PlotAxisKey(
		"pace",
		"pace",
		"min/km",
		float_to_pace_str,
		2,
		30),
	"pace_best" : PlotAxisKey(
		"pace_best",
		"fastest pace",
		"min/km",
		float_to_pace_str,
		2,
		30),
	"speed" : PlotAxisKey(
		"speed",
		"speed",
		"km/h",
		lambda val: f"{val:.1f}",
		2,
		30),
	"speed_best" : PlotAxisKey(
		"speed_best",
		"fastest speed",
		"km/h",
		lambda val: f"{val:.1f}",
		2,
		30),
	"heartrate" : PlotAxisKey(
		"heartrate",
		"heartrate",
		"bpm",
		lambda val: f"{val:.0f}",
		30,
		300),
	"heartrate_max" : PlotAxisKey(
		"heartrate_max",
		"maximum heartrate",
		"bpm",
		lambda val: f"{val:.0f}",
		30,
		300),
	"cadence" : PlotAxisKey(
		"cadence",
		"cadence",
		"spm",
		lambda val: f"{val:.0f}",
		0),
	"athlete" : PlotAxisKey(
		"athlete_name",
		"athlete name",
		"",
		lambda val:val),
	"activitytype" : PlotAxisKey(
		"type_name",
		"activitytype",
		"",
		lambda val:val),
	"date" : PlotAxisKey(
		"date",
		"date",
		"YYYY-MM-DD",
		#lambda val: datetime.fromtimestamp(val).date()),
		lambda val: val.date()),
	#"pace average" : PlotAxisKey(
	#	"pace average",
	#	"average pace",
	#	"min/km",
	#	float_to_pace_str,
	#	2,
	#	30),
	#"speed average" : PlotAxisKey(
	#	"speed average",
	#	"average speed",
	#	"km/h",
	#	lambda val: f"{val:.1f}",
	#	2,
	#	30),
	#"distance total" : PlotAxisKey(
	#	"distance total",
	#	"total distance",
	#	"km",
	#	lambda val: f"{val/1000:03.1f}",
	#	0),
	#"duration total" : PlotAxisKey(
	#	"duration total",
	#	"total duration",
	#	"h:min:sec",
	#	format_time_hours,
	#	0),
	#"elevation total" : PlotAxisKey(
	#	"elevation total",
	#	"total elevation",
	#	"m",
	#	lambda val: f"{value:.0f}",
	#	0),
	"singular" : PlotAxisKey(
		"singular",
		"",
		"",
		lambda val: None),
	"activity" : PlotAxisKey(
		"activity",
		"",
		"",
		lambda val: val.activity_dto.name)
}

class ColorManager():
	def __init__(self, plotter, so):#:AP.ActivityPlotter, so:AP.SpecificationObject):
		self.plotter = plotter
		self.color_key = so.key_color
		self.is_categorical = self.color_key.key in COLOR_KEYS_CATEGORICAL

		self.athlete_id_to_color_id = {}
		self.type_id_to_color_id = {}
		self.activity_id_to_color_id = {}
		self.min_value = None
		self.max_value = None
		self.colormap_name = "turbo"
		self.continuous_ticks = []
		self.continuous_ticks_labels = []

		self._setup()

	def __str__(self):
		retstr = ""
		retstr += "athlete_id_to_color_id:"+str(self.athlete_id_to_color_id)+"\n"
		retstr += "type_id_to_color_id:"+str(self.type_id_to_color_id)+"\n"
		retstr += "activity_id_to_color_id:"+str(self.activity_id_to_color_id)
		return retstr

	def _setup(self) -> None:
		'''
		parses the activities to determine parameters by which colors are decided
		'''
		if self.color_key.key == "athlete":
			# find all athlete_ids, assign each a unique color_id
			number_of_athletes = 0
			for activity in self.plotter.activities:
				if activity.athlete_id not in self.athlete_id_to_color_id:
					self.athlete_id_to_color_id[activity.athlete_id] = number_of_athletes
					number_of_athletes += 1

		elif self.color_key.key == "activitytype":
			# find all activitytype_ids, assign each a unique color_id
			number_of_types = 0
			for activity in self.plotter.activities:
				if activity.activitytype_id not in self.type_id_to_color_id:
					self.type_id_to_color_id[activity.activitytype_id] = number_of_types
					number_of_types += 1

		elif self.color_key.key == "activity":
			# assign unique color id to each activity:
			# (note that actual colors are not unique, since only colors from COLORS_CATEGORICAL are used)
			self.activity_id_to_color_id = {self.plotter.activities[k].id : k for k in range(len(self.plotter.activities))}

		#elif self.color_key.key == "date":
		#	self.colormap_name = "viridis"
		#	# find range of values:
		#	for activity in self.plotter.activities:
		#		if self.min_value is None:
		#			self.min_value = activity.datetime.date()
		#		elif activity.datetime.date() < self.min_value:
		#			self.min_value = activity.datetime.date()
		#		if self.max_value is None:
		#			self.max_value = activity.datetime.date()
		#		elif activity.datetime.date() > self.max_value:
		#			self.max_value = activity.datetime.date()
		#	tick_stepsize = (self.max_value.toordinal()-self.min_value.toordinal())/10
		#	self.continuous_ticks = np.arange(self.min_value.toordinal(), self.max_value.toordinal()+tick_stepsize, tick_stepsize)
		#	self.continuous_ticks_labels = [datetime.date.fromordinal(int(t)) for t in self.continuous_ticks]
		else:
			self.colormap_name = "viridis"
			# find range of values:
			if self.color_key.key == "date":
				for activity in self.plotter.activities:
					activity_value = activity.activity_dto.datetime
					if self.min_value is None or activity_value < self.min_value:
						self.min_value = activity_value
					if self.max_value is None or activity_value > self.min_value:
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
			self.continuous_ticks = [self.min_value+i*tick_stepsize for i in range(10)]
			self.continuous_ticks_labels = [self.color_key.format(t) for t in self.continuous_ticks]

			self.min_value = self._sanitize_value(self.min_value)
			self.max_value = self._sanitize_value(self.max_value)

	def _get_color_categorical(self, color_id):
		return COLORS_CATEGORICAL[color_id%len(COLORS_CATEGORICAL)]

	def _get_color_continuous(self, value):
		# determine relative value using lower and upper bound of value range
		relative_value = (self._sanitize_value(value)-self.min_value)/(self.max_value-self.min_value)
		# use colormap to get a color
		color = mpl.colormaps[self.colormap_name](relative_value)
		return color

	def _sanitize_value(self, value):
		if self.color_key.key == "time_since_start":
			return value.total_seconds()
		elif self.color_key.key == "date":
			return value.toordinal()
		else:
			return value

	def get_color_legend_data(self):
		if self.color_key.key in COLOR_KEYS_CONTINUOUS:
			return (self.continuous_ticks, self.continuous_ticks_labels)
		else:
			return ([],[])

	def get_color(self, x):
		return "blue"

	def get_color_by_activity(self, activity_dto):
		if self.color_key.key == "athlete":
			return self._get_color_categorical(self.athlete_id_to_color_id[activity_dto.athlete_id])

		elif self.color_key.key == "activitytype":
			return self._get_color_categorical(self.type_id_to_color_id[activity_dto.activitytype_id])

		elif self.color_key.key == "activity":
			return self._get_color_categorical(self.activity_id_to_color_id[activity_dto.id])

		elif self.color_key.key == "date":
			return self._get_color_continuous(activity_dto.datetime.date())

		elif self.color_key.key == "singular":
			return "red"

		else:
			# something went wrong
			print ("unknwon color_key:",self.color_key.key)
			return "blue"
		
	def get_color_by_split(self, split):
		return self._get_color_continuous(getattr(split, self.color_key.key))