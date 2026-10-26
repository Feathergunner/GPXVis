#!usr/bin/python
# -*- coding: utf-8 -*-import string

import os
import threading
from flask import Flask, render_template, request, jsonify, url_for, send_from_directory

from src import AppInputManager as AIM
from src import SubTask
from src.DatabaseHandler import db, get_activities_by_, get_activities_by_ids
from src import DatabaseHandler as DBH
from src.misc import ensure_dir_exists, check_gps_range
from src.misc_files import get_metadata_from_file

from org import GPX_DIR


app = Flask(__name__)
# init database:
DB_PATH = "project.db"
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"

db.init_app(app)
with app.app_context():
	db.create_all()
	#DBH.test_db()

aim_rmap = AIM.AppInputManagerRouteMap()
aim_ta = AIM.AppInputManagerTourAnimation()
aim_ad = AIM.AppInputManagerActivityData()

global current_job
current_job = None

# HTML-Seite anzeigen
@app.route("/")
def index():
	return render_template("index.html")

@app.route("/upload")
def upload():
	_athletes = db.session.execute(
		db.select(DBH.Athlete).order_by(DBH.Athlete.name)
	).scalars().all()

	return render_template(
		"upload.html",
		athletes=_athletes)

@app.route("/database")
def database():
	_athletes = db.session.execute(
		db.select(DBH.Athlete).order_by(DBH.Athlete.name)
	).scalars().all()

	_activity_types = db.session.execute(
		db.select(DBH.ActivityType).order_by(DBH.ActivityType.name)
	).scalars().all()

	return render_template(
		"database.html",
		athletes=_athletes,
		activity_types=_activity_types)

@app.route("/statistics")
def statistics():
	_athletes = db.session.execute(
		db.select(DBH.Athlete).order_by(DBH.Athlete.name)
	).scalars().all()

	_activity_types = db.session.execute(
		db.select(DBH.ActivityType).order_by(DBH.ActivityType.name)
	).scalars().all()

	return render_template(
		"statistics.html",
		athletes=_athletes,
		activity_types=_activity_types)

@app.route("/maps")
def maps():
	_athletes = db.session.execute(
		db.select(DBH.Athlete).order_by(DBH.Athlete.name)
	).scalars().all()

	_activity_types = db.session.execute(
		db.select(DBH.ActivityType).order_by(DBH.ActivityType.name)
	).scalars().all()

	return render_template(
		"maps.html",
		athletes=_athletes,
		activity_types=_activity_types)

@app.route("/animations")
def animations():
	_athletes = db.session.execute(
		db.select(DBH.Athlete).order_by(DBH.Athlete.name)
	).scalars().all()

	_activity_types = db.session.execute(
		db.select(DBH.ActivityType).order_by(DBH.ActivityType.name)
	).scalars().all()

	return render_template(
		"animations.html",
		athletes=_athletes,
		activity_types=_activity_types)

@app.route("/api/add_athlete", methods=["POST"])
def add_athlete():
	athlete_name = request.get_json().get("name", "")
	DBH.add_athlete(athlete_name)
	return {
		"status": "ok"
	}

@app.route("/api/delete_athletes", methods=["POST"])
def delete_athletes():
	athlete_ids = request.get_json().get("athlete_ids", "")
	DBH.delete_athletes(athlete_ids)
	return {
		"status": "ok"
	}

@app.route("/api/delete_types", methods=["POST"])
def delete_types():
	activity_type_ids = request.get_json().get("activity_type_ids", "")
	DBH.delete_types(activity_type_ids)
	return {
		"status": "ok"
	}

@app.route("/api/delete_activities", methods=["POST"])
def delete_activities():
	activity_ids = request.get_json().get("activity_ids", "")
	DBH.delete_activities(activity_ids)
	return {
		"status": "ok"
	}

@app.route("/api/rename_activities", methods=["POST"])
def rename_activities():
	print ("rename_activities")
	data = request.get_json()
	activity_ids = data.get("activity_ids", "")
	new_name = data.get("new_name", "")
	print ("ids:", activity_ids)
	print ("new name:", new_name)
	DBH.rename_activities(activity_ids, new_name)
	return {
		"status": "ok"
	}

def get_activities_from_query(data, consider_gps):
	athlete_ids = data.get("athlete_ids", "")
	type_ids = data.get("type_ids", "")
	date_min = data.get("date_min", "")
	date_max = data.get("date_max", "")
	use_unkown_date = data.get("use_unkown_date", "")

	activities_from_db = get_activities_by_(athlete_ids, type_ids, date_min, date_max, use_unkown_date)
	activities = [activity.to_dict for activity in activities_from_db]

	if consider_gps:
		ref_lat = float(data.get("lat", ""))
		ref_lon = float(data.get("lon", ""))
		ref_range = float(data.get("range", ""))
		activities_dict = []
		for activity in activities:
			if check_gps_range(activity["start_latitude"], activity["start_longitude"], ref_lat, ref_lon, ref_range):
				activities_dict.append(activity)
	else:
		activities_dict = activities

	return activities_dict

@app.route("/api/get_activities_table", methods=["POST"])
def get_activities_table():
	data = request.get_json()
	activities_dict = get_activities_from_query(data, data.get("consider_gps", ""))

	return render_template(
		"components/activity_table.html",
		activities = activities_dict,
		addselectioncheckbox = data.get("add_checkbox", ""),
		defaultchecked = data.get("default_checked", "")
	)

@app.route("/api/get_activities", methods=["POST"])
def get_activities():
	data = request.get_json()
	activities = get_activities_from_query(data, False)
	return jsonify(activities)

@app.route("/api/get_activities_at_coordinate", methods=["POST"])
def get_activities_at_coordinate():
	data = request.get_json()
	activities = get_activities_from_query(data, True)
	return jsonify(activities)

@app.route("/api/uploadGPX", methods=["POST"])
def upload_gpx():
	files = request.files.getlist("files")
	athlete_id = request.form["athlete_id"]

	for file in files:
		# get metadata:
		file_metadata = get_metadata_from_file(file, True)
		# copy file to local folder:
		new_filename = str(athlete_id)+"_"+file_metadata["type"]+"_"+file_metadata["datetime"]+".gpx"
		target_filepath = os.path.join(GPX_DIR, new_filename)
		# save file at destination:
		file.seek(0)
		file.save(target_filepath)

		DBH.add_activity(target_filepath, athlete_id=athlete_id)

	return {
		"status": "ok"
	}

@app.route("/api/get_all_athletes_from_db", methods=["POST"])
def get_all_athletes_from_db():
	return jsonify(DBH.get_all_athletes())

@app.route("/api/get_all_types_from_db", methods=["POST"])
def get_all_activitytypes_from_db():
	return jsonify(DBH.get_all_activitytypes())

@app.route("/api/runTourAnimation", methods=["POST"])
def run_TourAnimation():
	global current_job
	current_computation = "TourAnimation"
	data = request.get_json()
	activity_ids = data.get("activity_ids", "")

	filepath = db.session.execute(
		db.select(DBH.Activity.filepath)
			.where(DBH.Activity.id == activity_ids[0])
	).scalar_one_or_none()

	aim_ta.set_full_filepath(filepath)
	aim_ta.set_zoom(data.get("mapzoom",""))
	aim_ta.set_filename_prefix(data.get("filename", ""))
	
	current_job = aim_ta
	current_job.start_progress()
	thread = threading.Thread(target=aim_ta.run_animation_builder)
	thread.start()
	return jsonify({
		"current_task": "TourAnimation",
		"current_status": "started",
		"total_progress": 0
	})

@app.route("/api/runMapPlotter", methods=["POST"])
def run_MapPlotter():
	global current_job
	current_computation = "MapPlotter"
	data = request.get_json()

	activity_ids = data.get("activity_ids", "")
	ref_lat = data.get("lat", "")
	ref_lon = data.get("lon", "")
	mapzoom = data.get("mapzoom", "")
	filename = data.get("filename", "")

	if not isinstance(ref_lat, float) or not isinstance(ref_lon, float):
		current_job = SubTask.SubTask("Error: no map reference point specified!")
		current_job.error = True
		return jsonify({
			"current_task": "Error: no map reference point specified!",
			"current_status": "stopped",
			"total_progress": 0
		})
	
	aim_rmap.set_activities(get_activities_by_ids(activity_ids))
	aim_rmap.set_reference_area(float(ref_lat), float(ref_lon))
	aim_rmap.set_zoom(int(mapzoom))
	aim_rmap.set_filename_prefix(filename)
	
	current_job = aim_rmap
	current_job.start_progress()
	thread = threading.Thread(target=aim_rmap.run_plotter)
	thread.start()
	return jsonify({
		"current_task": "MapPlotter",
		"current_status": "started",
		"total_progress": 0
	})

@app.route("/api/runDataPlotter", methods=["POST"])
def run_DataPlotter():
	global current_job
	current_computation = "DataPlotter"
	data = request.get_json()
	activity_ids = data.get("activity_ids", "")
	axis_x = data.get("axis_x", "")
	axis_y = data.get("axis_y", "")
	filename = data.get("filename", "")

	aim_ad.set_activities(get_activities_by_ids(activity_ids))
	aim_ad.set_key_x(axis_x)
	aim_ad.set_key_y(axis_y)
	aim_ad.set_filename_prefix(filename)

	current_job = aim_ad
	current_job.start_progress()
	thread = threading.Thread(target=aim_ad.run_plotter)
	thread.start()
	return jsonify({
		"current_task": "DataPlotter",
		"current_status": "started",
		"total_progress": 0
	})

@app.route("/api/progress")
def get_computation_progress():
	global current_job
	if current_job is not None:
		print ("CURRENT JOB: "+str(current_job.get_current_taskname()))
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
	global current_job
	if current_job is not None:
		filepath = current_job.outputfilepath
	else:
		filepath = "unknown"

	return jsonify({
		"result_filename": filepath
		})

@app.route("/output/<path:filename>")
def return_img_filepath(filename):
	return send_from_directory("output", filename)

# Server starten
if __name__ == "__main__":
	# init database:
	with app.app_context():
		db.create_all()
	# run app:
	app.run(debug=True)