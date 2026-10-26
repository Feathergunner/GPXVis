#!usr/bin/python
# -*- coding: utf-8 -*-import string

import gpxpy
import datetime

from src.misc import parse_gps_from_gpx
from src.misc_geometry import get_latlon_vector_length

def get_metadata_from_file(file, compute_aggregates:bool=False):
	'''
	parses a gpx-file and extracts start location and date.
	computes aggregated data (total distance, total time, total elevation, ...) if compute_aggregates is true
	'''
	print ("get metadata...")
	gpxdata = gpxpy.parse(file)
	# proceed through coordinates to skip potential (0,0) points at the beginning:
	first_correct_datapoint = 0
	while gpxdata.tracks[0].segments[0].points[first_correct_datapoint].latitude < 1 and gpxdata.tracks[0].segments[0].points[first_correct_datapoint].longitude < 1:
		first_correct_datapoint += 1
	start_lat = gpxdata.tracks[0].segments[0].points[first_correct_datapoint].latitude
	start_lon = gpxdata.tracks[0].segments[0].points[first_correct_datapoint].longitude

	print ("gpxdata:", gpxdata)
	#print (gpxdata.time)

	# get other metadata:
	if gpxdata.time is not None:
		_date = gpxdata.time.date().isoformat()
		_datetime = gpxdata.time.isoformat()
	else:
		_date = "unknown"
		_datetime = "unknown"
	if gpxdata.tracks[0].type is not None:
		_type = gpxdata.tracks[0].type
	else:
		_type = "unknown"
	if gpxdata.tracks[0].name is not None:
		_name = gpxdata.tracks[0].name
	else:
		_name = ""

	total_dist = 0
	total_elevation = 0
	total_time = datetime.timedelta(0)
	if compute_aggregates:
		datapoints = parse_gps_from_gpx(gpxdata)
		current_lat = start_lat
		current_lon = start_lon
		current_elevation = datapoints[first_correct_datapoint]["elevation"]
		for i in range(first_correct_datapoint, len(datapoints)):
			total_dist += get_latlon_vector_length(datapoints[i]["latitude"]-current_lat, datapoints[i]["longitude"]-current_lon)
			total_elevation += max(0, datapoints[i]["elevation"]-current_elevation)
			current_lat = datapoints[i]["latitude"]
			current_lon = datapoints[i]["longitude"]
			current_elevation = datapoints[i]["elevation"]
		print ("last datapoint:", datapoints[-1])
		if datapoints[-1]["timestamp"] is not None:
			total_time = datapoints[-1]["timestamp"]-datapoints[first_correct_datapoint]["timestamp"]

	metadata = {
		"date": _date,
		"datetime": _datetime,
		"lat": start_lat,
		"lon": start_lon,
		"type": _type,
		"name": _name,
		"total distance": total_dist,
		"total duration": total_time,
		"total elevation": total_elevation
	}
	return metadata