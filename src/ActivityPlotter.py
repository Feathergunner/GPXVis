#!usr/bin/python
# -*- coding: utf-8 -*-import string

#import os
#import copy
#import math
#import numpy as np
#from matplotlib import pyplot as plt
#import matplotlib as mpl
#from datetime import datetime, timezone
#import gpxpy
#
from src.SubTask import SubTask
from src import ColorManager as CM
from src import ActivityPath as AP
from src import DatabaseHandler as DBH
#
#from src.misc import load_gpx_file, parse_gps_from_gpx, get_timestamp_in_seconds, format_time, format_time_hours, float_to_pace_str, ensure_dir_exists, ensure_unique_filename
#from org import GPX_DIR, GPX_DIR_TEST, METER_PER_DEG_LAT, METER_PER_DEG_LON
from src.org_plotting import LINECOLORS, DATA_KEYS_CATEGORICAL, PLOT_WIDTH, PLOT_HEIGHT, PLOT_DPI

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


class PlotSpecificationObject():
	def __init__(self,
			key_x:str,
			key_y:str,
			key_color:str="singular",
			split_type:str="length",
			split_size:int=1000,
			split_aggregates:False,
			name_base:str=""):
		self.key_x = key_x
		self.key_y = key_y
		self.key_color = key_color

		# dimension that is used to define splits:
		self.split_type = split_type
		# has to be one of Split.VALID_SPLIT_DIMENSIONS

		# split size in specified dimension:
		self.split_size = split_size
		
		self.split_aggregates = split_aggregates
		# if true, plot will contain only one datapoint for each split
		#	e.g. for all kinds of plots of aggregated data
		# if false, splits are used for coloring only,
		#	e.g. for elevation profile, mapped routes, etc.
		
		self.name_base = name_base

class MapSpecificationObject():
	def __init__(self,
			dim_x:int,
			dim_y:int,
			latitude_min:float,
			longitude_min:float,
			detaillevel:int):
		# map image size in pixel:
		self.dim_x = dim_x
		self.dim_y = dim_y

		self.latitude_min = latitude_min
		self.longitude_min = longitude_min
		self.detaillevel = detaillevel

class Activity():
	'''
	This class contains all relevant data about a single activity:
	- the metadata and aggregated statistics, as far as they are stored in the database
	- the list of nodes as parsed from the gpx-file
	- the list of records

	Contains functionalities to construct a plot, given a PlotSpecificationObject
	'''
	def __init__(self, activity_dto:DBH.ActivityDTO, nodelist:list, recordlist:list):
		self.activity_dto = activity_dto
		# list of AP.NodeList:
		self.nodelist = nodelist
		# list of DBH.RecordDataDTO:
		self.records = recordlist
		self.full_activity = AP.Split(self.nodelist)
		self.splits = []

		self.xs = []
		self.ys = []
		self.colors = []

	def _init_data(self):
		# reset data to be sure:
		self.xs = []
		self.ys = []
		self.colors = []
		
		# construct splits:
		self.splits = AP.construct_splits(self.nodelist, self.pso.split_type, self.pso.split_size)
		## todo: init colormanger depending on splits... also splits from other activities need to be considered.


	def construct_plotpoints(self, pso:PlotSpecificationObject, cm:CM.ColorManager):
		# given PlotSpecificationObject and ColorManager, construct x, y and colors for plotting
		self._init_data()

		# construct x,y,colors
		if self.pso.split_aggregates:
			# one datapoint per split:
			for split in self.splits:
				self.xs.append(getattr(split, self.pso.key_x))
				self.ys.append(getattr(split, self.pso.key_y))
				self.colors.append(cm.get_color_by_split(split))
		else:
			# one datapoint per node:
			for split in self.splits:
				for node in split.nodelist:
					self.xs.append(getattr(node, self.pso.key_x))
					self.ys.append(getattr(node, self.pso.key_y))
					self.colors.append(cm.get_color_by_split(split))

	def construct_routepoints(self, pso:PlotSpecificationObject, mso:MapSpecificationObject, cm:CM.ColorManager):
		# given PlotSpecificationObject, MapSpecificationObject and ColorManager, construct x, y and colors for plotting
		self._init_data()

		## todo: compute x,y image coordinates from lat/lon data


class ActivityPlotter(SubTask):
	def __init__(self, activities:list, pso:PlotSpecificationObject, mso:MapSpecificationObject=None):
		self.activities = activities
		self.pso = pso
		self.mso = mso
		self.cm = CM.ColorManager(pso.key_color, [act.activity_dto for act in self.activities])

		self.figure = None
		self.axes = None
		self.plottype = None
		self.min_x = None
		self.max_x = None
		self.min_y = None
		self.max_y = None
		super().__init__("ActivityPlotter", 3+len(self.activities)//10)

	def construct_plotname(self, suffix:str) -> str:
		return self.pso.name_base+suffix

	def _setup_plot(self):
		if self.pso.key_x in DATA_KEYS_CATEGORICAL or self.pso.key_y in DATA_KEYS_CATEGORICAL:
			self.plottype = "scatterplot"
		else:
			self.plottype = "lineplot"

	def _construct_plotdata(self):
		for activity in self.activities:
			activity.construct_plotpoints(self.pso, self.cm)

		self.min_x = min([min(activity.xs) for activity in self.activities])
		self.max_x = max([max(activity.xs) for activity in self.activities])

		self.min_y = min([min(activity.ys) for activity in self.activities])
		self.max_y = max([max(activity.ys) for activity in self.activities])

	def _construct_plotpoints(self):
		for activity in self.activities:
			activity.construct_routepoints(self.pso, self.mso, self.cm)

	def _setup_plot_axes(self):
		if KEY_RANGE_MIN[self.pso.key_x] is not None:
			axis_min_x = max(self.min_x, KEY_RANGE_MIN[self.pso.key_x])
		if KEY_RANGE_MAX[self.pso.key_x] is not None:
			axis_max_x = min(self.max_x, KEY_RANGE_MAX[self.pso.key_x])
		axis_diff_x = axis_max_x-axis_min_x
		if axis_diff_x > 0:
			xtickrange = np.arange(axis_min_x, axis_max_x+(axis_diff_x/10), axis_diff_x/10)
		else:
			xtickrange = [axis_min_x]
		xticklabels = [format_data(self.pso.key_x, x) for x in xtickrange]
		
		self.diff_y = self.max_y-self.min_y
		
		if KEY_RANGE_MIN[self.pso.key_y] is not None:
			axis_min_y = max(self.min_y, KEY_RANGE_MIN[self.pso.key_y])
		if KEY_RANGE_MAX[self.pso.key_y] is not None:
			axis_max_y = min(self.max_y, KEY_RANGE_MAX[self.pso.key_y])
		axis_diff_y = axis_max_y - axis_min_y
		if axis_diff_y > 0:
			ytickrange = np.arange(axis_min_y, axis_max_y+axis_diff_y/10, axis_diff_y/10)
		else:
			ytickrange = [axis_min_y]
		yticklabels = [format_data(self.pso.key_y, y) for y in ytickrange]

		self.axes.set_xlim(axis_min_x-(axis_x_diff/20), axis_max_x+(axis_x_diff/20))
		self.axes.set_ylim(axis_min_y-(axis_y_diff/20), axis_max_y+(axis_y_diff/20))
		self.axes.set_xticks(xtickrange, xticklabels, rotation=20)
		self.axes.set_yticks(ytickrange, yticklabels)
		self.axes.set_xlabel(self.pso.key_x + " ("+KEY_UNITS[self.pso.key_x]+")")
		self.axes.set_ylabel(self.pso.key_y + " ("+KEY_UNITS[self.pso.key_y]+")")

	def _setup_colorbar(self):
		cmmap_norm = mpl.colors.Normalize(vmin=self.cm.min_value.toordinal(), vmax=self.cm.max_value.toordinal())
		cmap = mpl.colormaps[self.cm.colormap_name]
		sm = mpl.cm.ScalarMappable(norm=cmmap_norm, cmap=cmap)
		cbar = plt.colorbar(sm, ax=self.axes, orientation='horizontal', pad=0.1, aspect=30)
		color_ticks, color_tick_labels = self.cm.get_color_legend_data()
		cbar.set_label(self.pso.key_color)
		cbar.set_ticks(color_ticks)
		cbar.set_ticklabels(color_tick_labels)

	def plot_data(self):
		# plot graph
		self._construct_plotdata()

		#self.figure, self.axes = plt.subplots(figsize=(self.width_inches, self.height_inches), dpi=self.dpi)

		for i in range(len(self.activities)):
			if i%10 == 0:
				self.progress += 1
		self.finish_progress()
		
	def plot_routes(self):
		# plot routes on map
		self._construct_plotpoints()

		for i in range(len(self.activities)):
			if i%10 == 0:
				self.progress += 1
		self.finish_progress()

	def animate_routes(self):
		# create animation of routes on map
		self._construct_plotpoints()

		for i in range(len(self.activities)):
			if i%10 == 0:
				self.progress += 1
		self.finish_progress()