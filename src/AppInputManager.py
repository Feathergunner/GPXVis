#!usr/bin/python
# -*- coding: utf-8 -*-import string

import os

from src import RouteGraph as RG
from src import TourGraph as TG
from src import RouteGraphPlotter as RGP
from src import RouteProfilePlotter as RPP
from src import TourGraphPlotter as TGP
from src.SubTask import SubTask
from org import GPX_DIR

class AppInputManager(SubTask):
	def __init__(self, taskname:str, taskweight:int):
		self.map_zoom_lvl = None
		self.line_color = None
		self.filename_prefix = None
		self.outputfilepath = None
		super().__init__(taskname, taskweight)

	def __str__(self):
		retstr = super().__str__()+"\n"
		retstr += "Target Filename: "+str(self.filename_prefix)+"\n"
		retstr += "line_color: "+str(self.line_color)+"\n"
		return retstr

	def set_zoom(self, map_zoom_lvl:int):
		self.map_zoom_lvl = map_zoom_lvl

	def set_activities(self, activities:list):
		'''
		activities: list of DBH.Activity
		'''
		self.activities = [activity.to_dict for activity in activities]

	def set_filename_prefix(self, filename:str):
		self.filename_prefix = filename

class AppInputManagerRouteMap(AppInputManager):
	def __init__(self):
		super().__init__("AppInputManagerRouteMap",3)
		self.ref_lat = None
		self.ref_lon = None

	def __str__(self):
		retstr = super().__str__()
		retstr += "Map zoom level: "+str(self.map_zoom_lvl)+"\n"
		return retstr

	def set_reference_area(self, ref_lat:float, ref_lon:float):
		self.ref_lat = ref_lat
		self.ref_lon = ref_lon

	def run_plotter(self):
		# sort activities by athlete:
		activities_by_athlete = {}
		for activity in self.activities:
			athlete_id = activity["athlete_id"]
			if athlete_id not in activities_by_athlete:
				activities_by_athlete[athlete_id] = []
			activities_by_athlete[athlete_id].append(activity)

		# construct a seperate routegraph for each athlete:
		routegraphconstructors = []
		for athlete_id in activities_by_athlete:
			rgc = RG.RouteGraphConstructor(
				activities = activities_by_athlete[athlete_id],
				lat_ref = self.ref_lat,
				lon_ref = self.ref_lon,
				name = activities_by_athlete[athlete_id][0]["type_name"]+"_by_"+activities_by_athlete[athlete_id][0]["athlete_name"]
				)
			self.add_task_child(rgc)
			routegraphconstructors.append(rgc)
		routegraphs = []
		for rgc in routegraphconstructors:
			rg = rgc.get_routegraph()
			if not rg.is_empty():
				routegraphs.append(rg)
		if len(routegraphs) == 0:
			## todo: raise exception
			self.outputfilepath = None
			print ("Error! No routes found!")
			self.finish_progress()
			return self.outputfilepath
		# plot the routegraphs:
		rgp = RGP.RouteGraphPlotter(routegraphs, self.map_zoom_lvl)
		self.add_task_child(rgp)
		filename = rgp.construct_filename("")
		if self.filename_prefix is not None and len(self.filename_prefix) > 0:
			filename = self.filename_prefix+"_"+filename
		self.outputfilepath = rgp.plot(filename)
		self.finish_progress()
		return self.outputfilepath

class AppInputManagerTourAnimation(AppInputManager):
	def __init__(self):
		super().__init__("AppInputManagerTourAnimation",2)
		
	def __str__(self):
		retstr = super().__str__()
		return retstr

	def set_animation_settings(self, speedup:int, fps:int, zoom_in:bool):
		self.speedup = speedup
		self.fps = fps
		self.zoom_in = zoom_in

	def run_animation_builder(self):
		tourgraphs = []
		for activity in self.activities:
			tgc = TG.TourGraphConstructor(activity)
			self.add_task_child(tgc)
			tourgraphs.append(tgc.get_tourgraph())
		
		# plot animation:
		tgp = TGP.TourGraphPlotter(tourgraphs, self.map_zoom_lvl)
		self.add_task_child(tgp)
		tgp.create_tour_animation(split_type="time", split_size=self.speedup//self.fps, fps=self.fps, synchronize_start="no", zoom_in=self.zoom_in, result_filename=self.filename_prefix, add_legend=False)
		self.finish_progress()

class AppInputManagerActivityData(AppInputManager):
	def __init__(self):
		super().__init__("AppInputManagerActivityData",1)
		self.axis_x_key = None
		self.axis_y_key = None
		self.axis_color_key = None

	def __str__(self):
		retstr = super().__str__()
		retstr += "Axis keys: ("+str(self.axis_x_key)+","+str(self.axis_y_key)+")\n"
		return retstr

	def set_key_x(self, key:str):
		self.axis_x_key = key

	def set_key_y(self, key:str):
		self.axis_y_key = key

	def set_key_color(self, key:str):
		self.axis_color_key = key

	def run_plotter(self):
		# plot daragraph of activities:
		rpp = RPP.RouteProfilePlotter(self.activities)
		self.add_task_child(rpp)
		rpp.parse_data()
		self.outputfilepath = rpp.plot(self.axis_x_key, self.axis_y_key, basename=self.filename_prefix)
		self.finish_progress()
		return self.outputfilepath
