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

class Activity():
	'''
	This class contains all relevant data about a single activity:
	- the metadata and aggregated statistics, as far as they are stored in the database
	- the list of nodes as parsed from the gpx-file
	- the list of records

	Contains functionalities to construct a plot, given a PlotSpecificationObject
	'''
	def __init__(self, activity:DBH.ActivityDTO, nodelist:list, recordlist:list):
		self.activity = activity
		# list of AP.NodeList:
		self.nodelist = nodelist
		# list of DBH.RecordDataDTO:
		self.records = recordlist
		self.full_activity = AP.Split(self.nodelist)
		self.splits = []

		self.xs = []
		self.ys = []
		self.colors = []

	def construct_plotpoints(self, pso:PlotSpecificationObject, cm:CM.ColorManager):
		# given PlotSpecificationObject and ColorManager, construct x, y and colors for plotting
		# reset data to be sure:
		self.xs = []
		self.ys = []
		self.colors = []
		
		# construct splits:
		self.splits = AP.construct_splits(self.nodelist, self.pso.split_type, self.pso.split_size)
		## todo: init colormanger depending on splits... also splits from other activities need to be considered.

		# construct x,y,colors
		## todo: needs correct conversion of latitude and longitude into x,y image dimensions
		if self.pso.split_only:
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


class PlotSpecificationObject():
	def __init__(self,
			key_x:str,
			key_y:str,
			key_color:str="singular",
			split_type:str="length",
			split_size:int=1000,
			split_only:False,
			name_base:str=""):
		self.key_x = key_x
		self.key_y = key_y
		self.key_color = key_color

		# dimension that is used to define splits
		# has to be one of Split.VALID_SPLIT_DIMENSIONS
		self.split_type = split_type
		# split size in specified dimension
		self.split_size = split_size
		# if true, plot will contain only one datapoint for each split
		#	e.g. for all kinds of plots of aggregated data
		# if false, splits are used for coloring only,
		#	e.g. for elevation profile, mapped routes, etc.
		self.split_only = split_only

		self.name_base = name_base


class ActivityPlotter(SubTask):
	def __init__(self, activities:list, pso:PlotSpecificationObject):
		self.activities = activities
		self.pso = pso

		self.figure = None
		self.axes = None
		self.plottype = None
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
			activity.construct_plotpoints(self.pso)

	def plot_data(self):
		# plot graph

		#self.figure, self.axes = plt.subplots(figsize=(self.width_inches, self.height_inches), dpi=self.dpi)
		#colormanager = CM.ColorManager(color_axis_key, self.activities)

		pass

	def plot_routes(self):
		# plot routes on map
		pass

	def animate_routes(self):
		# create animation of routes on map
		pass