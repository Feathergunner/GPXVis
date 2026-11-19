#!usr/bin/python
# -*- coding: utf-8 -*-import string

import os
import datetime
import gpxpy

from src.SubTask import SubTask
from src import ActivityPath as AP
from src import DatabaseHandler as DBH

from org import GPX_DIR

class ActivityMetadata():
	'''
	Handles initial parsing of gpx-file
	to extract metadata
	and find first valid trackpoint
	'''
	def __init__(self, gpxdata):
		# basic metadata:
		self.datetime = None
		self.activitytype_name = "unknown"
		self.name = ""
		# first datapoint:
		self.start_latitude = None
		self.start_longitude = None
		self.start_index = 0
		# aggregated data:
		self.duration_total = 0
		self.distance_total = 0
		self.elevation_gain = 0

		self._get_gpx_metadata(gpxdata)

	def _get_gpx_metadata(self, gpxdata) -> None:
		'''
		gpxdata: as returned by gpxpy.parse
	
		Reads header of gpxdata and sets basic metadata in self.agraph,
		and finds first valid coordinate (i.e. coordinate that isn't near (0,0))
		'''
		# get datetime of activity:
		if gpxdata.time is not None:
			self.date = gpxdata.time.date().isoformat()
			self.datetime = gpxdata.time.isoformat()
		# get id of activity type:
		if gpxdata.tracks[0].type is not None:
			# get name of activity type:
			self.activitytype_name = gpxdata.tracks[0].type
		# get name of activity:
		if gpxdata.tracks[0].name is not None:
			self.name = gpxdata.tracks[0].name
	
		# ensure coordinates are not (0,0).
		# This happens sometimes as default values, but since the position is in the middle of the ocean,
		# we can always dismiss the datapoint in this case.
		# The first datapoint outside of the square (+/- 1, +/-1) is used as the start of the activity.
		i = 0
		while abs(gpxdata.tracks[0].segments[0].points[i].latitude) < 1 and abs(gpxdata.tracks[0].segments[0].points[i].longitude) < 1:
			i += 1
		self.start_latitude = gpxdata.tracks[0].segments[0].points[i].latitude
		self.start_longitude = gpxdata.tracks[0].segments[0].points[i].longitude
		self.start_index = i

	def add_aggregated_statistics(self, duration_total, distance_total, elevation_gain):
		self.duration_total = duration_total
		self.distance_total = distance_total
		self.elevation_gain = elevation_gain


def check_for_missing_records(activity:DBH.ActivityDTO) -> list:
	'''
	Given a DBH.ActivityDTO, checks if this activity qualifies for any recordtype for which no recorddata yet exists.
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


class RecordUpdater(SubTask):
	def __init__(self, activity:DBH.ActivityDTO, nodelist:list, missing_recordtypes:list):
		self.activity = activity
		self.nodelist = nodelist
		self.missing_recordtypes = missing_recordtypes
		# set a callback function that can be run within app_context:
		super().__init__("RecordUpdater", 2)

	def get_missing_records(self):
		# get new recorddata:
		recorddata = self._compute_records()
		self.finish_progress()
		return recorddata

	def _compute_records(self) -> list:
		'''
		Parses activity graph and computes records.
		Returns a list of DBH.RecordData
		'''
		# init helper datastructure:
		n_types = len(self.missing_recordtypes)
		n_edges = len(self.nodelist)-1
		total_distance_at_position = [0]+[-1 for _ in range(n_edges)]
		total_time_at_position = [datetime.timedelta(0)]+[-1 for _ in range(n_edges)]
		for e_i in range(n_edges):
			total_distance_at_position[e_i+1] = total_distance_at_position[e_i]+self.nodelist[e_i].length
			total_time_at_position[e_i+1] = total_time_at_position[e_i]+self.nodelist[e_i].delta_time
		current_ends_pos = [0 for _ in  range(n_types)]
		best_times = [None for _ in range(n_types)]
		best_times_start_id = [None for _ in range(n_types)]
		best_times_end_id = [None for _ in range(n_types)]

		# parse activitygraph to find record intervals:
		current_start_pos = -1
		reached_end = False
		while not reached_end:
			reached_end = True
			current_start_pos += 1
			for t_i in range(n_types):
				while current_ends_pos[t_i]<n_edges+1 and  total_distance_at_position[current_ends_pos[t_i]]-total_distance_at_position[current_start_pos] < self.missing_recordtypes[t_i].distance*1000:
					current_ends_pos[t_i] += 1
				if current_ends_pos[t_i] >= n_edges:
					continue
				else:
					reached_end = False
					if best_times[t_i] is None or time < best_times[t_i]:
						best_times_start_id[t_i] = current_start_pos
						best_times_end_id[t_i] = current_ends_pos[t_i]
		
		# get exact time and elevation data:
		best_times_start = [total_time_at_position[best_times_start_id[t_i]] for t_i in range(n_types)]
		best_times = [total_time_at_position[best_times_end_id[t_i]]-total_time_at_position[best_times_start_id[t_i]] for t_i in range(n_types)]
		elevation_gains = [0 for _ in range(n_types)]
		elevation_deltas = [0 for _ in range(n_types)]
		for t_i in range(n_types):
			for e_i in range(best_times_start_id[t_i], best_times_end_id[t_i]):
				elevation_gains[t_i] += max(0, self.nodelist[e_i].delta_elevation)
				elevation_deltas[t_i] += self.nodelist[e_i].delta_elevation

		# create recorddata objects:
		recorddata = []
		for t_i in range(n_types):
			if best_times[t_i] is not None:
				recorddata.append(DBH.RecordData(
					recordtype_id	= self.missing_recordtypes[t_i].id,
					athlete_id		= self.activity.athlete_id,
					activity_id		= self.activity.id,
					time			= best_times[t_i].total_seconds(),
					starttime		= best_times_start[t_i].total_seconds(),
					endtime			= best_times[t_i].total_seconds()+best_times_start[t_i].total_seconds(),
					elevation_gain	= elevation_gains[t_i],
					elevation_delta	= elevation_deltas[t_i]))
		return recorddata


class ActivityUploader(SubTask):
	def __init__(self, files:list, athlete_id:int, app):
		self.files = files
		self.athlete_id = athlete_id
		self.app = app
		super().__init__("ActivityUploadManager", 2+len(files)*2)

	def upload_activities(self) -> None:
		with self.app.app_context():
			#new_activities_ids = []
			for gpxfile in self.files:
				# parse gpx file:
				gpxdata = gpxpy.parse(gpxfile)
				metadata = ActivityMetadata(gpxdata)
				nodelist = AP.construct_pathnodes(gpxdata, metadata.start_index)
				fullsplit = AP.Split(nodelist)
				duration_total = fullsplit.delta_time.total_seconds()
				distance_total = fullsplit.length
				elevation_gain = fullsplit.elevation_gain
				metadata.add_aggregated_statistics(duration_total, distance_total, elevation_gain)

				# copy file to local folder:
				new_filename = str(self.athlete_id)+"_"+metadata.activitytype_name+"_"+str(metadata.datetime)+".gpx"
				target_filepath = os.path.join(GPX_DIR, new_filename)
				gpxfile.seek(0)
				gpxfile.save(target_filepath)
	
				# Add data to database:
				new_activity = DBH.add_activity(target_filepath, metadata.activitytype_name, self.athlete_id)
				self.progress += 1

				# create record data:
				missing_recordtypes = check_for_missing_records(new_activity)
				ru = RecordUpdater(new_activity, nodelist, missing_recordtypes)
				self.add_task_child(ru)
				recorddata = ru.get_missing_records()
				# add to database:
				for record in recorddata:
					DBH.db.session.add(record)
				DBH.db.session.commit()
	
				# create preview image:
				## todo
				self.progress += 1
				
				#new_activities_ids.append(new_activity_id)

		self.finish_progress()

