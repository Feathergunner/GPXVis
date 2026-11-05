#!usr/bin/python
# -*- coding: utf-8 -*-import string

import src.DatabaseHandler as DBH
import src.TourGraph as TG

def update_records(db):
	all_activitytypes = DBH.get_all_activitytypes()
	all_athletes = DBH.get_all_athletes()
	for activitytype in all_activitytypes:
		# iterate through activity types...
		activity_recordtypes = DBH.get_recordtypes_by_(activitytype["id"])
		activity_recordtypes_ids = [rt.id for  rt in activity_recordtypes]
		for athlete in all_athletes:
			# iterate through athletes...
			all_activities = DBH.get_activities_by_(athlete_ids=[athlete["id"]], activitytype_ids=[activitytype["id"]])
			for activity in all_activities:
				# get recordtypes that exist for this activity:
				all_recordtype_ids = [record.recordtype_id for record in DBH.get_recorddata_by_([activity.id])]
				# find missing records on this specific activity:
				missing_recordtypes = []
				for recordtype in activity_recordtypes:
					if recordtype.id not in all_recordtype_ids and recordtype.distance*1000<activity.distance:
						# recordtype is truly missing
						missing_recordtypes.append(recordtype.id)
				# parse activity and add missing records:
				if len(missing_recordtypes) > 0:
					tgc = TG.TourGraphConstructor(activity.to_dict)
					tg = tgc.get_tourgraph()
					recorddata = tg.get_records([rtype for rtype in activity_recordtypes if rtype.id in missing_recordtypes])
					for recordtype_id in recorddata:
						DBH.add_recorddata(recordtype_id, activity.id, recorddata[recordtype_id][0], recorddata[recordtype_id][1])
