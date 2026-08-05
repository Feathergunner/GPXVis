#!usr/bin/python
# -*- coding: utf-8 -*-import string

import io
import os
import numpy as np
from matplotlib import pyplot as plt
import matplotlib as mpl
from PIL import Image

from src import OSMMapDownloader as osmmd
from src import TourGraph as TG
from src.SubTask import SubTask

from src.misc import ensure_dir_exists
from org import GPX_DIR, GPX_DIR_TEST, LAT_HOME, LON_HOME

LINEWIDTH = 1
LINECOLORS = ["red", "blue", "green", "magenta"]
VALID_COLOR_AXIS_KEYS = ["distance", "time", "speed", "elevation_change", "elevation_avg"]


class TourGraphPlotter(SubTask):
	def __init__(self, tourgraphs:list[TG.TourGraph], zoom:int, add_border:bool=True, dpi:int=10):
		self.tourgraphs = tourgraphs

		self.zoom = zoom
		self.add_border = add_border
		self.dpi = dpi
		super().__init__("TourGraphPlotter", len(self.tourgraphs)+2)

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
		filename = "Tour-"+basename+"_"+str(self.zoom)
		if len(suffix) > 0:
			filename += "_"+suffix
		return filename

	### PLOT GRAPH ON MAP:

	def _construct_gps_stats(self) -> None:
		'''
		Computes all stats required for plotting the gpx data onto a map.
		'''
		# get min/max lon/lat from all nodes:
		for tg in self.tourgraphs:
			if len(tg.nodes) == 0:
				# skip if this rg is empty
				continue
			for node in tg.nodes:
				node_lat = node.get_latitude()
				node_lon = node.get_longitude()
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
			mapdownloader.get_map()
			mapimage = Image.open(mapdownloader.filepath)
		
			# set up figure:
			im_x, im_y = mapimage.size
			width_inches = im_x / (self.dpi)
			height_inches = im_y / (self.dpi)
			#print ("map figure dimensions:",width_inches,height_inches)
			self.figure = plt.figure(figsize=(width_inches, height_inches), dpi=self.dpi)
		
			# plot map:
			plt.tight_layout()
			plt.axis('off')
			plt.imshow(mapimage)

			#size = self.figure.get_size_inches()*self.figure.dpi
			#print ("size in pixel and dpi of map:", size, self.figure.dpi)
		except FileNotFoundError:
			print ("no map image. plot route graph without map.")

	def _get_node_xy_coords(self, tg:TG.TourGraph, node_id:int) -> tuple:
		'''	
		constructs (x,y)-coords from a node's gps-datapoint, ready for lineplot
		'''
		x = None
		y = None
		node_lat = tg.nodes[node_id].get_latitude()
		node_lon = tg.nodes[node_id].get_longitude()
		
		if node_lat is not None and node_lon is not None:
			# compute pixel offsets:
			# compute distance in full tiles from (0,0) on image:
			relx = (node_lon-self.lon_mintile)/self.tile_lon_range
			rely = ((node_lat-self.lat_mintile)/self.tile_lat_range)-1
			# compute absolute pixel distances, consider 1-tile-border:
			x = relx*(osmmd.MAP_DIM_TILE*self.tile_x_range)
			y = rely*(osmmd.MAP_DIM_TILE*self.tile_y_range)
		return (x, y)

	def _plot_tourgraph(self, tg:TG.TourGraph, split_type:str="distance", split_size:int=100, color_axis_key:str=None, create_animation:bool=False, filename:str=None) -> None:
		print ("plot tourgraph with color_axis:", color_axis_key)

		if split_type not in ["distance", "time"]:
			raise ValueError("split_type has to be one of \"distance\", \"time\"!")
		if color_axis_key is not None and color_axis_key not in VALID_COLOR_AXIS_KEYS:
			raise ValueError("color_axis_key has to be \'None\' or one of: "+str(VALID_COLOR_AXIS_KEYS)+"!")	
		if create_animation:
			ensure_dir_exists(os.path.join("output","maps","animate_tmp"))

		if filename is None:
			filename = "tmp"

		# construct splits:
		splits = []
		if split_type == "distance":
			splits = tg.get_split_segments(splitdistance=split_size)
		elif split_type == "time":
			splits = tg.get_split_segments(splittime=split_size)

		# get range of colors to construct colormap
		if color_axis_key is not None:
			# normalize color-values:
			min_colorval = min(split[color_axis_key] for split in splits)
			max_colorval = max(split[color_axis_key] for split in splits)
			# compute color values:
			splitcolorvals = [(split[color_axis_key]-min_colorval)/(max_colorval-min_colorval+1) for split in splits]
		#else:
		#	splitcolorvals = ["red" * len(splits)]

		# plot:
		dim_cropped = 512
		figure_size_inches = self.figure.get_size_inches()
		#print ("size in pixel and dpi of map:", figure_size_inches*self.figure.dpi, self.figure.dpi)
		if create_animation:
			# resize figure to cropped:
			self.figure.set_size_inches(dim_cropped/self.figure.dpi, dim_cropped/self.figure.dpi)
			#croppedfigure_size_inches = self.figure.get_size_inches()
			#print ("size in pixel and dpi of cropped image:", croppedfigure_size_inches*self.figure.dpi, self.figure.dpi)
			
		for split_id in range(len(splits)):
			split = splits[split_id]
			xs = []
			ys = []
			for edge in split["edge_ids"]:
				(x,y) = self._get_node_xy_coords(tg, tg.edges[edge].id_begin)
				xs.append(x)
				ys.append(y)
			(x,y) = self._get_node_xy_coords(tg, tg.edges[split["edge_ids"][-1]].id_end)
			xs.append(x)
			ys.append(y)

			if color_axis_key is not None:
				color = mpl.colormaps["turbo"](splitcolorvals[split_id])
			else:
				color = "red"

			#ax.plot(xs, ys, c=color)
			plt.plot(xs, ys, c=color, linewidth=LINEWIDTH*100/self.dpi)

			if create_animation:
				# crop image to current position:
				x_min = int(xs[-1] - dim_cropped/2)
				x_max = int(xs[-1] + dim_cropped/2)
				y_min = int(ys[-1] + dim_cropped/2)
				y_max = int(ys[-1] - dim_cropped/2)
				plt.xlim(x_min, x_max)
				plt.ylim(y_min, y_max)

				# save intermediate image:
				plt.tight_layout()
				plt.axis('off')
				tmp_outputpath = os.path.join("output","maps","animate_tmp", filename+"_"+str(split_id)+".png")
				plt.savefig(tmp_outputpath, bbox_inches='tight', pad_inches=0)#, dpi=self.dpi)

		if create_animation:
			# reset figure size to original map size:
			self.figure.set_size_inches(figure_size_inches)

		plt.tight_layout()
		plt.axis('off')

		if create_animation:
			filepaths = [os.path.join("output","maps","animate_tmp", filename+"_"+str(split_id)+".png") for split_id in range(len(splits))]
			# Create a list of image objects
			image_list = [Image.open(file) for file in filepaths]

			# Save the first image as a GIF file
			image_list[0].save(os.path.join("output", "maps", filename+"_animated.gif"),
			save_all=True,
			append_images=image_list[1:], # append rest of the images
			duration=100, # in milliseconds
			loop=0)


	def plot(self, split_type:str="distance", split_size:int="100", color_axis_key:str=None, create_animation:bool=False, result_filename:str=None) -> str:
		#self.current_computation_step = "Construct map"
		self._construct_map()

		if result_filename is not None:
			if color_axis_key is not None:
				filename_suffix = "_"+color_axis_key
			else:
				filename_suffix = ""
			# ensure filename ends with ".png"
			if not result_filename.endswith(".png"):
				result_filename += filename_suffix
				result_filename_full = result_filename.split(".")[0]+filename_suffix+".png"
			else:
				result_filename = result_filename.split(".")[0]+filename_suffix
				result_filename_full = result_filename+".png"

			# ensure output directory exists:
			ensure_dir_exists(os.path.join("output","maps"))

		self.progress += 1
		i = 0
		for tg in self.tourgraphs:
			self.current_computation_step = "Plot tour "+str(i+1)+" of "+str(len(self.tourgraphs))
			#color = LINECOLORS[i]
			self._plot_tourgraph(tg, split_type=split_type, split_size=split_size, color_axis_key=color_axis_key, create_animation=create_animation, filename=result_filename)
			i += 1
			self.progress += 1

		if result_filename is None:
			plt.show()
			outputpath = None
		else:
			self.current_computation_step = "Save file"
			if create_animation:
				# reset limits in case image was cropped for animation before
				ax = plt.gca()  # get the current axes
				ax.relim()      # make sure all the data fits
				ax.autoscale()
			# save plot
			outputpath = os.path.join("output","maps",result_filename)
			plt.savefig(outputpath, bbox_inches='tight', pad_inches=0)#, dpi=self.dpi)
			print ("Saved map image with routes in: "+outputpath)
			plt.close('all')

		self.finish_progress()
		return outputpath
