#!usr/bin/python
# -*- coding: utf-8 -*-import string

import os
import math
import numpy as np
from matplotlib import pyplot as plt
import matplotlib as mpl
from datetime import datetime, timezone
import gpxpy

from src.SubTask import SubTask
from src import ColorManager as CM

from src.misc import load_gpx_file, parse_gps_from_gpx, get_timestamp_in_seconds, format_time, format_time_hours, float_to_pace_str, ensure_dir_exists
from org import GPX_DIR, GPX_DIR_TEST, METER_PER_DEG_LAT, METER_PER_DEG_LON, LINECOLORS

KEY_UNITS = {
	"distance" : "km",
	"time" : "h:min",
	"height" : "m",
	"height relative" : "m",
	"elevation gain" : "m",
	"slope" : "%",
	"pace" : "min/km",
	"speed" : "km/h",
	"date" : "YYYY-MM-DD",
	"total distance" : "km",
	"total duration" : "h:min:sec",
	"total elevation" : "m",
}

KEY_RANGE_MIN = {
	"distance" : None,
	"time" : None,
	"height" : None,
	"height relative" : None,
	"elevation gain" : 0,
	"slope" : -0.5,
	"pace" : 2,
	"speed" : 4,
	"date" : None,
	"total distance" : 0,
	"total duration" : 0,
	"total elevation" : 0,
}

KEY_RANGE_MAX = {
	"distance" : None,
	"time" : None,
	"height" : None,
	"height relative" : None,
	"elevation gain" : None,
	"slope" : 0.5,
	"pace" : 15,
	"speed" : 30,
	"date" : None,
	"total distance" : None,
	"total duration" : None,
	"total elevation" : None,
}

def format_data(key, value):
	if key == "distance":
		dist_km = value/1000
		return f"{dist_km:03.1f}"
	elif key == "time":
		return format_time_hours(value)
	elif key == "height":
		return f"{value:.0f}"
	elif key == "height relative":
		return f"{value:.0f}"
	elif key == "elevation gain":
		return f"{value:.0f}"
	elif key == "slope":
		slope_pct = value*100
		return f"{slope_pct:2.0f}"
	elif key == "pace":
		return float_to_pace_str(value)
	elif key == "speed":
		return f"{value:.1f}"
	elif key == "date":
		return datetime.fromtimestamp(value).date()
	elif key == "total distance":
		dist_km = value/1000
		return f"{dist_km:03.1f}"
	elif key == "total duration":
		return format_time_hours(value)
	elif key == "total elevation":
		return f"{value:.0f}"

class Datapoint:
	def __init__(self, gpx, previous_datapoint=None, stats=None):
		# gps coordinates: 
		self.latitude = gpx["latitude"]
		self.longitude = gpx["longitude"]
		# timestamp in seconds since 01-01-1970
		#self.timestamp = get_timestamp_in_seconds(gpx["timestamp"])
		self.timestamp = int((gpx["timestamp"].replace(tzinfo=None)-datetime(1970,1,1)).total_seconds())
		# absolute elevation above sea level:
		self.abs_elevation = gpx["elevation"]
		self.avg_elevation = gpx["elevation"]
		if previous_datapoint is None:
			# total distance in m:
			self.dist = 0
			# total passed time in seconds:
			self.passed_time = 0
			# pace in min/km:
			self.pace = 0
			# speed in km/h:
			self.speed = 0
			# current slope in % (i.e. meter of elevation gain per 100 meter distance)
			self.slope = 0
			# elevation of start point:
			self.start_elevation = self.abs_elevation
			# relative elevation to start:
			self.rel_elevation = 0
			# cumulative elevation in m:
			self.cum_elevation = 0
			self.stats = stats
		else:
			d_lat = self.latitude-previous_datapoint.latitude
			d_lon = self.longitude-previous_datapoint.longitude
			position_diff = math.sqrt((d_lat*METER_PER_DEG_LAT)**2+(d_lon*METER_PER_DEG_LON)**2)
			time_diff = self.timestamp - previous_datapoint.timestamp
			self.dist = previous_datapoint.dist+position_diff
			self.passed_time = previous_datapoint.passed_time + time_diff
			if position_diff > 0:
				self.pace = (time_diff/position_diff)*(1000/60)
				self.slope = (previous_datapoint.abs_elevation-self.abs_elevation)/(position_diff*100)
			else:
				self.pace = previous_datapoint.pace
				self.slope = previous_datapoint.slope
			if time_diff> 0:
				self.speed = (position_diff/1000)/(time_diff/3600)
			else:
				self.speed = previous_datapoint.speed
			self.start_elevation = previous_datapoint.start_elevation
			self.rel_elevation = self.abs_elevation-self.start_elevation
			self.cum_elevation = previous_datapoint.cum_elevation + max(0, self.abs_elevation-previous_datapoint.abs_elevation)
			self.stats = previous_datapoint.stats

	def get_data_by_key(self, key:str):
		if key == "distance":
			return self.dist
		elif key == "time":
			return self.passed_time
		elif key == "height":
			return self.abs_elevation
		elif key == "height relative":
			return self.rel_elevation
		elif key == "elevation gain":
			return self.cum_elevation
		elif key == "slope":
			return self.slope
		elif key == "pace":
			return self.pace
		elif key == "speed":
			return self.speed
		elif key == "date":
			return self.timestamp
		elif key == "total distance":
			return self.stats["total distance"]
		elif key == "total duration":
			return self.stats["total duration"]
		elif key == "total elevation":
			return self.stats["total elevation"]

	def __str__(self):
		_str = ""
		for key in ["distance", "time", "height", "height relative", "elevation gain", "pace", "speed", "slope"]:
			_str += key+": "+ str(self.get_data_by_key(key))+" - "
		return _str

	def __repr__(self):
		return str(self)

class Minisplit(Datapoint):
	def __init__(self, list_of_datapoints, previous_minisplit=None):
		# create a minisplit from a list of datapoints
		# datapoints are assumed to be in order
		# gps coordinates: 
		self.latitude = list_of_datapoints[-1].latitude
		self.longitude = list_of_datapoints[-1].longitude
		# timestamp in seconds since 01-01-1970
		#self.timestamp = get_timestamp_in_seconds(gpx["timestamp"])
		self.timestamp = list_of_datapoints[-1].timestamp
		# absolute elevation above sea level:
		avg_elevation = np.mean([dp.abs_elevation for dp in list_of_datapoints])
		self.abs_elevation = avg_elevation
		# total distance in m:
		self.dist = list_of_datapoints[-1].dist
		# total passed time in seconds:
		self.passed_time = list_of_datapoints[-1].passed_time
		if previous_minisplit is None:
			# pace in min/km:
			self.pace = 0
			# speed in km/h:
			self.speed = 0
			# current slope in % (i.e. meter of elevation gain per 100 meter distance)
			self.slope = 0
			# elevation of start point:
			self.start_elevation = avg_elevation
			# relative elevation to start:
			self.rel_elevation = 0
			# cumulative elevation in m:
			self.cum_elevation = 0
			self.stats = list_of_datapoints[-1].stats
		else:
			distance_diff = list_of_datapoints[-1].dist - previous_minisplit.dist
			time_diff = list_of_datapoints[-1].timestamp - previous_minisplit.timestamp
			if distance_diff > 0:
				self.pace = (time_diff/distance_diff)*(1000/60)
				self.slope = (previous_minisplit.abs_elevation-self.abs_elevation)/(distance_diff*100)
			else:
				self.pace = previous_minisplit.pace
				self.slope = previous_minisplit.slope
			if time_diff> 0:
				self.speed = (distance_diff/1000)/(time_diff/3600)
			else:
				self.speed = previous_minisplit.speed
			self.start_elevation = previous_minisplit.start_elevation
			self.rel_elevation = self.abs_elevation-self.start_elevation
			self.cum_elevation = previous_minisplit.cum_elevation + max(0, self.abs_elevation-previous_minisplit.abs_elevation)
			self.stats = previous_minisplit.stats

class RouteProfilePlotter(SubTask):
	def __init__(self, activities:list, verbose=False):
		self.activities = activities
		self.verbose = False
		super().__init__("RouteProfilePlotter", 2+len(self.activities)//10)
		self.progress += 1

	def construct_filename(self, basename:str, suffix:str=""):
		filename = basename+"_"+str(self.zoom)
		if len(suffix) > 0:
			filename += "_"+suffix
		return filename

	def parse_data(self):
		# computes statistics like distances, speed from raw gpx-data:
		if self.verbose:
			print ("Parse data...")
		self.data = []
		for i in range(len(self.activities)):
			if self.verbose:
				print ("parse data:", self.activities[i]["name"], self.activities[i]["datetime"])
			(gpxdata, metadata) = load_gpx_file(self.activities[i]["filepath"])
			gpsdata = parse_gps_from_gpx(gpxdata)
			datapoints = []
			previous_datapoint = None
			
			# first pass: construct chain of datapoints
			if self.verbose:
				print ("construct datapoints...")
			for gps_datapoint in gpsdata:
				new_datapoint = Datapoint(gps_datapoint, previous_datapoint, self.activities[i])
				if previous_datapoint is not None and new_datapoint.dist - previous_datapoint.dist > 1000:
					# skip datapoints where gps coords jump far away 
					continue
				else:
					datapoints.append(new_datapoint)
					previous_datapoint = new_datapoint

			# second pass: compute smooth delta-data (speed, pace, slope):
			# trace window around current datapoint that covers (at most) +/- some seconds, to compute smooth speed and pace and slope
			# also compute cutoff of datastream at the end to ignore final datapoints with pace > 30min/km
			delta_seconds = 10
			window_min_id = 0
			window_max_id = 0
			cutoff_id = 0
			if self.verbose:
				print ("compute delta statistics...")
			for i in range(len(datapoints)):
				# adjust window:
				while window_min_id < i-1 and datapoints[window_min_id].timestamp < datapoints[i].timestamp-delta_seconds:
					window_min_id += 1
				while window_max_id < len(datapoints)-1 and datapoints[window_max_id].timestamp < datapoints[i].timestamp + delta_seconds:
					window_max_id += 1
				if self.verbose:
					print ("  current datapoint:",i,"("+str(datapoints[i].timestamp)+") -- current window:",window_min_id,"("+str(datapoints[window_min_id].timestamp)+")-",window_max_id,"("+str(datapoints[window_max_id].timestamp)+")")
				# compute smoothed statistics:
				window_timediff = datapoints[window_max_id].timestamp - datapoints[window_min_id].timestamp
				window_distdiff = datapoints[window_max_id].dist - datapoints[window_min_id].dist
				window_elevationdiff = datapoints[window_max_id].abs_elevation - datapoints[window_min_id].abs_elevation
				datapoints[i].speed = (window_distdiff/1000)/(window_timediff/3600)
				datapoints[i].avg_elevation = np.mean([datapoints[j].abs_elevation for j in range(window_min_id, window_max_id+1)])
				if i > 0:
					datapoints[i].cum_elevation = datapoints[i-1].cum_elevation + max(0, datapoints[i].avg_elevation-datapoints[i-1].avg_elevation)
				if window_distdiff > 1:
					datapoints[i].pace = (window_timediff/window_distdiff)*(1000/60)
					datapoints[i].slope = window_elevationdiff/(window_distdiff)
				else:
					datapoints[i].pace = None
					# distance too small, slope computation inaccurate:
					if i > 0:
						# keep slope from previous datapoint (good approximation since distance is small)
						datapoints[i].slope = datapoints[i-1].slope
				if datapoints[i].pace is not None and datapoints[i].pace < 30:
					# reset cutoff to current datapoint, since pace is sufficient
					cutoff_id = i
				if self.verbose:
					print ("  - window: timediff:",window_timediff," - distdiff:",window_distdiff," - elevationdiff:",window_elevationdiff)
					print ("  - pace:",datapoints[i].pace," - speed:",datapoints[i].speed," - slope:",datapoints[i].slope)
			
			self.data.append(datapoints[:cutoff_id])
			if i%20 == 0:
				self.progress += 1

	def plot(self, x_axis_key:str, y_axis_key:str, color_axis_key:str="singular", basename:str=""):
		plotdata = []
		metadata = []

		colormanager = CM.ColorManager(color_axis_key, self.activities)

		for i in range(len(self.data)):
			activity = self.data[i]
			data = {}
			data["xs"] = []
			data["ys"] = []
			data["color"] = []
			data["meta"] = self.activities[i]
			for datapoint in activity:
				data["xs"].append(datapoint.get_data_by_key(x_axis_key))
				data["ys"].append(datapoint.get_data_by_key(y_axis_key))
			data["color"] = colormanager.get_color(self.activities[i])
			plotdata.append(data)

		i = 0
		for data in plotdata:
			plt.plot(data["xs"], data["ys"], c=data["color"])
			i += 1
			if i%20 == 0:
				self.progress += 1

		min_x = min(min(data["xs"]) for data in plotdata)
		if KEY_RANGE_MIN[x_axis_key] is not None:
			min_x = max(min_x, KEY_RANGE_MIN[x_axis_key])
		max_x = max(max(data["xs"]) for data in plotdata)
		if KEY_RANGE_MAX[x_axis_key] is not None:
			max_x = min(max_x, KEY_RANGE_MAX[x_axis_key])
		x_diff = max_x - min_x
		if x_diff > 0:
			xtickrange = np.arange(min_x, max_x+(x_diff/10), x_diff/10)
		else:
			xtickrange = [min_x]
		xticklabels = [format_data(x_axis_key, x) for x in xtickrange]

		min_y = min(min([y for y in data["ys"] if y is not None]) for data in plotdata)
		if KEY_RANGE_MIN[y_axis_key] is not None:
			min_y = max(min_y, KEY_RANGE_MIN[y_axis_key])
		max_y = max(max([y for y in data["ys"] if y is not None]) for data in plotdata)
		if KEY_RANGE_MAX[y_axis_key] is not None:
			max_y = min(max_y, KEY_RANGE_MAX[y_axis_key])
		y_diff = max_y - min_y
		if y_diff > 0:
			ytickrange = np.arange(min_y, max_y+y_diff/10, y_diff/10)
		else:
			ytickrange = [min_y]
		yticklabels = [format_data(y_axis_key, y) for y in ytickrange]
		plt.xlim(min_x-(x_diff/20), max_x+(x_diff/20))
		plt.ylim(min_y-(y_diff/20), max_y+(y_diff/20))
		plt.xticks(xtickrange, xticklabels, rotation=20)
		plt.yticks(ytickrange, yticklabels)
		plt.xlabel(x_axis_key + " ("+KEY_UNITS[x_axis_key]+")")
		plt.ylabel(y_axis_key + " ("+KEY_UNITS[y_axis_key]+")")
		
		# save plot
		ensure_dir_exists(os.path.join("output", "activities"))
		if basename is not None and len(basename) > 0:
			result_filename = basename+"_"
		else:
			result_filename = "activities_"
		result_filename += x_axis_key+"_"+y_axis_key+".png"
		outputpath = os.path.join("output","activities",result_filename)
		plt.savefig(outputpath, bbox_inches='tight', pad_inches=0, dpi=300)
		plt.close('all')
		self.finish_progress()
		return outputpath

if __name__ == '__main__':
	pass