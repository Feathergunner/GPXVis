#!usr/bin/python
# -*- coding: utf-8 -*-import string

import os

from src import RouteGraph as RG
from src import RouteGraphPlotter as RGP
from src import RouteProfilePlotter as RPP
from src.SubTask import SubTask
from org import GPX_DIR

class AppInputManager(SubTask):
	def __init__(self, taskname:str, taskweight:int):
		self.date_min = None
		self.date_max = None
		self.use_unknown_date = None
		self.gpx_dirs = None
		self.activity_type = None
		self.use_unknown_type = None
		self.line_color = None
		self.filename_prefix = None
		self.outputfilepath = None
		super().__init__(taskname, taskweight)

	def __str__(self):
		retstr = super().__str__()+"\n"
		retstr += "Target Filename: "+str(self.filename_prefix)+"\n"
		retstr += "Date range: ("+str(self.date_min)+" - "+str(self.date_max)+")"
		if self.use_unknown_date:
			retstr += " (also use activities with unknown date)"
		retstr += "\n"
		retstr += "Directories: "+str(self.gpx_dirs)+"\n"
		retstr += "Activity type: "+str(self.activity_type)+"\n"
		retstr += "line_color: "+str(self.line_color)+"\n"
		return retstr

	def set_daterange(self, date_min:str, date_max:str, use_unknown_date:bool):
		self.date_min = date_min
		self.date_max = date_max
		self.use_unknown_date = use_unknown_date

	def set_gpx_dir(self, gpx_dir:str):
		self.gpx_dirs = [gpx_dir]

	def set_gpx_dirs(self, gpx_dirs:list):
		self.gpx_dirs = gpx_dirs

	def set_activity_type(self, activity_type:str, use_unknown_type:bool):
		self.activity_type = activity_type
		self.use_unknown_type = use_unknown_type

	def set_filename_prefix(self, filename:str):
		self.filename_prefix = filename

class AppInputManagerRouteMap(AppInputManager):
	def __init__(self):
		super().__init__("AppInputManagerRouteMap",3)
		self.ref_lat = None
		self.ref_lon = None
		self.range_start = None
		self.map_zoom_lvl = None

	def __str__(self):
		retstr = super().__str__()
		retstr += "Reference Point: ("+str(self.ref_lat)+","+str(self.ref_lon)+")\n"
		retstr += "Maximum distance from reference point: "+str(self.range_start)+"km\n"
		retstr += "Map zoom level: "+str(self.map_zoom_lvl)+"\n"
		return retstr

	def set_reference_area(self, ref_lat:float, ref_lon:float, range_start:float):
		self.ref_lat = ref_lat
		self.ref_lon = ref_lon
		self.range_start = range_start

	def set_zoom(self, map_zoom_lvl:int):
		self.map_zoom_lvl = map_zoom_lvl

	def run_plotter(self):
		routegraphconstructors = []
		for gpx_dir in self.gpx_dirs:
			#full_gpx_path = os.path.join(GPX_DIR, gpx_dir)
			rgc = RG.RouteGraphConstructor(
				gpx_dir = gpx_dir,
				activity_type = self.activity_type,
				lat_ref = self.ref_lat,
				lon_ref = self.ref_lon,
				delta_km = self.range_start,
				date_min = self.date_min,
				date_max = self.date_max,
				use_unknown_date = self.use_unknown_date
				)
			self.add_task_child(rgc)
			routegraphconstructors.append(rgc)
		routegraphs = []
		for rgc in routegraphconstructors:
			rg = rgc.get_routegraph()
			if not rg.is_empty():
				routegraphs.append(rg)
		#print (routegraphs)
		if len(routegraphs) == 0:
			self.outputfilepath = None
			print ("No routes found!")
			self.finish_progress()
			return self.outputfilepath
		rgp = RGP.RouteGraphPlotter(routegraphs, self.map_zoom_lvl)
		self.add_task_child(rgp)
		filename = rgp.construct_filename(routegraphs[0].basename)
		if self.filename_prefix is not None and len(self.filename_prefix) > 0:
			filename = self.filename_prefix+"_"+filename
		self.outputfilepath = rgp.plot(filename)
		print ("outputfilepath: ",self.outputfilepath)
		self.finish_progress()
		return self.outputfilepath

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
		print ("aim_ad.run_plotter()")
		#full_gpx_path = os.path.join(GPX_DIR, self.gpx_dirs[0])
		rpp = RPP.RouteProfilePlotter(self.gpx_dirs[0], self.activity_type, date_min=self.date_min, date_max=self.date_max, use_unknown_date=self.use_unknown_date, verbose=True)
		self.add_task_child(rpp)
		#rpp.load_data()
		rpp.parse_data()
		self.outputfilepath = rpp.plot(self.axis_x_key, self.axis_y_key, basename=self.filename_prefix)
		self.finish_progress()
		return self.outputfilepath
