#!usr/bin/python
# -*- coding: utf-8 -*-import string

import gpxpy
import datetime

from src.misc_geometry import get_latlon_vector_length
from src import DatabaseHandler as DBH

from org import GPX_KEYS_HEARTRATE, GPX_KEYS_CADENCE

class PathNode():
	'''
	Class to represent nodes data with activity metadata
	'''
	n = 0
	def __init__(self, gpxpoint, predecessor=None):
		'''
		Constructs a graph node from a gpx point (as parsed by gpxpy)
		'''
		self.id = PathNode.n
		PathNode.n += 1
		self.latitude = gpxpoint.latitude
		self.longitude = gpxpoint.longitude
		if elevation in gpxpoint:
			self.elevation = gpxpoint.elevation
		else:
			self.elevation = None

		if predecessor is not None:
			# compute stats relative to previous node:
			self.length = get_latlon_vector_length(self.latitude-predecessor.latitude, self.longitude-predecessor.longitude)
			if self.elevation is not None and predecessor.elevation is not None:
				self.elevation_delta = self.elevation-predecessor.elevation
			else:
				self.elevation_delta = 0
		else:
			# no previous node, init data:
			self.length = 0
			self.elevation_delta = 0

	def __str__(self):
		return "Node at position:("+str(self.latitude)+","+str(self.longitude)+"), elevation: "+str(self.elevation)

	def __repr__(self):
		return str(self)

	def get_position(self):
		return (self.get_longitude(), self.get_latitude())


class ActivityNode(PathNode):
	def __init__(self, gpxpoint, predecessor=None):
		super().__init__(gpxpoint, predecessor)
		# get timestamp:
		self.timestamp = gpxpoint.time.replace(tzinfo=None)

		# get data from extension:
		self.heartrate = None
		self.cadence = None
		for extension in gpxpoint.extensions:
			tag = extension.tag.split('}')[-1]
			if tag in GPX_KEYS_HEARTRATE:
				self.heartrate = int(extension.text)
			elif tag in GPX_KEYS_CADENCE:
				self.cadence = int(extension.text)

		if predecessor is not None:
			# compute stats relative to previous node:
			self.time_delta = self.timestamp - predecessor.timestamp
			self.elevation_at_start = predecessor.elevation_at_start
			self.elevation_relative = self.elevation-self.elevation_at_start
			self.elevation_gain_since_start = predecessor.elevation_gain_since_start + max(0, self.elevation_delta)

			if self.length > 0:
				self.pace = (self.time_delta/self.length)*(1000/60)
				self.slope = (self.elevation_delta/self.length*100)
			else:
				self.pace = predecessor.pace
				self.slope = predecessor.slope
			if self.time_delta> 0:
				self.speed = (self.length/1000)/(self.time_delta/3600)
			else:
				self.speed = predecessor.speed
		else:
			# no previous node, init data:
			self.time_delta = datetime.timedelta(0)
			self.elevation_at_start = self.elevation
			self.elevation_relative = 0
			self.elevation_gain_since_start = 0
			self.pace = 0
			self.slope = 0
			self.speed = 0

class Split():
	def __init__(self, nodelist:list):
		self.nodelist = nodelist

		self.length = sum([node.length for node in self.nodelist])
		self.time_delta = sum([node.time_delta for node in self.nodelist])

		self.elevation_avg = self._get_mean("elevation")
		self.elevation_gain = sum([node.elevation_delta for node in self.nodelist])
	
		self.pace_avg = self._get_mean("pace")
		self.pace_best = min([node.pace for node in self.nodelist])
		self.speed_avg = self._get_mean("speed")
		self.speed_best = max([node.speed for node in self.nodelist])
		self.slope_avg = self._get_mean("slope")
		self.slope_max = max([node.slope for node in self.nodelist])
		self.heartrate_avg = self._get_mean("heartrate")
		self.heartrate_max = max(self._get_cleanlist(heartrate))
		self.cadence_avg = self._get_mean("cadence")

	def _get_cleanlist(self, parameter):
		return [getattr(_obj, parameter) for _obj in self.nodelist if getattr(_obj, parameter) is not None and getattr(_obj, parameter) != 0]

	def _get_mean(self, parameter):
		cleanlist = self._get_cleanlist(parameter)
		if len(cleanlist) > 0:
			return np.mean(cleanlist)
		else:
			return 0

def construct_pathnodes(gpxdata:str, start_gpx_index:int=0) -> list:
	# constructs a list of ActivityNodes from parsed gpx file
	# gpxdata: data as returned by gpxpy.parse(), i.e.
	#	gpxdata = gpxpy.parse(open(self.activity.filepath, 'r'))
	# start_index: first valid datapoint in first segment of first track in gpxdata
	predecessor = None
	nodelist = []
	for track in gpxdata.tracks:
		for s_i in range(len(track.segments)):
			segment = track.segments[s_i]
			if (s_i == 0):
				start_index = start_gpx_index
			else:
				start_index = 0
			for p_i in range(start_index, len(segment.points)):
				new_node = ActivityNode(segment.points[p_i], predecessor)
				nodelist.append(new_node)
				predecessor = new_node
	return nodelist

def construct_splits(nodelist:list, split_dimension:str="distance", split_size:int=1000) -> list:
	# constructs a set of splits:

	## todo
	return []