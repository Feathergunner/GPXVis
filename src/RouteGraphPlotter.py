#!usr/bin/python
# -*- coding: utf-8 -*-import string

import os
from matplotlib import pyplot as plt
from PIL import Image

from src import OSMMapDownloader as osmmd
from src import RouteGraph as RG
from src.SubTask import SubTask

from src.misc import ensure_dir_exists
from org import GPX_DIR, GPX_DIR_TEST, LAT_HOME, LON_HOME

LINEWIDTH = 1
LINECOLORS = ["red", "blue", "green", "magenta"]

class RouteGraphPlotter(SubTask):
	def __init__(self, routegraphs:list[RG.RouteGraph], zoom:int, add_border:bool=True, dpi:int=200):
		self.routegraphs = routegraphs

		self.zoom = zoom
		self.add_border = add_border
		self.dpi = dpi
		super().__init__("RouteGraphPlotter", len(self.routegraphs)+2)

		# gps and maptile stats:
		self.lon_min = None
		self.lon_max = None
		self.lat_min = None
		self.lat_max = None
		self.tile_x_min = None
		self.tile_x_max = None
		self.tile_y_min = None
		self.tile_y_max = None
		self.tile_x_range = None
		self.tile_y_range = None
		self.lon_mintile = None
		self.lon_maxtile = None
		self.lat_mintile = None
		self.lat_maxtile = None
		self.tile_lat_range = None
		self.tile_lon_range = None

	def construct_filename(self, basename:str, suffix:str="") -> str:
		filename = basename+"_"+str(self.zoom)
		if len(suffix) > 0:
			filename += "_"+suffix
		return filename

	### PLOT GRAPH ON MAP:

	def _construct_gps_stats(self) -> None:
		'''
		Computes all stats required for plotting the gpx data onto a map.
		'''
		# get min/max lon/lat from all nodes:
		for rg in self.routegraphs:
			if len(rg.nodes) == 0:
				# skip if this rg is empty
				continue
			for node_id in rg.nodes:
				node_lat = rg.nodes[node_id].get_latitude()
				node_lon = rg.nodes[node_id].get_longitude()
				if self.lon_min is None or self.lon_min > node_lon:
					self.lon_min = node_lon
				if self.lon_max is None or self.lon_max < node_lon:
					self.lon_max = node_lon
				if self.lat_min is None or self.lat_min > node_lat:
					self.lat_min = node_lat
				if self.lat_max is None or self.lat_max < node_lat:
					self.lat_max = node_lat
	
			# get min/max tile coordinates:
			self.tile_x_min, self.tile_y_min = osmmd.latlong_to_merccoords(self.lat_min, self.lon_min, self.zoom)
			self.tile_x_max, self.tile_y_max = osmmd.latlong_to_merccoords(self.lat_max, self.lon_max, self.zoom)
			self.tile_x_max += 1
			self.tile_y_min += 1
			if self.add_border:
				self.tile_x_min -= 1
				self.tile_x_max += 1
				self.tile_y_min += 1
				self.tile_y_max -= 1
	
			# compute tile ranges:
			(self.lat_mintile, self.lon_mintile) = osmmd.tile_xy_to_latlon(self.tile_x_min, self.tile_y_min, self.zoom)
			(self.lat_maxtile, self.lon_maxtile) = osmmd.tile_xy_to_latlon(self.tile_x_max, self.tile_y_max, self.zoom)
			self.tile_lat_range = self.lat_maxtile - self.lat_mintile
			self.tile_lon_range = self.lon_maxtile - self.lon_mintile
			self.tile_x_range = self.tile_x_max - self.tile_x_min
			self.tile_y_range = self.tile_y_max - self.tile_y_min

	def _construct_map(self) -> None:
		# prepare stats:
		self._construct_gps_stats()
		# get map:
		mapdownloader = osmmd.OSMMapDownloader(self.lat_min, self.lat_max, self.lon_min, self.lon_max, zoom=self.zoom, add_border=self.add_border)
		self.add_task_child(mapdownloader)

		try:
			#self.current_computation_description = "Downloading map"
			mapdownloader.get_map()
			mapimage = Image.open(mapdownloader.filepath)
		
			# set up figure:
			#self.current_computation_description = "Set up map image"
			im_x, im_y = mapimage.size
			width_inches = im_x / (self.dpi)
			height_inches = im_y / (self.dpi)
			plt.figure(figsize=(width_inches, height_inches))
		
			# plot map:
			plt.imshow(mapimage)
		except FileNotFoundError:
			print ("no map image. plot route graph without map.")

	def _get_node_xy_coords(self, rg:RG.RouteGraph, node_id:int) -> tuple:
		'''	
		constructs (x,y)-coords from a node's gps-datapoint, ready for lineplot
		'''
		x = None
		y = None
		node_lat = rg.nodes[node_id].get_latitude()
		node_lon = rg.nodes[node_id].get_longitude()
		
		if node_lat is not None and node_lon is not None:
			# compute pixel offsets:
			# compute distance in full tiles from (0,0) on image:
			relx = (node_lon-self.lon_mintile)/self.tile_lon_range
			rely = ((node_lat-self.lat_mintile)/self.tile_lat_range)-1
			# compute absolute pixel distances, consider 1-tile-border:
			x = relx*(osmmd.MAP_DIM_TILE*self.tile_x_range)
			y = rely*(osmmd.MAP_DIM_TILE*self.tile_y_range)
		return (x, y)

	def _plot_routegraph(self, rg:RG.RouteGraph, color:str, linewidth:int, offset:int=0) -> None:
		print ("plot routegraph with color:", color, "and offset:", offset)
		# plot routes:
		for edge_id in rg.edges:
			xs = []
			ys = []
			incident_nodes = rg.edges[edge_id].get_node_list()
			for n_id in incident_nodes:
				(x,y) = self._get_node_xy_coords(rg, n_id)
				xs.append(x+offset)
				ys.append(y+offset)
			plt.plot(xs, ys, c=color, linewidth=linewidth)
	
		plt.tight_layout()
		plt.axis('off')

	def plot(self, result_filename=None) -> str:
		#self.current_computation_step = "Construct map"
		self._construct_map()
		self.progress += 1
		i = 0
		for rg in self.routegraphs:
			self.current_computation_step = "Plot route "+str(i+1)+" of "+str(len(self.routegraphs))
			color = LINECOLORS[i]
			self._plot_routegraph(rg, color=LINECOLORS[i], linewidth=LINEWIDTH, offset=i)
			i += 1
			self.progress += 1

		if result_filename is None:
			plt.show()
			outputpath = None
		else:
			self.current_computation_step = "Save file"
			# ensure filename ends with ".png"
			if not result_filename.endswith(".png"):
				result_filename = result_filename.split(".")[0]+".png"
			# save plot
			ensure_dir_exists(os.path.join("output","maps"))
			outputpath = os.path.join("output","maps",result_filename)
			plt.savefig(outputpath, bbox_inches='tight', pad_inches=0, dpi=self.dpi)
			print ("Saved map image with routes in: "+outputpath)
			plt.close('all')
		self.finish_progress()
		return outputpath

def plot_routegraph(rg:RG.RouteGraph, map_zoom:int=10, add_border:bool=True, filename_suffix:str="", write_to_file:bool=True):
	print ("Plot RouteGraph...")
	rgp = RouteGraphPlotter([rg], map_zoom, add_border)
	if write_to_file:
		filename = rgp.construct_filename(rg.basename, filename_suffix)
	else:
		filename = None
	rgp.plot(result_filename=filename)
	return filename

#def plot_multiple_graphs(gpx_dirs:list, activity_type:str, lat_ref:float=LAT_HOME, lon_ref:float=LON_HOME, delta_km:float=5, dist_cutoff_km:int=None, min_date:str=None, max_date:str=None, map_zoom:int=10):

if __name__ == '__main__':
	test = False

	simplify = True
	plot_nx = False
	# run example:
	# specify some dates:
	date_min = "2026-05-15"#"2019-01-01"
	date_max = None#"2026-04-01"

	type = "running" # running, hiking, cycling, Unknown
	filename_suffix = ""#"leutra"
	zoom = 14

	if test:
		dist_cutoff = 1
		add_border=False
		gpx_dir = GPX_DIR_TEST
	else:
		add_border = True
		dist_cutoff = None
		gpx_dir = GPX_DIR

	# construct graph:
	rg = RG.construct_routegraph(gpx_dir, type, LAT_HOME, LON_HOME, 5, dist_cutoff, date_min, date_max)
	print ("Constructed graph with",rg.number_of_nodes(),"nodes and",rg.number_of_edges(),"edges.")

	if test:
		rgp = RouteGraphPlotter([rg], zoom, add_border)
		rgp.plot(None)
	else:
		plot_routegraph(rg, zoom, add_border, filename_suffix)
	