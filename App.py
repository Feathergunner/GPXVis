#!usr/bin/python
# -*- coding: utf-8 -*-import string

import os
import threading
from flask import Flask, render_template, request, jsonify, url_for, send_from_directory

from src import AppInputManager as AIM
from src import GPXDataManager as GPXDM
from src import SubTask
from src.misc import ensure_dir_exists

from org import GPX_DIR


app = Flask(__name__)#, static_folder="output")

aim_rmap = AIM.AppInputManagerRouteMap()
aim_ad = AIM.AppInputManagerActivityData()

global current_job
current_job = None

# HTML-Seite anzeigen
@app.route("/")
def index():
	return render_template("index.html")

# display user directories for selection of gpx-directory:
@app.route("/api/list-dir")
def list_dir():
	# path = request.args.get("path", ".")
	try:
		gpxdm = GPXDM.GPXDataManager()
		subdirs = gpxdm.get_subdirs()
		#print (subdirs)
		return jsonify({
			"folders": subdirs
		})

	except Exception as e:
		print (e)
		return jsonify({
			"error": str(e)
		})

@app.route("/api/list_files")
def list_files():
	path = GPX_DIR#request.args.get("path", ".")
	try:
		gpxdm = GPXDM.GPXDataManager()
		(all_files, all_folders) = gpxdm.list_files()
		#print ("folders:", all_folders)
		#print ("files:", all_files)
		return jsonify({
			"all_folders" : all_folders,
			"all_files": all_files
		})

	except Exception as e:
		return jsonify({
			"error": str(e)
		})

@app.route("/api/newDir", methods=["POST"])
def create_new_datadir():
	dirname = request.get_json().get("dirName", "")
	full_dir_path = os.path.join(GPX_DIR,dirname)
	print ("dirname:", dirname)
	ensure_dir_exists(full_dir_path)
	#db_filepath = os.path.join(GPX_DIR, "db.csv")
	#open(db_filepath, 'a').close()

	return {
		"status": "ok"
	}

@app.route("/api/uploadGPX", methods=["POST"])
def upload_gpx():
	target_folder = request.form["target_folder"]
	files = request.files.getlist("files")
	full_target_path = os.path.join(GPX_DIR,target_folder)
	print(target_folder)
	dm = GPXDM.GPXDataManager(target_folder)

	for file in files:
		dm.add_new_file(file)
	dm.update_db()

	return {
		"status": "ok"
	}

@app.route("/api/rebuild_database")
def rebuild_database():
	print ("rebuild_database")
	gpxdm = GPXDM.GPXDataManager()
	thread = threading.Thread(target=gpxdm.rebuild_database)
	thread.start()
	return jsonify({
		"current_task": "RebuildDatabase",
		"current_status": "started",
		"total_progress": 0
	})

@app.route("/api/runMapPlotter", methods=["POST"])
def run_MapPlotter():
	global current_job
	print ("runMapPlotter")
	current_computation = "MapPlotter"
	data = request.get_json()
	print (data)
	ref_lat = data.get("lat", "")
	ref_lon = data.get("lon", "")
	ref_range = data.get("range", "")
	mapzoom = data.get("mapzoom", "")
	type = data.get("type", "")
	use_unkown_type = data.get("use_unkown_type", "")
	datadirs = data.get("dir", "")
	date_min = data.get("date_min", "")
	date_max = data.get("date_max", "")
	use_unkown_date = data.get("use_unkown_date", "")
	filename = data.get("filename", "")

	if type == "":
		type = None
	if date_min == "":
		date_min = None
	if date_max == "":
		date_max = None

	if len(datadirs) < 1:
		current_job = SubTask.SubTask("Error: no data directory specified!")
		current_job.error = True
		#current_job.finish_progress()
		return jsonify({
			"current_task": "Error: no data directory specified!",
			"current_status": "stopped",
			"total_progress": 0
		})
	if not isinstance(ref_lat, float) or not isinstance(ref_lon, float):
		current_job = SubTask.SubTask("Error: no map reference point specified!")
		current_job.error = True
		#current_job.finish_progress()
		return jsonify({
			"current_task": "Error: no map reference point specified!",
			"current_status": "stopped",
			"total_progress": 0
		})

	
	aim_rmap.set_reference_area(float(ref_lat), float(ref_lon), int(ref_range))
	aim_rmap.set_daterange(date_min, date_max, use_unkown_date)
	aim_rmap.set_activity_type(type, use_unkown_type)
	aim_rmap.set_zoom(int(mapzoom))
	#for datadir in datadirs:
	aim_rmap.set_gpx_dirs(datadirs)
	aim_rmap.set_filename_prefix(filename)
	#print (aim_rmap)
	
	current_job = aim_rmap
	current_job.start_progress()
	thread = threading.Thread(target=aim_rmap.run_plotter)
	thread.start()
	print (aim_rmap)
	#result_filepath = aim_rmap.run_plotter()
	return jsonify({
		"current_task": "MapPlotter",
		"current_status": "started",
		"total_progress": 0
	})

@app.route("/api/runDataPlotter", methods=["POST"])
def run_DataPlotter():
	global current_job
	print ("runDataPlotter")
	current_computation = "DataPlotter"
	data = request.get_json()
	print (data)
	type = data.get("type", "")
	use_unkown_type = data.get("use_unkown_type", "")
	datadirs = data.get("dir", "")
	date_min = data.get("date_min", "")
	date_max = data.get("date_max", "")
	use_unkown_date = data.get("use_unkown_date", "")
	axis_x = data.get("axis_x", "")
	axis_y = data.get("axis_y", "")
	filename = data.get("filename", "")

	if type == "":
		type = None
	if date_min == "":
		date_min = None
	if date_max == "":
		date_max = None

	if len(datadirs) < 1:
		current_job = SubTask.SubTask("Error: no data directory specified!")
		current_job.error = True
		#current_job.finish_progress()
		return jsonify({
			"current_task": "Error: no data directory specified!",
			"current_status": "stopped",
			"total_progress": 0
		})
	
	aim_ad.set_daterange(date_min, date_max, use_unkown_date)
	aim_ad.set_activity_type(type, use_unkown_type)
	#for datadir in datadirs:
	aim_ad.set_gpx_dirs(datadirs)
	aim_ad.set_key_x(axis_x)
	aim_ad.set_key_y(axis_y)
	aim_ad.set_filename_prefix(filename)
	print (aim_ad)

	current_job = aim_ad
	current_job.start_progress()
	thread = threading.Thread(target=aim_ad.run_plotter)
	thread.start()
	#result_filepath = aim_rmap.run_plotter()
	return jsonify({
		"current_task": "DataPlotter",
		"current_status": "started",
		"total_progress": 0
	})

@app.route("/api/progress")
def get_computation_progress():
	if current_job is not None:
		#print ("CURRENT JOB: "+str(current_job.get_current_taskname()))
		#print (str(current_job))
		progress = current_job.get_progress_dict()
	else:
		progress = {
			"current_task": "Nothing",
			"current_status": "stopped",
			"total_progress": 0
		}
	return jsonify(progress)

@app.route("/api/getResultPath")
def get_result_path():
	#print ("GET RESULT PATH")
	#print ("  current_job:",current_job.taskname)
	#print ("   filepath:", current_job.outputfilepath)
	if current_job is not None:
		filepath = current_job.outputfilepath
	else:
		filepath = "unknown"

	return jsonify({
		"result_filename": filepath
		})

@app.route("/output/<path:filename>")
def return_img_filepath(filename):
	#print ("requested file:",filename)
	return send_from_directory("output", filename)

# Server starten
if __name__ == "__main__":
	app.run(debug=True)