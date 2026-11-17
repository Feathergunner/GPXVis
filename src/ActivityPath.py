#!usr/bin/python
# -*- coding: utf-8 -*-import string

import gpxpy
import datetime

from src.misc_geometry import get_latlon_vector_length
from src import DatabaseHandler as DBH

class PathNode():
	'''
	Class to represent nodes data with activity metadata
	'''
	n = 0
	def __init__(self, gpxpoint, previous_node=None):
		'''
		Constructs a graph node from a gpx point (as parsed by gpxpy)
		'''
		self.id = PathNode.n
		PathNode.n += 1
		self.latitude = gpxpoint.latitude
		self.longitude = gpxpoint.longitude
		self.elevation = gpxpoint.elevation
		if previous_node is not None:
			self.length = get_latlon_vector_length(self.latitude-previous_node.latitude, self.longitude-previous_node.longitude)
			self.delta_elevation = self.elevation-previous_node.elevation
		else:
			self.length = 0
			self.delta_elevation = 0

	def __str__(self):
		return "Node at position:("+str(self.latitude)+","+str(self.longitude)+"), elevation: "+str(self.elevation)

	def __repr__(self):
		return str(self)

	def get_position(self):
		return (self.get_longitude(), self.get_latitude())


class ActivityNode(PathNode):
	def __init__(self, gpxpoint, previous_node=None):
		super().__init__(gpxpoint, previous_node)
		self.timestamp = gpxpoint.time
		if previous_node is not None:
			self.delta_time = self.timestamp - previous_node.timestamp
		else:
			self.delta_time = datetime.timedelta(0)
		self.heartrate = None
		self.cadence = None
		for extension in gpxpoint.extensions:
			tag = extension.tag.split('}')[-1]
			if tag in ["hr", "heartrate", "heart_rate"]:
				self.heartrate = int(extension.text)
			elif tag in ["cad", "cadence"]:
				self.cadence = int(extension.text)

def construct_pathnodes(gpxdata:str, start_gpx_index:int=0) -> list:
	# constructs a list of ActivityNodes from parsed gpx file
	# gpxdata: data as returned by gpxpy.parse(), i.e.
	#	gpxdata = gpxpy.parse(open(self.activity.filepath, 'r'))
	# start_index: first valid datapoint in first segment of first track in gpxdata
	previous_node = None
	nodelist = []
	for track in gpxdata.tracks:
		for s_i in range(len(track.segments)):
			segment = track.segments[s_i]
			if (s_i == 0):
				start_index = start_gpx_index
			else:
				start_index = 0
			for p_i in range(start_index, len(segment.points)):
				new_node = ActivityNode(segment.points[p_i], previous_node)
				nodelist.append(new_node)
				previous_node = new_node
	return nodelist