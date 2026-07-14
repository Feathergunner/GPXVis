#!usr/bin/python
# -*- coding: utf-8 -*-import string

'''
Script to check gpx-files, and move them to a subfolder by activity-type with meaningful filenames constructed from activity-type and date
'''

import os
import shutil
import gpxpy
import csv

from src.misc import parse_gps_from_gpx, ensure_dir_exists, load_json, parse_full_date, check_datestr_format, parse_isodatestring, check_gps_range, check_daterange
from src.misc_geometry import get_latlon_vector_length
from org import GPX_DIR

class GPXDataManager():
	def __init__(self, data_dir:str=None):
		self.main_dir = GPX_DIR#main_dir
		if data_dir is not None:
			self.data_dir = os.path.join(self.main_dir, data_dir)
		else:
			self.data_dir = self.main_dir
		ensure_dir_exists(self.data_dir)
		self.metafile_path = os.path.join(self.main_dir, "db.csv")
		if not os.path.exists(self.metafile_path):
			open(self.metafile_path, 'a').close()
		print ("init GPXDataManager at dir",self.data_dir)

	def _get_db(self):
		print ("get db from ", self.metafile_path)
		with open(self.metafile_path, 'r') as dbfile:
			dbreader = csv.reader(dbfile, delimiter=',')
			file_db = {}
			for line in dbreader:
				print (line)
				norm_path = os.path.normpath(line[0])
				print (norm_path)
				parts = norm_path.split(os.sep)
				print (parts)
				mainpath = os.sep.join(parts[:2])
				print (mainpath, self.data_dir)
				if mainpath == self.data_dir:
					file_db[line[0]] = {
						"date": line[1],
						"lat": float(line[2]),
						"lon": float(line[3]),
						"type": line[4],
						"total distance": int(line[5]),
						"total duration": int(line[6]),
						"total elevation": int(line[7]),
						"name":line[8]
					}
		return file_db

	def get_subdirs(self):
		subdirs = []
		elements = os.listdir(self.main_dir)
		for element in elements:
			if os.path.isdir(os.path.join(self.main_dir,element)):
				subdirs.append(element)
		'''
		with open(self.metafile_path, 'r') as dbfile:
			dbreader = csv.reader(dbfile, delimiter=',')
			filelist = [line[0] for line in dbreader]
		for entry in filelist:
			[path, filename] = os.path.split(entry)
			if path not in subdirs:
				subdirs.append(path)
		'''
		return subdirs

	def _write_db(self, data):
		with open(self.metafile_path, 'w') as dbfile:
			dbwriter = csv.writer(dbfile, delimiter=',')
			for key in data:
				dbwriter.writerow([key, data[key]["date"], data[key]["lat"], data[key]["lon"], data[key]["type"], data[key]["total distance"], data[key]["total duration"], data[key]["total elevation"], data[key]["name"]])

	def list_files(self, subdir:str=None):
		if subdir is None:
			data_dir = self.main_dir
			subdir = ""
		else:
			data_dir = os.path.join(self.main_dir, subdir)
		all_files = {}
		all_folders = []
		items = os.listdir(data_dir)
		for item in items:
			full_path = os.path.join(data_dir, item)
			if os.path.isdir(full_path):
				subfolder = os.path.join(subdir, item)
				all_folders.append(subfolder)
				(sub_files, sub_folders) = self.list_files(subfolder)
				all_files = all_files | sub_files
				all_folders += sub_folders
			else:
				if item.endswith(".gpx"):
					if not subdir in all_files:
						all_files[subdir] = []
					all_files[subdir].append(item)
		return (all_files, all_folders)

	def _get_activity_metadata(self, activityfilepath, compute_aggregates:bool=False):
		with open(activityfilepath, 'r') as activityfile:
			return self._get_metadata_from_file(activityfile)

	def _get_metadata_from_file(self, file, compute_aggregates:bool=False):
		'''
		parses a gpx-file and extracts start location and date.
		computes aggregated data (total distance, total time, total elevation, ...) if compute_aggregates is true
		'''
		gpxdata = gpxpy.parse(file)
		# proceed through coordinates to skip potential (0,0) points at the beginning:
		first_correct_datapoint = 0
		while gpxdata.tracks[0].segments[0].points[first_correct_datapoint].latitude < 1 and gpxdata.tracks[0].segments[0].points[first_correct_datapoint].longitude < 1:
			first_correct_datapoint += 1
		start_lat = gpxdata.tracks[0].segments[0].points[first_correct_datapoint].latitude
		start_lon = gpxdata.tracks[0].segments[0].points[first_correct_datapoint].longitude
		# get other metadata:
		if gpxdata.time is not None:
			date = gpxdata.time.date().isoformat()
		else:
			date = "unknown"
		if gpxdata.tracks[0].type is not None:
			type = gpxdata.tracks[0].type
		else:
			type = "unknown"
		if gpxdata.tracks[0].name is not None:
			name = gpxdata.tracks[0].name
		else:
			name = ""

		total_dist = 0
		total_elevation = 0
		total_time = 0

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
			total_time = datapoints[-1]["timestamp"]-datapoints[first_correct_datapoint]["timestamp"]

		metadata = {
			"date": date,
			"lat": start_lat,
			"lon": start_lon,
			"type": type,
			"name": name,
			"total distance": total_dist,
			"total duration": total_time,
			"total elevation": total_elevation
		}
		return metadata

	def _update_db_subdir(self, existing_db, source_dir:str=None, compute_aggregates:bool=False):
		if source_dir is None:
			source_dir = self.main_dir
		print ("Update DB in dir:", source_dir)
		for itemname in os.listdir(source_dir):
			itempath = os.path.join(source_dir, itemname)
			if os.path.isfile(itempath):
				if itemname.endswith(".gpx"):
					print ("  Consider item",itemname)
					if not itempath in existing_db.keys():
						existing_db[itempath] = self._get_activity_metadata(itempath, compute_aggregates)
			elif os.path.isdir(itempath):
				self._update_db_subdir(existing_db, itempath, compute_aggregates)
		return existing_db

	def rebuild_database(self, compute_aggregates:bool=True):
		db = self._update_db_subdir({}, compute_aggregates=compute_aggregates)
		self._write_db(db)

	def update_db(self):
		file_db = self._get_db()
		updated_db = self._update_db_subdir(file_db)
		self._write_db(updated_db)

	def add_new_file(self, file, update_db:bool=False, target_dir:str=None):
		if target_dir is None:
			target_dir = self.data_dir
		metadata = self._get_metadata_from_file(file)
		print (metadata)
		# construct filename and determine filepath:
		new_filename = metadata["type"]+"_"+metadata["date"]+".gpx"
		if metadata["type"] == "hiking" or metadata["type"] == "walking":
			subdir = "hiking"
		else:
			subdir = metadata["type"]
		full_target_dir = os.path.join(target_dir, subdir)
		ensure_dir_exists(full_target_dir)
		target_filepath = os.path.join(full_target_dir, new_filename)
		# if activity with this filename already exists (e.g. multiple activities on single day),
		# then append counter:
		multiple_acitivty_suffix_counter = 1
		while os.path.exists(target_filepath):
			# todo: check other metadata (e.g. lat/lon to prohibit multiple copies of the same activity)
			multiple_acitivty_suffix_counter += 1
			new_filename = metadata["type"]+"_"+metadata["date"]+"_"+str(multiple_acitivty_suffix_counter)+".gpx"
			target_filepath = os.path.join(full_target_dir, new_filename)
		# save file at destination:
		file.seek(0)
		file.save(target_filepath)
		if update_db:
			self.update_db()

	def add_new_files(self, source_dir:str, target_dir:str=None, compute_aggregates:bool=False):
		if target_dir is None:
			target_dir = self.data_dir
		for filename in os.listdir(source_dir):
			if filename.endswith(".gpx"):
				source_filepath = os.path.join(source_dir, filename)
				metadata = self._get_activity_metadata(source_filepath, compute_aggregates)
				print (metadata)
				# construct filename and determine filepath:
				new_filename = metadata["type"]+"_"+metadata["date"]+".gpx"
				if metadata["type"] == "hiking" or metadata["type"] == "walking":
					subdir = "hiking"
				else:
					subdir = metadata["type"]
				full_target_dir = os.path.join(target_dir, subdir)
				ensure_dir_exists(full_target_dir)
				target_filepath = os.path.join(full_target_dir, new_filename)
				# if activity with this filename already exists (e.g. multiple activities on single day),
				# then append counter:
				multiple_acitivty_suffix_counter = 1
				while os.path.exists(target_filepath):
					# todo: check other metadata (e.g. lat/lon to prohibit multiple copies of the same activity)
					multiple_acitivty_suffix_counter += 1
					new_filename = metadata["type"]+"_"+metadata["date"]+"_"+str(multiple_acitivty_suffix_counter)+".gpx"
					target_filepath = os.path.join(full_target_dir, new_filename)
				# copy file to new destination:
				shutil.copyfile(source_filepath, target_filepath)
				print ("copied file", source_filepath, "to", target_filepath)
		self.update_db()

	def get_list_of_gpx_files(self, lat_ref:float, lon_ref:float, delta_km:float=2, activity_type:str=None, use_unknown_type:bool=False, date_min:str=None, date_max:str=None, use_unknown_date:bool=False):
		# check if dates are correct:
		if not check_datestr_format(date_min):
			raise ValueError("date_min("+str(date_min)+") has to be in isoformat YYYY-MM-DD")
		if not check_datestr_format(date_max):
			raise ValueError("max_date("+str(date_max)+") has to be in isoformat YYYY-MM-DD")

		filelist = []
		db = self._get_db()
		print ("db:", db)
		for filename in db:
			file = db[filename]
			print (filename, file)
			if activity_type is not None and file["type"] != "unkown" and file["type"] != activity_type:
				#print ("  ...wrong activity_type! required:", str(activity_type), " - found:", file["type"])
				continue
			if file["type"] == "unknown" and not use_unknown_type:
				continue
			if file["date"] == "unknown" and not use_unknown_date:
				continue
			if file["date"] != "unknown":
				#print (file["date"], "is not Unknown:")
				#print ("check date range")
				as_full_date = parse_full_date(file["date"])
				if as_full_date is not None:
					timestamp = as_full_date
				else:
					timestamp = parse_isodatestring(file["date"])
				if not check_daterange(timestamp, parse_isodatestring(date_min), parse_isodatestring(date_max)):
					#data_is_in_range = False 
					#print ("  ...not in date range")
					continue
			if not check_gps_range(float(file["lat"]), float(file["lon"]), lat_ref, lon_ref, delta_km):
				#data_is_in_range = False 
				#print ("  ...not in gps range")
				continue
			filelist.append(filename)
		print ("found files:")
		print(filelist)
		return filelist
		
	def get_statistics_from_db(self, lat_ref:float, lon_ref:float, delta_km:float=2, activity_type:str=None, use_unknown_type:bool=False, date_min:str=None, date_max:str=None, use_unknown_date:bool=False):
		files = self.get_list_of_gpx_files(lat_ref, lon_ref, delta_km, activity_type, use_unknown_type, date_min, date_max, use_unknown_date)
		statistics = {}
		db = self._get_db()

		for file in files:
			statistics[file] = db[file]
		return statistics
'''
def parse_dir(gpxdir):
	for filename in os.listdir(gpxdir):
		if filename.endswith(".gpx"):
			#print ("read file:",filename)
			sourcefilepath = os.path.join(gpxdir, filename)
			gpx_file = open(sourcefilepath, 'r')
			gpx = gpxpy.parse(gpx_file)
			act_type = gpx.tracks[0].type
			act_date = gpx.time

			new_filename = act_type+"_"+act_date.date().isoformat()+".gpx"
			if act_type == "hiking" or act_type == "walking":
				subdir = "hiking"
			else:
				subdir = act_type
			targetdir = os.path.join(gpxdir, subdir)
			ensure_dir_exists(targetdir)
			targetfilepath = os.path.join(targetdir, new_filename)
			multiple_acitivty_suffix_counter = 1
			while os.path.exists(targetfilepath):
				multiple_acitivty_suffix_counter += 1
				new_filename = act_type+"_"+act_date.date().isoformat()+"_"+str(multiple_acitivty_suffix_counter)+".gpx"
				targetfilepath = os.path.join(targetdir, new_filename)
			
			shutil.copyfile(sourcefilepath, targetfilepath)
			print ("copied file", sourcefilepath, "to", targetfilepath)
'''

if __name__ == '__main__':
	gpxdm = GPXDataManager(main_dir="gpxdata")
	#gpxdm.rebuild_database()
	gpxdm.add_new_files(os.path.expanduser("~/Downloads"))
	#gpxdm.add_new_files(os.path.expanduser("gpx_leutra"))