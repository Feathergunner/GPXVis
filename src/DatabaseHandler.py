#!usr/bin/python
# -*- coding: utf-8 -*-import string

import datetime
from src.misc import construct_pace_string, construct_speed_string

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_

from src.misc import format_time_hours
from src.misc_files import get_metadata_from_file

db = SQLAlchemy()

class Athlete(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String, nullable=False, unique=True)

class ActivityType(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String, nullable=False, unique=True)

class Activity(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	activitytype_id = db.Column(db.Integer, db.ForeignKey(ActivityType.id),nullable=False)
	athlete_id = db.Column(db.Integer, db.ForeignKey(Athlete.id),nullable=False)
	name = db.Column(db.String)
	filepath = db.Column(db.String,nullable=False)
	datetime = db.Column(db.DateTime, nullable=True)
	distance = db.Column(db.Float)
	duration = db.Column(db.Float)
	elevation = db.Column(db.Float)
	start_latitude = db.Column(db.Float)
	start_longitude = db.Column(db.Float)

	@property
	def to_dict(self):
		actdict = {
			"id" : self.id,
			"activitytype_id" : self.activitytype_id,
			"athlete_id" : self.athlete_id,
			"name" : self.name,
			"filepath" : self.filepath,
			"datetime" : self.datetime,
			"distance" : round(self.distance),
			"duration" : self.duration,
			"elevation" : round(self.elevation),
			"start_latitude" : self.start_latitude,
			"start_longitude" : self.start_longitude,
			# pre-formatted data:
			"type_name" : db.session.execute(db.select(ActivityType).filter_by(id=self.activitytype_id)).scalar_one_or_none().name,
			"athlete_name" : db.session.execute(db.select(Athlete).filter_by(id=self.athlete_id)).scalar_one_or_none().name,
			"distance_km" : round(self.distance/1000,1),
			"duration_hms" : "--",
			"speed" : "--", # speed in km/h
			"pace" : "--", # pace in min/km
			"date" : "unknown",
			"time" : "unknown",
			"startpos_str" : f"({self.start_latitude:.3f},{self.start_longitude:.3f})"
		}
		if self.datetime is not None:
			date = self.datetime.date()
			actdict["date"] = f"{date.day:02d}.{date.month:02d}.{date.year:d}"
			time = self.datetime.time()
			actdict["time"] = f"{time.hour:02d}:{time.minute:02d}"
		if self.duration > 0:
			actdict["duration_hms"] = format_time_hours(self.duration, include_seconds=True)
			actdict["speed"] = construct_speed_string(self.duration, self.distance)
			actdict["pace"] = construct_pace_string(self.duration, self.distance)
		return actdict

def add_athlete(name:str):
	existing_athlete = db.session.execute(db.select(Athlete).filter_by(name=name)).scalar_one_or_none()

	if existing_athlete is None:
		athlete = Athlete(name=name)
		db.session.add(athlete)
		db.session.commit()
		#print("New Athlet",name,"added to DB.")
	else:
		print("Error: Athlete with name:",name,"already exists.")

def add_activitytype(name:str):
	existing_activitytype = db.session.execute(db.select(ActivityType).filter_by(name=name)).scalar_one_or_none()

	if existing_activitytype is None:
		activity = ActivityType(name=name)
		db.session.add(activity)
		db.session.commit()
		print("New ActivityType",name,"added to DB.")
	else:
		print("Error: ActivityType with name:",name,"already exists.")

def add_activity(filepath, activity_type_name:str=None, athlete_id:int=None, athlete_name:str=""):
	# check if athlete is in db & get id:
	athlete = None
	if athlete_id is not None:
		athlete = Athlete.query.filter_by(id=athlete_id).first()
	else:
		athlete = Athlete.query.filter_by(name=athlete_name).first()
	if athlete is None:
		athlete = Athlete(name=athlete_name)
		db.session.add(athlete)
		db.session.flush()
	#print ("Athlete is",athlete.name,"(",athlete.id,")")

	# get metadata from parsed file:
	with open(filepath, 'r') as activityfile:
		metadata = get_metadata_from_file(activityfile, True)

	# check if activity_type is in db & get id:
	if activity_type_name is None:
		activity_type_name = metadata["type"]
	activitytype = ActivityType.query.filter_by(name=activity_type_name).first()
	if activitytype is None:
		activitytype = ActivityType(name = activity_type_name)
		db.session.add(activitytype)
		db.session.flush()
	#print ("Type is",activitytype.name,"(",activitytype.id,")")

	_datetime = None
	if not metadata["datetime"] == "unknown":
		_datetime = datetime.datetime.fromisoformat(metadata["datetime"])

	# build database entry:
	new_activity = Activity(
		activitytype_id = activitytype.id,
		athlete_id = athlete.id,
		name = metadata["name"],
		filepath = filepath,
		datetime = _datetime,
		distance = metadata["total distance"],
		duration = metadata["total duration"].total_seconds(),
		elevation = metadata["total elevation"],
		start_latitude = metadata["lat"],
		start_longitude = metadata["lon"])
	db.session.add(new_activity)
	db.session.commit()

def get_all_athletes():
	athletes = db.session.execute(db.select(Athlete).order_by(Athlete.id)).scalars()
	return [{"id": athlete.id, "name":athlete.name} for athlete in athletes]

def get_all_activitytypes():
	types = db.session.execute(db.select(ActivityType).order_by(ActivityType.id)).scalars()
	return [{"id": type.id, "name":type.name} for type in types]

def get_activities_by_ids(activity_ids:list):
	activities = db.session.execute(db.select(Activity).where(Activity.id.in_(activity_ids))).scalars().all()
	return activities

def get_activities_by_(
		athlete_ids:list = None,
		activitytype_ids:list = None,
		date_min:datetime.datetime = None,
		date_max:datetime.datetime = None,
		use_unkown_date:bool = False):
	'''
	Gets specified activities from database.
	if athlete_ids is None, all athletes are considered
	if activitytype_ids is None, all activity_types are considered
	'''
	query = db.select(Activity)

	# restrict by acthlte:
	if athlete_ids is not None:
		query = query.where(
			Activity.athlete_id.in_(athlete_ids))

	# restrict by activitytype:
	if activitytype_ids is not None:
		query = query.where(
			Activity.activitytype_id.in_(activitytype_ids))

	# restrict by date:
	if use_unkown_date:
		query = query.where(or_(
			Activity.datetime.is_(None),
			Activity.datetime >= date_min, Activity.datetime < date_max))
	else:
		query = query.where(
			Activity.datetime >= date_min, Activity.datetime < date_max)
	activities = db.session.execute(query.order_by(Activity.datetime)).scalars().all()
	return activities

def update_activity_name(activity_id:int, new_name:str):
	activity = db.session.execute(db.select(Activity).where(Activity.id == activity_ids)).scalar_one_or_none()
	if activity is None:
		# todo: raise exception
		return
	activity.name = new_name
	session.commit()


def test_db():
	print ("\n #### run test_db ####\n")
	#add_activitytype("Biking")
	#add_activitytype("Hiking")
	#add_athlete("Ango")
	#add_athlete("Tester")

	debug_print_all()

def debug_print_all():
	print ("Activity types:")
	all_activities = get_all_activitytypes()
	for act in all_activities:
		print (act["id"],":",act["name"])

	print ("Athletes:")
	athletes = get_all_athletes()
	for ath in athletes:
		print (ath["id"],":",ath["name"])

	print ("Activities:")
	activities = db.session.execute(db.select(Activity).order_by(Activity.id)).scalars()
	print (["id: "+str(act.id)+", path: "+str(act.filepath) for act in activities])