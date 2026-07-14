#!usr/bin/python
# -*- coding: utf-8 -*-import string

import os
import json
from datetime import datetime, date
import math
import re
import gpxpy

from src import GPXDataManager as GPXDM
from src.misc_geometry import get_latlon_vector_length

MAP_DIM_TILE = 256
MAP_DEFAULT_ZOOM = 14

date_format = r"\d\d\d\d-\d\d-\d\d"
date_regex = re.compile(date_format)

def check_datestr_format(datestr:str) -> bool:
	# check if dates are in isoformat (we don't care if dates are actually correct)
	if datestr is not None and date_regex.match(datestr) is None:
		return False
	return True

def load_json(filepath:str):
	with open(filepath, "r", encoding="utf-8") as f:
		return json.load(f)

def save_json(data, filepath:str) -> None:
	with open(filepath, "w", encoding="utf-8") as f:
		json.dump(data, f, indent=2)
		
def display_json(title:str, jsondata) -> None:
    """Format API output for better readability."""
    dashed = "-"*20
    header = f"{dashed} {title} {dashed}"
    footer = "-"*len(header)
    print(header)
    print(json.dumps(jsondata, indent=4))
    print(footer)
	
def ensure_dir_exists(directory:str) -> None:
	if not os.path.exists(directory):
		os.makedirs(directory)

# Helper function to transform pace time from "m:ss"-format to float
def pace_to_float(pace_str:str) -> float:
    try:
        minutes, seconds = map(int, pace_str.strip().split(':'))
        return minutes + seconds / 60
    except Exception as e:
        print(f"Fehler beim Parsen von Pace '{pace_str}': {e}")
        return None

# Helper function to transform time in minutes from float to "m:ss"-String
def float_to_pace_str(pace_float:float) -> str:
    total_seconds = int(round(pace_float * 60))
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes}:{seconds:02d}"
	
def format_time(seconds:int) -> str:
	'''
	formats an int of time in seconds into a string of min:sec
	'''
	if seconds <= 0 or seconds is None:
		return None
	minutes = int(seconds // 60)
	secs = int(seconds % 60)
	return f"{minutes}:{secs:02}"

def parse_full_date(date_str:str) -> datetime.date:
	# date_str: in format YYYY-MM-DDT....
	try:
		date_part = date_str.split('T')[0] if date_str else None
		date_as_date = datetime.strptime(date_part, '%Y-%m-%d').date() if date_part else None
		return date_as_date 
	except Exception as e:
		print(f"Error while parsing date '{date_str}': {e}")
		return None
		
def parse_isodatestring(date_str:str) -> datetime.date:
	'''
	Parses a string in format YYYY-MM-DD to the corresponding datetime.date-object
	'''
	if date_str is None:
		return None
	datesplit = date_str.split('-')
	return date(int(datesplit[0]), int(datesplit[1]), int(datesplit[2]))

def get_timestamp_in_seconds(date_str:str) -> int:
	# date_str: in format YYYY-MM-DDTHH:MM:SSZ
	try:
		utc_dt = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S.%fZ')
		# Convert UTC datetime to seconds since the Epoch
		timestamp = (utc_dt - datetime(1970, 1, 1)).total_seconds()
		return timestamp
	except Exception as e:
		print(f"Error while parsing date '{date_str}': {e}")
		return None

def latlong_to_merccoords(lat:float, lon:float, zoom:int=MAP_DEFAULT_ZOOM) -> tuple:
	'''
	computes the (x,y)-coordinates from (latitude, longitude) data, to fetch map tiles from mercerator projected online map service

	maths from https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Derivation_of_tile_names
	'''
	x = int((lon+180)/360 * 2**zoom)
	y = int((1-(math.log(math.tan(lat*(math.pi/180))+(1/(math.cos(lat*(math.pi/180))))))/math.pi)*2**(zoom-1))
	return (x,y)

def tile_xy_to_latlon(x:int, y:int, zoom:int=MAP_DEFAULT_ZOOM) -> tuple:
	lon = (x/(2**zoom))*360-180
	lat = math.atan(math.sinh(math.pi-(y/2**zoom)*2*math.pi))*(180/math.pi)
	return (lat, lon)

def check_daterange(datestring:datetime.date, min_date:datetime.date, max_date:datetime.date) -> bool:
	'''
	datestring: specifies a date in the format DD.MM.YYYY
	Checks if the date specified by datestring is within [min_date, max_date]
	If one of min_date, max_date is None, interval is considered to be open (in that direction)
	'''
	if min_date is not None and min_date > datestring:
		# datestring before min_date
		return False
	if max_date is not None and max_date < datestring:
		# datestring after max_date
		return False
	return True

def check_gps_range(lat:float, lon:float, ref_lat:float, ref_lon:float, delta_km:float) -> bool:
	'''
	checks if coordinate (lat, lon) is within delta-range (in km) of reference point (ref_lat, ref_lon)
	'''
	if ref_lat is None or ref_lon is None or delta_km is None:
		return True

	dist_m = get_latlon_vector_length(lat-ref_lat, lon-ref_lon)
	#print ("distance in m between (",lat, lon,") and (",ref_lat, ref_lon,") is: ",dist_m)
	dist_km = dist_m/1000
	#print ("distance in km between (",lat, lon,") and (",ref_lat, ref_lon,") is: ",dist_km)
	if dist_km < delta_km:
		return True
	else:
		return False

### LOAD GPX DATA ###
def parse_gps_from_gpx(gpxdata) -> list:
	'''
	parses gpx-file into a list of dict-encoded datapoints
	'''
	gpspoints = []
	for track in gpxdata.tracks:
		for segment in track.segments:
			for point in segment.points:
				#print (point)
				if point.latitude > 1 and point.longitude > 1:
					gpspoints.append({"latitude": point.latitude, "longitude": point.longitude, "elevation": point.elevation, "timestamp": point.time})
				#print(f'Point at ({point.latitude},{point.longitude}) -> {point.elevation}')
	return gpspoints

def load_gpx_file(filepath) -> tuple:
	# returns list of dictionaries with keys ["latitude", "longitude", "elevation")
	gpx_file = open(filepath, 'r')
	gpxdata = gpxpy.parse(gpx_file)
	metadata = {
		"name": gpxdata.tracks[0].name,
		"time": gpxdata.time
		}
	i = 0
	while gpxdata.tracks[0].segments[0].points[i].latitude < 1 or gpxdata.tracks[0].segments[0].points[i].longitude < 1:
		i += 1
	metadata["start_latitude"] = gpxdata.tracks[0].segments[0].points[i].latitude
	metadata["start_longitude"] = gpxdata.tracks[0].segments[0].points[i].longitude
	return (gpxdata, metadata)

def get_gpx(
		directory:str,
		activity_type:str,
		use_unknown_type:bool=False,
		lat_ref:float=None,
		lon_ref:float=None,
		delta_km:float=2,
		dist_cutoff_km=None,
		date_min:str=None,
		date_max:str=None,
		use_unknown_date:bool=False,
		verbose:bool=False) -> tuple:
	# check if dates are correct:
	if not check_datestr_format(date_min):
		raise ValueError("min_date has to be in isoformat YYYY-MM-DD")
	if not check_datestr_format(date_max):
		raise ValueError("max_date has to be in isoformat YYYY-MM-DD")

	activity_gpxs = []
	activity_metadata = []
	gpxs_filenames = []
	found_activity_types = []

	if verbose:
		print ("load gpx data from directory", os.path.join(directory, activity_type), "...")

	gpxdm = GPXDM.GPXDataManager(data_dir=directory)
	relevant_filepaths = gpxdm.get_list_of_gpx_files(lat_ref, lon_ref, delta_km, activity_type, use_unknown_type, date_min, date_max, use_unknown_date)
	for filepath in relevant_filepaths:
		(gpxdata, metadata) = load_gpx_file(filepath)
		activity_gpxs.append(gpxdata)
		activity_metadata.append(metadata)
		gpxs_filenames.append(filepath)
	activity_statistics = gpxdm.get_statistics_from_db(lat_ref, lon_ref, delta_km, activity_type, use_unknown_type, date_min, date_max, use_unknown_date)

	return (activity_gpxs, activity_metadata, gpxs_filenames, activity_statistics)