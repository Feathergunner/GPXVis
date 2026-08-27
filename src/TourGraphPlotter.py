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

from src.misc import ensure_dir_exists, format_time, format_time_hours
from org import GPX_DIR, GPX_DIR_TEST, LAT_HOME, LON_HOME

LINEWIDTH = 1
LINECOLORS = ["red", "blue", "green", "magenta"]
VALID_COLOR_AXIS_KEYS = ["distance", "time", "speed", "elevation_change", "elevation_avg"]

def fig2img(fig):
	"""Convert a Matplotlib figure to a PIL Image and return it"""
	buf = io.BytesIO()
	fig.savefig(buf)
	buf.seek(0)
	img = Image.open(buf)
	return img

class TourGraphPlotter(SubTask):
	def __init__(self, tourgraphs:list[TG.TourGraph], zoom:int, add_border:bool=True, dpi:int=1, add_profile:bool=False):
		self.tourgraphs = tourgraphs

		self.zoom = zoom
		self.add_border = add_border
		self.dpi = dpi
		self.add_profile = add_profile
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

	def _construct_map(self, create_animation:bool=False) -> None:
		# prepare stats:
		self._construct_gps_stats()
		# get list of (lat, lon)-coords of tour (for map construction):
		tourcoords = None
		if create_animation:
			tourcoords = [(node.get_latitude(), node.get_longitude()) for node in self.tourgraphs[0].nodes]
		# get map:
		mapdownloader = osmmd.OSMMapDownloader(self.lat_min, self.lat_max, self.lon_min, self.lon_max, zoom=self.zoom, add_border=self.add_border, route=tourcoords)
		self.add_task_child(mapdownloader)
		try:
			# load map:
			mapdownloader.get_map()
			mapimage = Image.open(mapdownloader.filepath)
			# set up figure:
			im_x, im_y = mapimage.size
			width_inches = im_x / (self.dpi)
			height_inches = im_y / (self.dpi)
			self.figure, self.axes = plt.subplots(figsize=(width_inches, height_inches), dpi=self.dpi)
			self.axes.set_zorder(1)
			self.axes.set_position([0, 0, 1, 1])
			self.axes.set_axis_off()
			# add map image:
			self.axes.imshow(mapimage)
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
		print ("plot tourgraph with splits defined by",split_type,"with size",split_size,"and color_axis:", color_axis_key)

		# list of PIL images that make up the animation:
		animation_frames = []

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

		# plot:
		dim_cropped = 512
		figure_size_inches = self.figure.get_size_inches()

		# init plot:
		if color_axis_key is not None:
			color = mpl.colormaps["turbo"](splitcolorvals[split_id])
		else:
			color = "red"
		line, = self.axes.plot([], [], c=color, linewidth=LINEWIDTH*100/self.dpi)
		xs = []
		ys = []

		if create_animation:
			# resize figure to cropped:
			self.figure.set_size_inches(dim_cropped/self.figure.dpi, dim_cropped/self.figure.dpi)
			# initialize text info box, positioned relative to the image
			textbox = self.axes.text(
				0.03, 0.97,
				"",
				transform=self.axes.transAxes,
				fontsize=720,
				verticalalignment="top",
				bbox=dict(
					boxstyle="round,pad=0.3",
					facecolor="white",
					edgecolor="black",
					alpha=0.7
				)
			)

		# add height profile:
		if create_animation or self.add_profile:
			self.axis_profile = self.figure.add_axes([0.02, 0.02, 0.96, 0.2], zorder=10, facecolor="white")
			# compute dimensions and limits of profile plots:
			total_dist = sum([split["distance"] for split in splits])
			self.axis_profile.set_xlim([-total_dist*0.01,total_dist*1.01])
			min_elevation = min([split["elevation_avg"] for split in splits])
			max_elevation = max([split["elevation_avg"] for split in splits])
			delta_elevation = max_elevation-min_elevation
			self.axis_profile.set_ylim([min_elevation-0.05*delta_elevation, max_elevation+0.1*delta_elevation])
			min_speed = min([split["speed"] for split in splits])
			max_speed = max([split["speed"] for split in splits])
			delta_speed = max_speed-min_speed
			speed_scale_factor = delta_elevation/delta_speed
	
			self.axis_profile.patch.set_alpha(1.0)
			for spine in self.axis_profile.spines.values():
				spine.set_visible(True)
				spine.set_color("black")
				spine.set_linewidth(LINEWIDTH*100/self.dpi)
			self.axis_profile.set_xticks([])
			self.axis_profile.set_yticks([])
			self.axis_profile.text(
				0.03, 0.95,
				"elevation profile (red) & speed (blue)",
				transform=self.axis_profile.transAxes,
				fontsize=720,
				verticalalignment="top"
			)
			# init line plots for elevation and speed profiles:
			profile_xs = []
			profile_ys_elevation = []
			profile_ys_speed = []
			line_elevation, = self.axis_profile.plot([], [], c="red", linewidth=LINEWIDTH*100/self.dpi)
			line_speed, = self.axis_profile.plot([], [], c="blue", linewidth=LINEWIDTH*100/self.dpi)

		for split_id in range(len(splits)):
			# add next gps-segment to plot:
			split = splits[split_id]
			for edge in split["edge_ids"]:
				(x,y) = self._get_node_xy_coords(tg, tg.edges[edge].id_begin)
				xs.append(x)
				ys.append(y)
			(x,y) = self._get_node_xy_coords(tg, tg.edges[split["edge_ids"][-1]].id_end)
			xs.append(x)
			ys.append(y)
			line.set_data(xs, ys)

			if create_animation or self.add_profile:
				# update elevation and speed profile plots:
				if len(profile_xs) == 0:
					profile_xs.append(split["distance"])
				else:
					profile_xs.append(profile_xs[-1]+split["distance"])
				profile_ys_elevation.append(split["elevation_avg"])
				profile_ys_speed.append((split["speed"]-min_speed)*speed_scale_factor+min_elevation)
				line_elevation.set_data(profile_xs, profile_ys_elevation)
				line_speed.set_data(profile_xs, profile_ys_speed)

			if create_animation:
				# crop image to current position:
				x_min = int(xs[-1] - dim_cropped/2)
				x_max = int(xs[-1] + dim_cropped/2)
				y_min = int(ys[-1] + dim_cropped/2)
				y_max = int(ys[-1] - dim_cropped/2)
				self.axes.set_xlim(x_min, x_max)
				self.axes.set_ylim(y_min, y_max)

				# update text info (time, distance, speed):
				textbox.set_text(format_time(split["time_total"])+" min:sek\n"+f"{split["dist_total"]/1000:03.1f} km\n"+f"{split["speed"]*3600/1000:.1f} km/h")

				# save intermediate image:
				self.axes.set_axis_off()
				# convert pyplot plot to PIL image and store in list of frames:
				animation_frames.append(fig2img(plt.gcf()))

		self.axes.set_axis_off()
		if create_animation:
			# Save the first image as a GIF file
			animation_frames[0].save(
				os.path.join("output", "maps", filename+"_animated.gif"),
				save_all=True,
				append_images=animation_frames[1:], # append rest of the images
				duration=100, # in milliseconds
				loop=0)

	def plot(self, split_type:str="distance", split_size:int="100", color_axis_key:str=None, create_animation:bool=False, result_filename:str=None) -> str:
		#self.current_computation_step = "Construct map"
		self._construct_map(create_animation=create_animation)
		# ensure output directory exists:
		ensure_dir_exists(os.path.join("output","maps"))

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
		
		self.progress += 1
		i = 0
		for tg in self.tourgraphs:
			self.current_computation_step = "Plot tour "+str(i+1)+" of "+str(len(self.tourgraphs))
			self._plot_tourgraph(tg, split_type=split_type, split_size=split_size, color_axis_key=color_axis_key, create_animation=create_animation, filename=result_filename)
			i += 1
			self.progress += 1

		outputpath = None
		if not create_animation:
			if result_filename is None:
				plt.show()
			else:
				# save plot
				self.current_computation_step = "Save file"
				outputpath = os.path.join("output","maps",result_filename)
				plt.savefig(outputpath, bbox_inches='tight', pad_inches=0)#, dpi=self.dpi)
				print ("Saved map image with routes in: "+outputpath)
				plt.close('all')

		self.finish_progress()
		return outputpath
