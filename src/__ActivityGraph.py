#!usr/bin/python
# -*- coding: utf-8 -*-import string

import os
import datetime
import gpxpy

from src import DatabaseHandler as DBH
from src.SubTask import SubTask
from src.misc_geometry import get_latlon_vector_length
from src.misc import ensure_dir_exists


class ActivityGraphNode():
	'''
	Class to represent nodes data with activity metadata
	'''
	n = 0
	def __init__(self, gpxpoint):
		'''
		Constructs a graph node from a gpx point (as parsed by gpxpy)
		'''
		self.id = ActivityGraphNode.n
		ActivityGraphNode.n += 1
		self.latitude = gpxpoint.latitude
		self.longitude = gpxpoint.longitude
		self.elevation = gpxpoint.elevation
		self.timestamp = gpxpoint.time
		for extension in gpxpoint.extensions:
			tag = extension.tag.split('}')[-1]
			if tag in ["hr", "heartrate", "heart_rate"]:
				self.heartrate = int(extension.text)
			elif tag in ["cad", "cadence"]:
				self.cadence = int(extension.text)

	def __str__(self):
		return "GraphNode: pos:("+str(self.get_latitude())+","+str(self.get_longitude())+"), elevation: "+str(self.get_elevation())

	def __repr__(self):
		return str(self)

	def get_position(self):
		return (self.get_longitude(), self.get_latitude())

class BaseGraphEdge():
	def __init__(self):
		self.id = -1
		self.id_min = -1
		self.id_max = -1

	def __str__(self):
		return "Edge "+str(self.id)+" between nodes "+str(self.id_min)+" - "+str(self.id_max)

	def __repr__(self):
		return str(self)

	def get_node_list(self):
		return [self.id_min, self.id_max]

	def get_key(self):
		return get_edge_key(self.id_min, self.id_max)


class ActivityGraphEdge(BaseGraphEdge):
	# class to hold tour segment data (like average speed) to be used for plotting
	n = 0

	def __init__(self, node_a:ActivityGraphNode, node_b:ActivityGraphNode):
		self.id = ActivityGraphEdge.n
		ActivityGraphEdge.n += 1

		self.length = get_latlon_vector_length(node_a.latitude-node_b.latitude, node_a.longitude-node_b.longitude)

		time_a = node_a.timestamp
		time_b = node_b.timestamp
		elevation_a = node_a.elevation
		elevation_b = node_b.elevation
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


class ActivityGraph():
	# class to construct a graoh for a single activity,
	# to plot activity with color-coded graph segments
	# or to create tour animation 

	def __init__(self, activity:DBH.ActivityDTO):
		# graph objects:
		self.nodes = {}
		self.edges = []

		# valid start point (within gpx file):
		self.start_node_id = None
		self.start_latitude = None
		self.start_longitude = None

		self.activity = activity
		#self.record_ids = []

		# activity aggregated statistics:
		self.total_distance = 0
		self.total_duration = 0
		self.elevation_gain = 0

		# filepath to preview image:
		self.previewpath = None

	'''
	# needs app_context()
	def write_to_database(self, db):
		if self.database_activity is not None:
			# activity already exists in database, skip:
			return
		# build database entry:
		self.database_activity = DBH.Activity(
			activitytype_id = self.acitivitytype_id,
			athlete_id = self.athlete_id,
			name = self.name,
			filepath = self.filepath,
			datetime = self.datetime,
			distance = self.total_distance,
			duration = self.total_duration.total_seconds(),
			elevation = self.elevation_gain,
			start_latitude = self.start_latitude,
			start_longitude = self.start_longitude)
		db.session.add(self.database_activity)
		db.session.commit()
	'''

	def number_of_nodes(self) -> int:
		return len(self.nodes.keys())

	def number_of_edges(self) -> int:
		return len(self.edges)

	def is_empty(self) -> bool:
		return self.number_of_nodes() == 0

	def add_metadata(self, metadatadict:dict):
		self.name = metadatadict["name"]
		self.type = metadatadict["type"]
		self.datetime = metadatadict["datetime"]
		self.start_index = metadatadict["start_index"]
		self.start_latitude = metadatadict["start_latitude"]
		self.start_longitude = metadatadict["start_longitude"]

	def add_node(self, node:ActivityGraphNode):
		self.nodes[node.id]=node

	def get_node(self, node_id:int):
		return self.nodes[node_id]

	def add_egde(self, node_a:ActivityGraphNode, node_b:ActivityGraphNode):
		new_edge = ActivityGraphEdge(node_a, node_b)
		self.edges.append(new_edge)

	def get_split_segments(self, splitdistance:int=None, splittime:int=None, offset:int=0):
		'''
		Returns a list of lists of edge-ids, where each list of edge-ids covers a split.
		
		If splitdistance is not None, this defines the length of a split in meters.
		Else if splittime is not None, this defines the length of a split in seconds.
			If both are None, splitdistance is set to 100 meters.

		offset: specifies how many datapoints in the beginning of the tour are skipped
		before the first segment starts (used to synchronize the segments multiple tours).
		'''

		## todo: move this to TourGraphConstructor and add progress tracking
		## better: move to plotter

		#print ("get split segments for tour",self.basename)
		if splitdistance is None and splittime is None:
			splitdistance = 100

		current_total_covered = 0
		if splitdistance is not None:
			next_split_end = splitdistance
		else:
			next_split_end = splittime

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
		return splits


class ActivityGraphConstructor(SubTask):
	def __init__(self):
		self.agraph = None
		super().__init__("ActivityGraphConstructor", 2)

	'''
	this must move to activityuploader
	def build_from_file(self, gpxfilepath:str, athlete:DBH.Athlete):
		# build activitygraph directly from gpx file.
		# assumes this activity does not exist yet in database.
		# adjust weight to consider multiple steps:
		self.weight = 4
		# load gpxdata:
		self._init_graph(gpxfilepath, athlete.id)
		# build graph:
		self._construct_graph_structure()
		self.progress += 1

		# compute aggregated statistics:
		self._compute_aggregates()
		self.progress += 1

		# compute records:
		ru = RecordUpdater(self.agraph)
		self.add_task_child(ru)
		ru.update_records()

		# create preview image:
		# todo (needs tourgraphplotter)
		self.progress += 1

		self.finish_progress()
		return self.agraph
	'''

	def build_from_database(self, activity:DBH.ActivityDTO):
		# build activitygraph from existing DBH.ActivityDTO
		# load gpxdata:
		self._init_graph(activity.filepath, activity.athlete_id, activity.activitytype_id)
		self.agraph.activity = activity
		# build graph:
		self._construct_graph_structure()
		self.progress += 1

		self.finish_progress()
		return self.agraph

	def _init_graph(self, gpxfilepath:str, athlete_id:int, acitivitytype_id:int) -> None:
		self.agraph = ActivityGraph(athlete_id)
		# load file, parse file for metadata and gps coordinates:
		self.gpxdata = gpxpy.parse(open(gpxfilepath, 'r'))
		self._get_gpx_metadata(self.gpxdata)

	def _construct_graph_structure(self) -> None:
		# Constructs graph
		# computes aggregated statistics
		# finds records for track in gpxdata.tracks:
		previous_node = None

		for track in self.gpxdata.tracks:
			for s_i in range(len(track.segments)):
				segment = track.segments[s_i]
				if (s_i == 0):
					start_index = self.agraph.start_index
				else:
					start_index = 0
				for p_i in range(start_index, len(segment.points)):
					new_node = ActivityGraphNode(segment.points[p_i])
					self.agraph.add_node(new_node)
					if previous_node is not None:
						# construct edge:
						self.agraph.add_egde(previous_node, new_node)
					previous_node = new_node

	def _compute_aggregates(self) -> None:
		self.agraph.total_distance = 0
		self.agraph.total_duration = 0
		self.agraph.elevation_gain = 0
		for edge in self.agraph.edges:
			self.agraph.total_distance += edge.length
			self.agraph.total_duration += edge.duration
			self.agraph.elevation_gain += max(0, edge.elevation_change)

	def _get_gpx_metadata(self, gpxdata) -> None:
		'''
		gpxdata: as returned by gpxpy.parse
	
		Reads header of gpxdata and sets basic metadata in self.agraph,
		and finds first valid coordinate (i.e. coordinate that isn't near (0,0))
		'''
		# get datetime of activity:
		if gpxdata.time is not None:
			self.agraph.date = gpxdata.time.date().isoformat()
			self.agraph.datetime = gpxdata.time.isoformat()
		# get id of activity type:
		if gpxdata.tracks[0].type is not None:
			# get name of activity type:
			activitytype_name = gpxdata.tracks[0].type
		else:
			# activity type is unknown:
			activitytype_name = "unknown"
		#self.acitivitytype_id = DBH.ensure_activitytype_exists(activitytype_name)
		# get name of activity:
		if gpxdata.tracks[0].name is not None:
			self.agraph.name = gpxdata.tracks[0].name
		else:
			self.agraph.name = ""
	
		# ensure coordinates are not (0,0).
		# This happens sometimes as default values, but since the position is in the middle of the ocean,
		# we can always dismiss the datapoint in this case.
		# The first datapoint outside of the square (+/- 1, +/-1) is used as the start of the activity.
		i = 0
		while abs(gpxdata.tracks[0].segments[0].points[i].latitude) < 1 and abs(gpxdata.tracks[0].segments[0].points[i].longitude) < 1:
			i += 1
		self.agraph.start_latitude = gpxdata.tracks[0].segments[0].points[i].latitude
		self.agraph.start_longitude = gpxdata.tracks[0].segments[0].points[i].longitude
		self.agraph.start_index = i


def check_for_missing_records(activity:DBH.Activity) -> list:
	'''
	Given a DBH.Activity, checks if this activity qualifies for any recordtype for which no recorddata yet exists.
	Needs to be run within app_context!

	Returns the list of DBH.RecordType that contains all recordtypes for which this activity qualifies but that are not yet in the database.
	'''
	relevant_recordtypes = DBH.get_recordtypes_by_(activity.activitytype_id)
	existing_recordtype_ids = [record.recordtype_id for record in DBH.get_recorddata_by_([activity.id])]
	missing_recordtypes = []
	for recordtype in relevant_recordtypes:
		if recordtype.id not in existing_recordtype_ids and recordtype.distance*1000<activity.distance:
			# recordtype is truly missing:
			missing_recordtypes.append(recordtype)
	return missing_recordtypes

