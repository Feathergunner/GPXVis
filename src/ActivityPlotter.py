#!usr/bin/python
# -*- coding: utf-8 -*-import string

import os
import numpy as np
import matplotlib as mpl
from matplotlib import pyplot as plt
from matplotlib.collections import LineCollection
from datetime import datetime

from src.SubTask import SubTask
from src import ColorManager as CM
from src import ActivityPath as AP
from src import DatabaseHandler as DBH
from src.misc import ensure_dir_exists, ensure_unique_filename
#
#from src.misc import load_gpx_file, parse_gps_from_gpx, get_timestamp_in_seconds, format_time, format_time_hours, float_to_pace_str
#from org import GPX_DIR, GPX_DIR_TEST, METER_PER_DEG_LAT, METER_PER_DEG_LON
from src.org_plotting import LINECOLORS, DATA_KEYS_CATEGORICAL, PLOT_WIDTH, PLOT_HEIGHT, PLOT_DPI, COLOR_KEYS_CONTINUOUS


class SpecificationObject():
	'''
	Base clsas for PlotSpecificationObject and MapSpecificationObject
	'''
	def __init__(self,
			key_color:str="singular",
			split_type:str="length",
			split_size:int=1000,
			records_highlight:bool=False,
			records_only:bool=False,
			name_base:str=""):
		# attribute that defines the color of the plot:
		self.key_color = key_color

		# dimension that is used to define splits:
		self.split_type = split_type
		# has to be one of Split.VALID_SPLIT_DIMENSIONS
		# split size in specified dimension:
		self.split_size = split_size

		# how do visualize records:
		self.records_highlight = records_highlight
		# if records_highlight == True, record segments are highlighted in the plot
		self.records_only = records_only
		# if records_only == True, only record segments are plotted

		self.name_base = name_base


class PlotSpecificationObject(SpecificationObject):
	def __init__(self,
			key_x:str,
			key_y:str,
			key_color:str="singular",
			split_type:str="length",
			split_size:int=1000,
			activity_aggregates:bool=False,
			split_aggregates:bool=False,
			records_highlight:bool=False,
			records_only:bool=False,
			name_base:str=""):
		super().__init__(key_color, split_type, split_size, records_highlight, records_only, name_base)
		self.key_x = key_x
		self.key_y = key_y
		
		self.activity_aggregates = activity_aggregates
		# if true, plot will contain only one datapoint for each activity
		# if false, the parameter split_aggregates defines the plot type

		self.split_aggregates = split_aggregates
		# if true, plot will contain only one datapoint for each split
		#	e.g. for all kinds of plots of aggregated data
		# if false, splits are used for coloring only,
		#	e.g. for elevation profile, mapped routes, etc.

		if self.activity_aggregates or self.split_aggregates:
			self.records_highlight = False
			self.records_only = False
		# if activity_aggregates or split_aggregates is set True, only aggregated split data is plotted,
		# so highlighting records is not possible
		# plotting only record data is not supported in this mode.

		## todo: verify that key_x and key_y correspond to the plot type as specified by activity_aggregates and split_aggregates
		## alterntively, set activity_aggregates and split_aggregates based on key_x and key_y?
		

class MapSpecificationObject(SpecificationObject):
	def __init__(self,
			dim_x:int,
			dim_y:int,
			latitude_min:float,
			longitude_min:float,
			detaillevel:int,
			key_color:str="singular",
			split_type:str="length",
			split_size:int=1000,
			records_highlight:bool=False,
			records_only:bool=False,
			name_base:str=""):
		super().__init__(key_color, split_type, split_size, records_highlight, records_only, name_base)
		# map image size in pixel:
		self.dim_x = dim_x
		self.dim_y = dim_y

		# map parameters:
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
	def __init__(self, activity_dto:DBH.ActivityDTO, nodelist:list, recordlist:list=[]):
		self.activity_dto = activity_dto
		# list of AP.NodeList:
		self.nodelist = nodelist
		# list of DBH.RecordDataDTO:
		self.records = recordlist

		# aggregated ativity data:
		self.full_activity = None
		# activity splits:
		self.splits = []

		# plot points:
		self.xs = []
		self.ys = []
		self.colors = []

	def init_splits(self, split_type, split_size):		
		# construct splits:
		self.full_activity = AP.Split(self.nodelist)
		self.splits = AP.construct_splits(self.nodelist, split_type, split_size)

	def _get_color_for_split(self, split:AP.Split, pso:PlotSpecificationObject, cm:CM.ColorManager):
		if pso.key_color.key in DATA_KEYS_CATEGORICAL:
			return cm.get_color_by_activity(self.activity_dto)
		else:
			return cm.get_color_by_split(split)

	def construct_plotpoints(self, pso:PlotSpecificationObject, cm:CM.ColorManager):
		# given PlotSpecificationObject and ColorManager, construct x, y and colors for plotting
		# reset data to be sure:
		self.xs = []
		self.ys = []
		self.colors = []

		if pso.activity_aggregates:
			# one datapoint per activity
			# SCATTERPLOT:
			self.xs.append(getattr(self.full_activity, pso.key_x.key))
			self.ys.append(getattr(self.full_activity, pso.key_y.key))
			self.colors.append(cm.get_color_by_activity(self.activity_dto))

		elif pso.split_aggregates:
			# one datapoint per split
			# SCATTERPLOT:
			for split in self.splits:
				self.xs.append(getattr(split, pso.key_x.key))
				self.ys.append(getattr(split, pso.key_y.key))
				self.colors.append(self._get_color_for_split(split, pso, cm))
		else:
			# one datapoint per node
			# LINEPLOT
			if pso.records_only:
				## todo: plot only records
				for record in self.recordlist:
					continue
			else:
				for split in self.splits:
					self.xs.append(np.asarray([getattr(node, pso.key_x.key) for node in split.nodelist]))
					self.ys.append(np.asarray([getattr(node, pso.key_y.key) for node in split.nodelist]))
					if pso.records_highlight:
						## todo: set highlight color for nodes within record segments:
						## and linewidth(?)
						self.colors.append(self._get_color_for_split(split, pso, cm))
					else:
						self.colors.append(self._get_color_for_split(split, pso, cm))
		#print ("activity colors:", self.colors)

	def construct_routepoints(self, mso:MapSpecificationObject, cm:CM.ColorManager):
		# given MapSpecificationObject and ColorManager, construct x, y and colors for plotting
		self._init_data(mso.split_type, mso.split_size)

		## todo: compute x,y image coordinates from lat/lon data

		if mso.records_only:
			## todo
			pass
		else:
			## todo
			if mso.records_highlight:
				## todo
				pass


class ActivityPlotter(SubTask):
	def __init__(self, activities:list):
		self.activities = activities

		self.cm = None
		self.figure = None
		self.axes = None
		self.plottype = None
		self.min_x = None
		self.max_x = None
		self.min_y = None
		self.max_y = None
		super().__init__("ActivityPlotter", 3+len(self.activities)//10)

	def _construct_plotname(self, so, suffix:str) -> str:
		plotname = so.name_base
		if len(suffix) > 0:
			plotname += "_"+suffix
		return plotname

	def _setup_colorbar(self, so:SpecificationObject):
		self.cm = CM.ColorManager(self, so)
		cmmap_norm = mpl.colors.Normalize(vmin=self.cm.min_value, vmax=self.cm.max_value)
		cmap = mpl.colormaps[self.cm.colormap_name]
		sm = mpl.cm.ScalarMappable(norm=cmmap_norm, cmap=cmap)
		cbar = plt.colorbar(sm, ax=self.axes, orientation='horizontal', pad=0.1, aspect=30)
		color_ticks, color_tick_labels = self.cm.get_color_legend_data()
		cbar.set_label(so.key_color.label)
		cbar.set_ticks(color_ticks)
		cbar.set_ticklabels(color_tick_labels)


class ActivityDataPlotter(ActivityPlotter):
	def __init__(self, activities:list, pso:PlotSpecificationObject):
		self.activities = activities
		self.pso = pso
		super().__init__(activities)

		for activity in self.activities:
			activity.init_splits(self.pso.split_type, self.pso.split_size)

	def _construct_plotname(self, suffix:str) -> str:
		plotname = super()._construct_plotname(self.pso, suffix)
		plotname += "_"+self.pso.key_x.label+"_"+self.pso.key_y.label
		return plotname

	def _setup_plot(self):
		if self.pso.key_x in DATA_KEYS_CATEGORICAL or self.pso.key_y in DATA_KEYS_CATEGORICAL:
			self.plottype = "scatterplot"
		else:
			self.plottype = "lineplot"

	def _construct_plotdata(self):
		for activity in self.activities:
			activity.construct_plotpoints(self.pso, self.cm)

		if self.plottype == "scatterplot":
			self.min_x = min([min(activity.xs) for activity in self.activities])
			self.max_x = max([max(activity.xs) for activity in self.activities])
			self.min_y = min([min(activity.ys) for activity in self.activities])
			self.max_y = max([max(activity.ys) for activity in self.activities])
		else:
			self.min_x = min([min([min(split) for split in activity.xs]) for activity in self.activities])
			self.max_x = max([max([max(split) for split in activity.xs]) for activity in self.activities])
			self.min_y = min([min([min(split) for split in activity.ys]) for activity in self.activities])
			self.max_y = max([max([max(split) for split in activity.ys]) for activity in self.activities])


	def _setup_plot_axes(self):
		if self.pso.key_x.range_min is not None:
			axis_min_x = max(self.min_x, self.pso.key_x.range_min)
		else:
			axis_min_x = self.min_x
		if self.pso.key_x.range_max is not None:
			axis_max_x = min(self.max_x, self.pso.key_x.range_max)
		else:
			axis_max_x = self.max_x
		axis_diff_x = axis_max_x-axis_min_x
		if axis_diff_x > 0:
			xtickrange = np.arange(axis_min_x, axis_max_x+(axis_diff_x/10), axis_diff_x/10)
		else:
			xtickrange = [axis_min_x]
		xticklabels = [self.pso.key_x.format(x) for x in xtickrange]
		
		self.diff_y = self.max_y-self.min_y
		
		if self.pso.key_y.range_min is not None:
			axis_min_y = max(self.min_y, self.pso.key_y.range_min)
		else:
			axis_min_y = self.min_y
		if self.pso.key_y.range_max is not None:
			axis_max_y = min(self.max_y, self.pso.key_y.range_max)
		else:
			axis_max_y = self.max_y
		axis_diff_y = axis_max_y - axis_min_y
		if axis_diff_y > 0:
			ytickrange = np.arange(axis_min_y, axis_max_y+axis_diff_y/10, axis_diff_y/10)
		else:
			ytickrange = [axis_min_y]
		yticklabels = [self.pso.key_y.format(y) for y in ytickrange]

		self.axes.set_xlim(axis_min_x-(axis_diff_x/20), axis_max_x+(axis_diff_x/20))
		self.axes.set_ylim(axis_min_y-(axis_diff_y/20), axis_max_y+(axis_diff_y/20))
		self.axes.set_xticks(xtickrange, xticklabels, rotation=20)
		self.axes.set_yticks(ytickrange, yticklabels)
		self.axes.set_xlabel(self.pso.key_x.label + " ("+self.pso.key_x.unit+")")
		self.axes.set_ylabel(self.pso.key_y.label + " ("+self.pso.key_y.unit+")")

	def plot_data(self, filenamesuffix:str=""):
		# init plot:
		self.figure, self.axes = plt.subplots(figsize=(PLOT_WIDTH, PLOT_HEIGHT), dpi=PLOT_DPI)
		self._setup_colorbar(self.pso)
		self._construct_plotdata()
		self._setup_plot()
		self._setup_plot_axes()

		# plot data:
		for i in range(len(self.activities)):
			if self.plottype == "lineplot":
				segments = []
				for j in range(len(self.activities[i].splits)):
					points = np.asarray([[self.activities[i].xs[j][k], self.activities[i].ys[j][k]] for k in range(len(self.activities[i].xs[j]))])
					#print (points)
					segments.append(points)
				self.axes.add_collection(LineCollection(segments, colors=[self.activities[i].colors[j] for j in range(len(self.activities[i].splits))]))
				#self.axes.plot(self.activities[i].xs, self.activities[i].ys, color=self.activities[i].colors)
			elif self.plottype == "scatterplot":
				self.axes.scatter(self.activities[i].xs, self.activities[i].ys, color=self.activities[i].colors)
			if (i>0 and i%10 == 0):
				self.progress += 1

		# save plot:
		outputfolder = os.path.join("output", "activities")
		ensure_dir_exists(outputfolder)
		result_filename = self._construct_plotname(filenamesuffix)
		outputpath = os.path.join(outputfolder, ensure_unique_filename(outputfolder, result_filename)+".png")
		self.figure.savefig(outputpath, bbox_inches='tight', pad_inches=0.2, dpi=PLOT_DPI)
		plt.close('all')
		self.finish_progress()
		return outputpath

class ActivityMapPlotter(ActivityPlotter):
	def __init__(self, activities:list, mso:MapSpecificationObject):
		self.activities = activities
		self.mso = mso
		super().__init__(activities, mso)
	
	def _construct_routepoints(self):
		for activity in self.activities:
			activity.construct_routepoints(self.mso, self.cm)

	def plot_routes(self):
		# plot routes on map
		self._construct_routepoints()

		if self.mso.key_color in COLOR_KEYS_CONTINUOUS:
			self._setup_colorbar()

		for i in range(len(self.activities)):
			if i%10 == 0:
				self.progress += 1
		self.finish_progress()

	def animate_routes(self):
		# create animation of routes on map
		self._construct_routepoints()

		if self.mso.key_color in COLOR_KEYS_CONTINUOUS:
			self._setup_colorbar()

		for i in range(len(self.activities)):
			if i%10 == 0:
				self.progress += 1
		self.finish_progress()