#!usr/bin/python
# -*- coding: utf-8 -*-import string

from enum import Enum
import datetime

from src.misc import format_time_hours, float_to_pace_str

class AxisDataSource(Enum):
	PATHNODE = 1
	SPLIT = 2
	ACTIVITY = 3
	ACTIVITY_DTO = 4

class AxisSpecs():
	n = 0
	def __init__(self,
			key:str,
			label:str,
			unit:str,
			format,
			datasource:AxisDataSource,
			range_min		= None,
			range_max		= None,
			spacial_cont	= False,
			spacial_cat		= False,
			color_cont		= False,
			color_cat		= False):
		self.id = AxisSpecs.n
		AxisSpecs.n += 1

		self.key = key
		self.label = label
		self.unit = unit
		self.format = format
		self.range_min = range_min
		self.range_max = range_max
		self.datasource = datasource
		if spacial_cat and spacial_cont:
			raise Exception("Spacial key cannot be both categorical and continuous!")
		self.spacial_cont = spacial_cont
		self.spacial_cat = spacial_cat
		if color_cat and color_cont:
			raise Exception("Color key cannot be both categorical and continuous!")
		self.color_cont = color_cont
		self.color_cat = color_cat

	def __str__(self):
		retstr = ""
		for key in self.to_dict():
			retstr += key+": "+str(self.to_dict()[key])+"\n"
		retstr += "datasource: "+str(self.datasource)
		return retstr

	def get_label_with_unit(self):
		if self.unit == "":
			return self.label
		else:
			return self.label+" ("+self.unit+")"

	def to_dict(self):
		'''
		to pass AxisSpecs to javascript frontend
		'''
		return {
			"id" : self.id,
			"label" : self.label,
			"unit" : self.unit,
			"spacial_cat" : self.spacial_cat,
			"spacial_cont" : self.spacial_cont,
			"color_cat" : self.color_cat,
			"color_cont" : self.color_cont
		}

###########################################################
### Node keys:
###########################################################

AXIS_DISTANCE_NODE = AxisSpecs(
	"distance_since_start",
	"distance",
	"km",
	lambda val: f"{val/1000:03.1f}",
	datasource = AxisDataSource.PATHNODE,
	range_min = 0,
	spacial_cont = True,
	color_cont = True)

AXIS_TIME_NODE = AxisSpecs(
	"time_since_start",
	"time since activity start",
	"h:min:sec",
	format_time_hours,
	datasource = AxisDataSource.PATHNODE,
	range_min = 0,
	spacial_cont = True,
	color_cont = True)

AXIS_ELEVATION_NODE = AxisSpecs(
	"elevation",
	"elevation",
	"m",
	lambda val: f"{val:.0f}",
	datasource = AxisDataSource.PATHNODE,
	spacial_cont = True,
	color_cont = True)

AXIS_ELEVATIONREL_NODE = AxisSpecs(
	"elevation_relative",
	"elevation relative to start",
	"m",
	lambda val: f"{val:.0f}",
	datasource = AxisDataSource.PATHNODE,
	spacial_cont = True,
	color_cont = True)

AXIS_ELEVATIONGAIN_NODE = AxisSpecs(
	"elevation_gain_since_start",
	"elevation gain",
	"m",
	lambda val: f"{val:.0f}",
	datasource = AxisDataSource.PATHNODE,
	range_min = 0,
	spacial_cont = True,
	color_cont = True)

AXIS_SLOPE_NODE = AxisSpecs(
	"slope",
	"slope",
	"%",
	lambda val: f"{val:2.0f}%",
	datasource = AxisDataSource.PATHNODE,
	range_min = -50,
	range_max = 50,
	spacial_cont = True,
	color_cont = True)

AXIS_PACE_NODE = AxisSpecs(
	"pace",
	"pace",
	"min/km",
	float_to_pace_str,
	datasource = AxisDataSource.PATHNODE,
	range_min = 2,
	range_max = 30,
	spacial_cont = True,
	color_cont = True)

AXIS_SPEED_NODE = AxisSpecs(
	"speed",
	"speed",
	"km/h",
	lambda val: f"{val:.1f}",
	datasource = AxisDataSource.PATHNODE,
	range_min = 2,
	range_max = 30,
	spacial_cont = True,
	color_cont = True)

AXIS_HEARTRATE_NODE = AxisSpecs(
	"heartrate",
	"heartrate",
	"bpm",
	lambda val: f"{val:.0f}",
	datasource = AxisDataSource.PATHNODE,
	range_min = 40,
	range_max = 250,
	spacial_cont = True,
	color_cont = True)

AXIS_CADENCE_NODE = AxisSpecs(
	"cadence",
	"cadence",
	"spm",
	lambda val: f"{val:.0f}",
	datasource = AxisDataSource.PATHNODE,
	range_min = 0,
	spacial_cont = True,
	color_cont = True)

###########################################################
### Split keys:
###########################################################

AXIS_DISTANCE_SPLIT = AxisSpecs(
	"distance_since_start",
	"distance since activity start",
	"km",
	lambda val: f"{val/1000:03.1f}",
	datasource = AxisDataSource.SPLIT,
	range_min = 0,
	spacial_cat = True,
	color_cont = True)

AXIS_LENGTH_SPLIT = AxisSpecs(
	"length",
	"length",
	"m",
	lambda val: f"{val:03.0f}",
	datasource = AxisDataSource.SPLIT,
	range_min = 0,
	spacial_cat = True,
	color_cont = True)

AXIS_TIME_SPLIT = AxisSpecs(
	"time_since_start",
	"time since activity start",
	"h:min:sec",
	format_time_hours,
	datasource = AxisDataSource.SPLIT,
	range_min = 0,
	spacial_cat = True,
	color_cont = True)

AXIS_DURATION_SPLIT = AxisSpecs(
	"time_delta",
	"time",
	"h:min:sec",
	format_time_hours,
	datasource = AxisDataSource.SPLIT,
	range_min = 0,
	spacial_cat = True,
	color_cont = True)

AXIS_ELEVATIONGAIN_SPLIT = AxisSpecs(
	"elevation_gain",
	"elevation gain",
	"m",
	lambda val: f"{val:.0f}",
	datasource = AxisDataSource.SPLIT,
	range_min = 0,
	spacial_cat = True,
	color_cont = True)

AXIS_SLOPE_SPLIT = AxisSpecs(
	"slope",
	"average slope",
	"%",
	lambda val: f"{val:2.0f}%",
	datasource = AxisDataSource.SPLIT,
	range_min = -50,
	range_max = 50,
	spacial_cat = True,
	color_cont = True)

AXIS_PACE_SPLIT = AxisSpecs(
	"pace",
	"average pace",
	"min/km",
	float_to_pace_str,
	datasource = AxisDataSource.SPLIT,
	range_min = 2,
	range_max = 30,
	spacial_cat = True,
	color_cont = True)

AXIS_SPEED_SPLIT = AxisSpecs(
	"speed",
	"average speed",
	"km/h",
	lambda val: f"{val:.1f}",
	datasource = AxisDataSource.SPLIT,
	range_min = 2,
	range_max = 30,
	spacial_cat = True,
	color_cont = True)

AXIS_SLOPEMAX_SPLIT = AxisSpecs(
	"slope_max",
	"maximum slope",
	"%",
	lambda val: f"{val:2.0f}%",
	datasource = AxisDataSource.SPLIT,
	range_min = -50,
	range_max = 50,
	spacial_cat = True,
	color_cont = True)

AXIS_PACEMAX_SPLIT = AxisSpecs(
	"pace_best",
	"fastest pace",
	"min/km",
	float_to_pace_str,
	datasource = AxisDataSource.SPLIT,
	range_min = 2,
	range_max = 30,
	spacial_cat = True,
	color_cont = True)

AXIS_SPEEDMAX_SPLIT = AxisSpecs(
	"speed_best",
	"highest speed",
	"km/h",
	lambda val: f"{val:.1f}",
	datasource = AxisDataSource.SPLIT,
	range_min = 2,
	range_max = 30,
	spacial_cat = True,
	color_cont = True)

AXIS_HEARTRATE_SPLIT = AxisSpecs(
	"heartrate",
	"average heartrate",
	"bpm",
	lambda val: f"{val:.0f}",
	datasource = AxisDataSource.SPLIT,
	range_min = 40,
	range_max = 250,
	spacial_cat = True,
	color_cont = True)

AXIS_CADENCE_SPLIT = AxisSpecs(
	"cadence",
	"average cadence",
	"spm",
	lambda val: f"{val:.0f}",
	datasource = AxisDataSource.SPLIT,
	range_min = 0,
	spacial_cat = True,
	color_cont = True)

###########################################################
### Activity keys:
###########################################################

#############################
## Aggregated data:
#############################

AXIS_LENGTH_ACTIVITY = AxisSpecs(
	"length",
	"length",
	"m",
	lambda val: f"{val:03.0f}",
	datasource = AxisDataSource.ACTIVITY,
	range_min = 0,
	spacial_cat = True,
	color_cont = True)

AXIS_DURATION_ACTIVITY = AxisSpecs(
	"time_delta",
	"time",
	"h:min:sec",
	format_time_hours,
	datasource = AxisDataSource.ACTIVITY,
	range_min = 0,
	spacial_cat = True,
	color_cont = True)

AXIS_ELEVATIONGAIN_ACTIVITY = AxisSpecs(
	"elevation_gain",
	"elevation gain",
	"m",
	lambda val: f"{val:.0f}",
	datasource = AxisDataSource.ACTIVITY,
	range_min = 0,
	spacial_cat = True,
	color_cont = True)

AXIS_SLOPE_ACTIVITY = AxisSpecs(
	"slope",
	"average slope",
	"%",
	lambda val: f"{val:2.0f}%",
	datasource = AxisDataSource.ACTIVITY,
	range_min = -50,
	range_max = 50,
	spacial_cat = True,
	color_cont = True)

AXIS_PACE_ACTIVITY = AxisSpecs(
	"pace",
	"average pace",
	"min/km",
	float_to_pace_str,
	datasource = AxisDataSource.ACTIVITY,
	range_min = 2,
	range_max = 30,
	spacial_cat = True,
	color_cont = True)

AXIS_SPEED_ACTIVITY = AxisSpecs(
	"speed",
	"average speed",
	"km/h",
	lambda val: f"{val:.1f}",
	datasource = AxisDataSource.ACTIVITY,
	range_min = 2,
	range_max = 30,
	spacial_cat = True,
	color_cont = True)

AXIS_SLOPEMAX_ACTIVITY = AxisSpecs(
	"slope_max",
	"maximum slope",
	"%",
	lambda val: f"{val:2.0f}%",
	datasource = AxisDataSource.ACTIVITY,
	range_min = -50,
	range_max = 50,
	spacial_cat = True,
	color_cont = True)

AXIS_PACEMAX_ACTIVITY = AxisSpecs(
	"pace_best",
	"fastest pace",
	"min/km",
	float_to_pace_str,
	datasource = AxisDataSource.ACTIVITY,
	range_min = 2,
	range_max = 30,
	spacial_cat = True,
	color_cont = True)

AXIS_SPEEDMAX_ACTIVITY = AxisSpecs(
	"speed_best",
	"highest speed",
	"km/h",
	lambda val: f"{val:.1f}",
	datasource = AxisDataSource.ACTIVITY,
	range_min = 2,
	range_max = 30,
	spacial_cat = True,
	color_cont = True)

AXIS_HEARTRATE_ACTIVITY = AxisSpecs(
	"heartrate",
	"average heartrate",
	"bpm",
	lambda val: f"{val:.0f}",
	datasource = AxisDataSource.ACTIVITY,
	range_min = 40,
	range_max = 250,
	spacial_cat = True,
	color_cont = True)

AXIS_CADENCE_ACTIVITY = AxisSpecs(
	"cadence",
	"average cadence",
	"spm",
	lambda val: f"{val:.0f}",
	datasource = AxisDataSource.ACTIVITY,
	range_min = 0,
	spacial_cat = True,
	color_cont = True)

#############################
## Activity metadata:
#############################

AXIS_DATE = AxisSpecs(
	"datetime",
	"date",
	"YYYY-MM-DD",
	lambda val: val.date(),
	datasource = AxisDataSource.ACTIVITY_DTO,
	spacial_cat = True,
	color_cont = True)

AXIS_ATHLETE = AxisSpecs(
	"athlete_name",
	"athlete name",
	"",
	lambda val: val,
	datasource = AxisDataSource.ACTIVITY_DTO,
	spacial_cat = True,
	color_cat = True)

AXIS_ACTIVITYTYPE = AxisSpecs(
	"type_name",
	"activity type",
	"",
	lambda val: val,
	datasource = AxisDataSource.ACTIVITY_DTO,
	spacial_cat = True,
	color_cat = True)

AXIS_ACTIVITY = AxisSpecs(
	"id",
	"activity",
	"",
	lambda val: val,
	datasource = AxisDataSource.ACTIVITY_DTO,
	spacial_cat = True,
	color_cat = True)

#############################
## Special color modes:
#############################

# no color axis, everything in the same color:
AXIS_NOAXIS = AxisSpecs(
	"",
	"singular",
	"",
	lambda val: None,
	datasource = AxisDataSource.ACTIVITY_DTO,
	spacial_cat = True,
	color_cat = True)

###########################################################

ALL_AXES_LIST = [
	AXIS_DISTANCE_NODE,
	AXIS_TIME_NODE,
	AXIS_ELEVATION_NODE,
	AXIS_ELEVATIONREL_NODE,
	AXIS_ELEVATIONGAIN_NODE,
	AXIS_SLOPE_NODE,
	AXIS_PACE_NODE,
	AXIS_SPEED_NODE,
	AXIS_HEARTRATE_NODE,
	AXIS_CADENCE_NODE,
	
	#AXIS_DISTANCE_SPLIT,
	AXIS_LENGTH_SPLIT,
	#AXIS_TIME_SPLIT,
	AXIS_DURATION_SPLIT,
	AXIS_ELEVATIONGAIN_SPLIT,
	AXIS_SLOPE_SPLIT,
	AXIS_PACE_SPLIT,
	AXIS_SPEED_SPLIT,
	AXIS_SLOPEMAX_SPLIT,
	AXIS_PACEMAX_SPLIT,
	AXIS_SPEEDMAX_SPLIT,
	AXIS_HEARTRATE_SPLIT,
	AXIS_CADENCE_SPLIT,

	AXIS_LENGTH_ACTIVITY,
	AXIS_DURATION_ACTIVITY,
	AXIS_ELEVATIONGAIN_ACTIVITY,
	AXIS_SLOPE_ACTIVITY,
	AXIS_PACE_ACTIVITY,
	AXIS_SPEED_ACTIVITY,
	AXIS_SLOPEMAX_ACTIVITY,
	AXIS_PACEMAX_ACTIVITY,
	AXIS_SPEEDMAX_ACTIVITY,
	AXIS_HEARTRATE_ACTIVITY,
	AXIS_CADENCE_ACTIVITY,

	AXIS_DATE,
	AXIS_ATHLETE,
	AXIS_ACTIVITYTYPE,
	AXIS_ACTIVITY,
	AXIS_NOAXIS
]

ALL_AXES = {axisspec.id : axisspec for axisspec in ALL_AXES_LIST}
ALL_AXES_DICT = {axisspec.id : axisspec.to_dict() for axisspec in ALL_AXES_LIST}
TIME_AXES = [
	AXIS_TIME_NODE,
	AXIS_TIME_SPLIT,
	AXIS_DURATION_SPLIT,
	AXIS_DURATION_ACTIVITY#,AXIS_DATE
]