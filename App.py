#!usr/bin/python
# -*- coding: utf-8 -*-import string

import os
import threading
from flask import Flask, render_template, request, jsonify, url_for, send_from_directory
from flask_alembic import Alembic

from src import AppInputManager as AIM
from src import SubTask
from src import RecordUpdater as RU
from src import DatabaseHandler as DBH
from src.DatabaseHandler import db, get_activities_by_, get_activities_by_ids
from src.misc import ensure_dir_exists, check_gps_range
from src.misc_files import get_metadata_from_file

from org import GPX_DIR
from src.org_plotting import AXIS_DIM_CONT, AXIS_DIM_CAT, AXIS_DOM_COLOR

app = Flask(__name__)
# init database:
DB_PATH = "project.db"
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["ALEMBIC_CONTEXT"] = {"render_as_batch": True}

db.init_app(app)

# Initialize Flask-Alembic and run upgrades
alembic = Alembic(app)
with app.app_context():
	alembic.upgrade()

aim_rmap = AIM.AppInputManagerRouteMap()
aim_ta = AIM.AppInputManagerTourAnimation()
aim_ad = AIM.AppInputManagerActivityData()
aim_rd = AIM.AppInputManagerRecordData()

global current_job
current_job = None

# render html:
@app.route("/")
def index():
	return render_template("index.html")

@app.route("/upload")
def upload():
	_athletes = DBH.get_all_athletes()
	_defaults = DBH.get_default_settings()

	return render_template(
		"upload.html",
		athletes=_athletes,
		default_setting=_defaults)

@app.route("/database")
def database():
	_athletes = DBH.get_all_athletes()
	_activity_types = DBH.get_all_activitytypes()
	_defaults = DBH.get_default_settings()

	return render_template(
		"database.html",
		athletes=_athletes,
		activity_types=_activity_types,
		default_setting=_defaults)

@app.route("/statistics")
def statistics():
	_athletes = DBH.get_all_athletes()
	_activity_types = DBH.get_all_activitytypes()
	_defaults = DBH.get_default_settings()

	return render_template(
		"statistics.html",
		athletes=_athletes,
		activity_types=_activity_types,
		axisdim_cont= AXIS_DIM_CONT,
		axisdim_cat=AXIS_DIM_CAT,
		axisdim_color=AXIS_DOM_COLOR,
		default_setting=_defaults)

@app.route("/maps")
def maps():
	_athletes = DBH.get_all_athletes()
	_activity_types = DBH.get_all_activitytypes()
	_defaults = DBH.get_default_settings()

	return render_template(
		"maps.html",
		athletes=_athletes,
		activity_types=_activity_types,
		default_setting=_defaults)

@app.route("/animations")
def animations():
	_athletes = DBH.get_all_athletes()
	_activity_types = DBH.get_all_activitytypes()
	_defaults = DBH.get_default_settings()

	return render_template(
		"animations.html",
		athletes=_athletes,
		activity_types=_activity_types,
		default_setting=_defaults)

@app.route("/records")
def records():
	_activity_types = DBH.get_all_activitytypes()
	_records = DBH.get_recorddata_by_()
	_defaults = DBH.get_default_settings()

	recordtypes_by_acttype = {}
	records_by_type = {}
	for record in _records:
		r_dict = record.to_dict
		if r_dict["activitytype_name"] not in records_by_type:
			records_by_type[r_dict["activitytype_name"]] = {}
			recordtypes_by_acttype[r_dict["activitytype_name"]] = []
		if r_dict["rtype_name"] not in records_by_type[r_dict["activitytype_name"]]:
			records_by_type[r_dict["activitytype_name"]][r_dict["rtype_name"]] = []
			recordtypes_by_acttype[r_dict["activitytype_name"]].append(r_dict["rtype_name"])
		records_by_type[r_dict["activitytype_name"]][r_dict["rtype_name"]].append(r_dict)
	for atype in records_by_type:
		records_by_type[atype] = dict(sorted(records_by_type[atype].items(), key=lambda item: item[1][0]["rtype_distance"]))
	return render_template(
		"records.html",
		activity_types=_activity_types,
		recorddata=records_by_type,
		recordtypes=recordtypes_by_acttype,
		axisdim_cont= AXIS_DIM_CONT,
		axisdim_cat=AXIS_DIM_CAT,
		axisdim_color=AXIS_DOM_COLOR,
		default_setting=_defaults)

@app.route("/settings")
def settings():
	_athletes = DBH.get_all_athletes()
	_activity_types = DBH.get_all_activitytypes()
	_defaults = DBH.get_default_settings()

	return render_template(
		"settings.html",
		athletes=_athletes,
		activity_types=_activity_types,
		default_setting=_defaults)

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
	data = request.get_json()
	activity_ids = data.get("activity_ids", "")
	new_name = data.get("new_name", "")
	DBH.rename_activities(activity_ids, new_name)
	return {
		"status": "ok"
	}

@app.route("/api/update_settings", methods=["POST"])
def update_settings():
	data = request.get_json()
	athlete_ids = data.get("athlete_ids", "")
	type_ids = data.get("type_ids", "")
	ref_lat_raw = data.get("lat", "")
	ref_lon_raw = data.get("lon", "")
	if ref_lat_raw < 0:
		ref_lat = None
	else:
		ref_lat = float(ref_lat_raw)
	if ref_lon_raw < 0:
		ref_lon = None		
	else:
		ref_lon = float(ref_lon_raw)

	if len(athlete_ids) == 0:
		athlete_id = None
	else:
		athlete_id = athlete_ids[0]
	if len(type_ids) == 0:
		type_id = None
	else:
		type_id = type_ids[0]
	min_date = None
	DBH.set_default_settings(athlete_id, type_id, min_date, ref_lat, ref_lon)
	return {"status": "ok"}

@app.route("/api/get_default_map_parameter")
def get_default_map_parameter():
	print ("get default parameters")
	defaults = DBH.get_default_settings()
	return jsonify({
		"default_latitude": defaults["location_latitude"],
		"default_longitude": defaults["location_longitude"]})

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

	activities = db.session.execute(
		db.select(DBH.Activity)
			.where(DBH.Activity.id.in_(activity_ids))
	).scalars().all()

	aim_ta.set_activities(activities)
	aim_ta.set_zoom(data.get("mapzoom", ""))
	aim_ta.set_color_key(data.get("color_key", ""))
	aim_ta.set_animation_settings(int(data.get("animation_speedup", "")), int(data.get("animation_fps", "")), bool(data.get("animation_zoom_in", "")))
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
	aim_ad.set_color_key(data.get("color_key", ""))
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

@app.route("/api/runRecordPlotter", methods=["POST"])
def run_RecordPlotter():
	global current_job
	data = request.get_json()
	recorddata_ids = data.get("recorddata_ids", "")
	axis_key_x = data.get("axis_x", "")
	axis_key_y = data.get("axis_y", "")
	key_color = data.get("color_key", "")
	filename = data.get("filename", "")

	records_and_activities = DBH.get_recorddata_and_activity_by_record_ids(recorddata_ids)
	records = [rec_and_act[0] for rec_and_act in records_and_activities]
	activities = [rec_and_act[1] for rec_and_act in records_and_activities]
	timeframe_starts = [record.starttime for record in records]
	timeframe_ends = [record.starttime+record.time for record in records]

	aim_rd.set_activities(activities)
	aim_rd.set_timeframes(timeframe_starts, timeframe_ends)
	aim_rd.set_key_x(axis_key_x)
	aim_rd.set_key_y(axis_key_y)
	aim_rd.set_color_key(key_color)
	aim_rd.set_filename_prefix(filename)

	current_job = aim_rd
	current_job.start_progress()
	thread = threading.Thread(target=aim_rd.run_plotter)
	thread.start()
	return jsonify({
		"current_task": "DataPlotter",
		"current_status": "started",
		"total_progress": 0
	})

@app.route("/api/create_record_category", methods=["POST"])
def create_record_category():
	data = request.get_json()
	for activity_type in data.get("recordActivityType", ""):
		DBH.add_recordtype(
			activity_type,
			data.get("recordDistance", ""),
			data.get("recordName", ""))
	return {
		"status": "ok"
	}

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

# start server
if __name__ == "__main__":
	# run app:
	with app.app_context():
		# print database stats to console
		DBH.get_stats()
		#db.session.query(DBH.RecordData).delete()
		#db.session.commit()
		updater = RU.RecordUpdater(db)
		updater.update_records()
	app.run(debug=False)