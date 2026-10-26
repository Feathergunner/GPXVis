#!usr/bin/python
# -*- coding: utf-8 -*-import string

import os
import math
import numpy as np
import datetime

from src import OSMMapDownloader as osmmd
from src.SubTask import SubTask
from src.RouteGraph import RouteGraphNode, BaseGraphEdge
from src.misc_geometry import get_latlon_vector_length, round_gps
from src.misc import ensure_dir_exists, load_gpx_file, parse_gps_from_gpx

class TourGraphEdge(BaseGraphEdge):
	# class to hold tour segment data (like average speed) to be used for plotting

	n = 0

	def __init__(self, node_a:RouteGraphNode, node_b:RouteGraphNode):
		self.id = TourGraphEdge.n
		TourGraphEdge.n += 1

		self.length = get_latlon_vector_length(node_a.get_latitude()-node_b.get_latitude(), node_a.get_longitude()-node_b.get_longitude())

		time_a = node_a.get_time()
		time_b = node_b.get_time()
		elevation_a = node_a.get_elevation()
		elevation_b = node_b.get_elevation()
		if elevation_a is None or elevation_b is None:
			elevation_a = 0
			elevation_b = 0
		if time_a is not None and time_b is not None:
			# use timestamp data to get correct edge orientation:
			if time_a < time_b:
				self.id_begin = node_a.id
				self.id_end = node_b.id
				self.duration = time_b - time_a
				self.elevation_change = elevation_b-elevation_a
			else:
				self.id_begin = node_b.id
				self.id_end = node_a.id
				self.duration = time_a - time_b
				self.elevation_change = elevation_a-elevation_b
		else:
			# assume node_a is first
			self.id_begin = node_a.id
			self.id_end = node_b.id
			self.duration = datetime.timedelta(0)
			self.elevation_change = elevation_b-elevation_a
		self.elevation_avg = (elevation_a + elevation_b)/2


class TourGraph():
	# class to construct a graoh for a single tour (in contrast to RouteGraph),
	# to plot tour with color-coded graph segments
	# or to create tour animation 

	def __init__(self, name:str=""):
		self.nodes = {}
		self.edges = []
		self.start_node_id = -1

		self.basename = name

	def number_of_nodes(self) -> int:
		return len(self.nodes.keys())

	def number_of_edges(self) -> int:
		return len(self.edges)

	def is_empty(self) -> bool:
		return self.number_of_nodes() == 0

	def add_node(self, node:RouteGraphNode):
		self.nodes[node.id]=node

	def get_node(self, node_id:int):
		return self.nodes[node_id]

	def add_egde(self, node_a:TourGraphEdge, node_b:TourGraphEdge):
		new_edge = TourGraphEdge(node_a, node_b)
		self.edges.append(new_edge)

	def construct_from_gpx(self, gpx_filename:str):
		(gpxdata, metadata) = load_gpx_file(gpx_filename)
		gpsdata = parse_gps_from_gpx(gpxdata)
		previous_node = None
		datapoint_dists = []

		for datapoint in gpsdata:
			# check lat/lon
			lat = datapoint["latitude"]
			lon = datapoint["longitude"]
			if lat is None or lon is None:
				continue
			if lat == 0 or lon == 0:
				continue
			
			# construct node:
			new_node = RouteGraphNode(datapoint)
			self.add_node(new_node)
			
			if previous_node is not None:
				# construct edge:
				self.add_egde(previous_node, new_node)
			previous_node = new_node

	def get_split_segments(self, splitdistance:int=None, splittime:int=None, offset:int=0):
		'''
		Returns a list of lists of edge-ids, where each list of edge-ids covers a split.
		
		If splitdistance is not None, this defines the length of a split in meters.
		Else if splittime is not None, this defines the length of a split in seconds.
			If both are None, splitdistance is set to 100 meters.

		offset: specifies how many datapoints in the beginning of the tour are skipped
		before the first segment starts (used to synchronize the segments multiple tours).
		'''

		print ("get split segments for tour",self.basename)
		if splitdistance is None and splittime is None:
			splitdistance = 100

		current_total_covered = 0
		if splitdistance is not None:
			next_split_end = splitdistance
			print ("  by distance:",splitdistance)
		else:
			next_split_end = splittime
			print ("  by time:",splittime)

		start_edge = offset

		# init list of splits:
		splits = []
		splits.append({
			"edge_ids" : [start_edge],
			"distance" : self.edges[start_edge].length,
			"time" : self.edges[start_edge].duration.total_seconds(),
			"speed" : self.edges[start_edge].length/self.edges[start_edge].duration.total_seconds(),
			"elevation_change" : self.edges[start_edge].elevation_change,
			"elevation_avg" : self.edges[start_edge].elevation_avg,
			"dist_total" : 0,
			"time_total" : 0
			})
		current_edge_id = start_edge+1
		while current_edge_id < self.number_of_edges():
			new_split_edges = []
			split_dist = 0
			split_time = 0
			split_elevation_change = 0
			split_sum_of_elevations = 0

			add_next_edge = True
			while (add_next_edge and current_edge_id < self.number_of_edges()):
				new_split_edges.append(current_edge_id)
				split_dist += self.edges[current_edge_id].length
				split_time += self.edges[current_edge_id].duration.total_seconds()
				split_elevation_change += self.edges[current_edge_id].elevation_change
				split_sum_of_elevations += self.edges[current_edge_id].elevation_avg

				current_edge_id += 1
				if splitdistance is not None:
					if current_total_covered + split_dist > next_split_end:
						add_next_edge = False
						current_total_covered += split_dist
						next_split_end += splitdistance
				elif current_total_covered + split_time > next_split_end:
					add_next_edge = False
					current_total_covered += split_time
					next_split_end += splittime
					
			new_split = {
				"edge_ids" : new_split_edges,
				"distance" : split_dist,
				"time" : split_time,
				"speed" : split_dist/split_time,
				"elevation_change" : split_elevation_change,
				"elevation_avg" : split_sum_of_elevations/len(new_split_edges),
				"dist_total" : splits[-1]["dist_total"] + split_dist,
				"time_total" : splits[-1]["time_total"] + split_time
				}
			splits.append(new_split)

		#print ("Constructed splits for tour",self.basename,":",len(splits))
		#print ("split sizes (edges):", [len(s[edge_ids]) for s in splits])
		return splits