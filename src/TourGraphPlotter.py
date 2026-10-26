#!usr/bin/python
# -*- coding: utf-8 -*-import string

import io
import os
import subprocess
import numpy as np
from matplotlib import pyplot as plt
#from matplotlib.lines import Line2D
import matplotlib as mpl
from PIL import Image, ImageDraw

from src import OSMMapDownloader as osmmd
from src import TourGraph as TG
from src.SubTask import SubTask

from src.misc import ensure_dir_exists, format_time, format_time_hours
from src.misc_geometry import get_latlon_vector_length
from org import GPX_DIR, GPX_DIR_TEST, LAT_HOME, LON_HOME

LINEWIDTH = 1
LINECOLORS = ["red", "blue", "green", "magenta", "orange", "purple", "cyan", "olive", "pink"]
VALID_COLOR_AXIS_KEYS = ["distance", "time", "speed", "elevation_change", "elevation_avg"]


def fig2img(fig):
	"""
	Convert a Matplotlib figure to a PIL Image and return it
	"""
	buf = io.BytesIO()
	fig.savefig(buf)
	buf.seek(0)
	img = Image.open(buf)
	return img

class TourGraphPlotter(SubTask):
	def __init__(self,
			tourgraphs:list[TG.TourGraph],
			zoom:int,
			add_border:bool=True,
			dpi:int=100,
			add_profile:bool=False):
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

		self.filename = "tmp"

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
			for node_id in tg.nodes:
				node = tg.nodes[node_id]
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

	def _construct_map(self, follow_path_only:bool=False) -> None:
		self.current_computation_step = "Construct map"
		# prepare stats:
		self._construct_gps_stats()
		# get list of (lat, lon)-coords of tour (for map construction):
		tourcoords = None
		if follow_path_only:
			tourcoords = [(self.tourgraphs[0].nodes[edge.id_begin].get_latitude(), self.tourgraphs[0].nodes[edge.id_begin].get_longitude()) for edge in self.tourgraphs[0].edges]
		# get map:
		mapdownloader = osmmd.OSMMapDownloader(self.lat_min, self.lat_max, self.lon_min, self.lon_max, zoom=self.zoom, add_border=self.add_border, route=tourcoords)
		self.add_task_child(mapdownloader)
		try:
			# load map:
			mapdownloader.get_map()
			mapimage = Image.open(mapdownloader.filepath)
			# set up figure:
			self.im_pxl_x, self.im_pxl_y = mapimage.size
			width_inches = self.im_pxl_x / (self.dpi)
			height_inches = self.im_pxl_y / (self.dpi)
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

	def _plot_animated_tours_to_mp4(self,
			split_type:str="distance",
			split_size:int=100,
			fps:int=10,
			synchronize_start:str="distance",
			add_legend:bool=False,
			filename:str=None) -> None:
		'''
		Construct animation frames and use ffmpeg to create an mp4 video file
		'''

		ensure_dir_exists(os.path.join("output","animaions"))
		if filename is not None:
			outputpath = os.path.join("output","animaions",filename+".mp4")
		else:
			outputpath = os.path.join("output","animaions",self.filename+".mp4")

		# ffmpeg command with settings:
		cmd = [
			"ffmpeg",
			"-y",
			"-f", "rawvideo",
			"-vcodec", "rawvideo",
			"-pix_fmt", "rgba",
			"-s", f"{self.im_pxl_x}x{self.im_pxl_y}",
			"-r", str(fps),
			"-i", "-",
			"-an",
			"-c:v", "libx264",
			"-pix_fmt", "yuv420p",
			outputpath
		]

		# construct synchronized splits:
		startindices = [0]*len(self.tourgraphs)
		if synchronize_start == "starttime":
			startindices = self._find_common_startindex_by_timestamp()
		elif synchronize_start == "distance":
			startindices = self._find_common_startindex_by_distance()
		tourgraph_splits = []
		for i in range(len(self.tourgraphs)):
			if split_type == "distance":
				tourgraph_splits.append(self.tourgraphs[i].get_split_segments(splitdistance=split_size, offset=startindices[i]))
			elif split_type == "time":
				tourgraph_splits.append(self.tourgraphs[i].get_split_segments(splittime=split_size, offset=startindices[i]))

		# init plot:
		self.axes.set_axis_off()
		figure_size_inches = self.figure.get_size_inches()
		lines = []
		markerpoints = []
		tour_xs = [[] for _ in self.tourgraphs]
		tour_ys = [[] for _ in self.tourgraphs]
		for i in range(len(self.tourgraphs)):
			self.current_computation_step = "Plot tour "+str(i+1)+" of "+str(len(self.tourgraphs))
			line, = self.axes.plot([], [], c=LINECOLORS[i], linewidth=LINEWIDTH*100/self.dpi, zorder=i, label=self.tourgraphs[i].basename)
			point, = self.axes.plot([], [], c=LINECOLORS[i], marker='o', markersize=400/self.dpi, zorder=20+i)
			lines.append(line)
			markerpoints.append(point)

		if add_legend:
			self.axes.legend(handles=lines)
		
		current_split_id = 0
		reached_final_split = False
		with subprocess.Popen(cmd, stdin=subprocess.PIPE) as proc:
			while not reached_final_split:
				reached_final_split = True
				if current_split_id%10 == 0:
					print ("current split:", current_split_id)
				for tour_id in range(len(self.tourgraphs)):
					remaining_splits = False
					tg = self.tourgraphs[tour_id]
					if current_split_id < len(tourgraph_splits[tour_id]):
						remaining_splits = True
						split = tourgraph_splits[tour_id][current_split_id]
						# get start coordinates for every edge in split:
						for edge in split["edge_ids"]:
							(x,y) = self._get_node_xy_coords(tg, tg.edges[edge].id_begin)
							tour_xs[tour_id].append(x)
							tour_ys[tour_id].append(y)
						# get end coordinate for last edge of split:
						(x,y) = self._get_node_xy_coords(tg, tg.edges[split["edge_ids"][-1]].id_end)
						tour_xs[tour_id].append(x)
						tour_ys[tour_id].append(y)
						lines[tour_id].set_data(tour_xs[tour_id], tour_ys[tour_id])
						markerpoints[tour_id].set_data([tour_xs[tour_id][-1]], [tour_ys[tour_id][-1]])
					reached_final_split = reached_final_split and not remaining_splits

				# convert pyplot plot to PIL image:
				frame = fig2img(plt.gcf())
				draw = ImageDraw.Draw(frame)
				# Send the frame directly to FFmpeg
				proc.stdin.write(frame.tobytes())

				current_split_id += 1

		proc.stdin.close()
		return_code = proc.wait()
		if return_code != 0:
			raise RuntimeError(f"FFmpeg exited with code {return_code}")
			
	def _find_common_startindex_by_timestamp(self) -> list[int]:
		'''
		Determines a common start time of all tours, that is,
		finds the earliest timepoint at which all tours are active.

		Returns a list of integers, one for each TourGraph.
		The list specifies the position of the common start time in each TourGraph.
		'''
		print ("!! SYNCHRONIZE BY TIMESTAMP NOT YET IMPLEMENTED !!")
		return [0]*len(self.tourgraphs)

	def _find_common_startindex_by_distance(self, precision:int=5) -> list[int]:
		'''
		Assumes that all TourGraphs follow the same route.
		Determines a common start point of all tours, that is
		finds the earliest point (i.e. GPS-coordinate) that is passed by all tours.
		Returns a list of indices, one for each TourGraph.
		The list specifies the position of the common start point in each TourGraph.

		precision: int
			maximum distance (in meters) for two coordinates to be considered "equal"
			to simplify computation.
		'''
		def get_node_latlon(tg_id, edge_id):
			tg = self.tourgraphs[tg_id]
			lat = tg.nodes[tg.edges[edge_id].id_begin].get_latitude()
			lon = tg.nodes[tg.edges[edge_id].id_begin].get_longitude()
			return (lat, lon)

		def get_distance(tg_id_a, edge_id_a, tg_id_b, edge_id_b):
			(lat_a, lon_a) = get_node_latlon(tg_id_a, edge_id_a)
			(lat_b, lon_b) = get_node_latlon(tg_id_b, edge_id_b)
			return get_latlon_vector_length(lat_a-lat_b, lon_a-lon_b)

		# init list of start edge offsets:
		start_edge_ids = [0]*len(self.tourgraphs)
		current_tg_reference = 1
		while current_tg_reference < len(self.tourgraphs):
			# find start position for tourgraph specified by current_tg_reference
			current_distance = get_distance(0, start_edge_ids[0], current_tg_reference, start_edge_ids[current_tg_reference])
			compare_distance = get_distance(0, start_edge_ids[0], current_tg_reference, start_edge_ids[current_tg_reference]+1)
		
			# test offsetting the tour specified by current_tg_reference, see if distance gets smaller
			while current_distance+0.1 > compare_distance:
				start_edge_ids[current_tg_reference] += 1
				current_distance = compare_distance
				if current_distance < precision:
					# precision is sufficient
					break
				compare_distance = get_distance(0, start_edge_ids[0], current_tg_reference, start_edge_ids[current_tg_reference]+1)

			compare_distance = get_distance(0, start_edge_ids[0]+1, current_tg_reference, start_edge_ids[current_tg_reference])
			# test offsetting first tour
			additional_offset = 0
			while current_distance+0.1 > compare_distance:
				additional_offset += 1
				start_edge_ids[0] += 1
				current_distance = compare_distance
				if current_distance < precision:
					# precision is sufficient
					break
				compare_distance = get_distance(0, start_edge_ids[0]+1, current_tg_reference, start_edge_ids[current_tg_reference])

			# add new offset to all previously checked tours:
			for k in range(1,current_tg_reference):
				start_edge_ids[k] += additional_offset
			current_tg_reference += 1

		return start_edge_ids

	def _plot_tourgraph(self,
			tg:TG.TourGraph,
			split_type:str="distance",
			split_size:int=100,
			color_axis_key:str=None,
			create_animation:bool=False,
			animation_fullmap:bool=False,
			filename:str=None) -> None:
		'''
		Plot a tourgraph with splits defined by split_type with size split_size and colored corresponding to color_axis_key

		create_animation:
			if True, saves every frame of an animated tour
		animation_fullmap:
			if True, the frames contain the full map.
			otherwise, the animation frames show a zoomed-in fraction around the current position.
		'''

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
		point, = self.axes.plot([], [], c=color, marker='o', markersize=400)
		xs = []
		ys = []

		if create_animation:
			if not animation_fullmap:
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
			point.set_data([xs[-1]], [ys[-1]])

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
				if not animation_fullmap:
					# crop image to current position:
					x_min = int(xs[-1] - dim_cropped/2)
					x_max = int(xs[-1] + dim_cropped/2)
					y_min = int(ys[-1] + dim_cropped/2)
					y_max = int(ys[-1] - dim_cropped/2)
					self.axes.set_xlim(x_min, x_max)
					self.axes.set_ylim(y_min, y_max)


				# update text info (time, distance, speed):
				textbox.set_text(format_time(split["time_total"])+" min:sek\n"+f"{split["dist_total"]/1000:03.1f} km\n"+f"{split["speed"]*3600/1000:.1f} km/h")

				# convert pyplot plot to PIL image and store in list of frames:
				self.axes.set_axis_off()
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

	def plot(self,
			split_type:str="distance",
			split_size:int="100",
			color_axis_key:str=None,
			create_animation:bool=False,
			animation_fullmap:bool=False,
			result_filename:str=None) -> str:

		self._construct_map(follow_path_only = create_animation and not animation_fullmap)
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
			self._plot_tourgraph(tg, split_type=split_type, split_size=split_size, color_axis_key=color_axis_key, create_animation=create_animation, animation_fullmap=animation_fullmap, filename=result_filename)
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
				plt.savefig(outputpath, bbox_inches='tight', pad_inches=0)
				plt.close('all')

		self.finish_progress()
		return outputpath

	def create_tour_animation(self,
			split_type:str="distance",
			split_size:int=100,
			fps:int=10,
			synchronize_start:str="no",
			add_legend:bool=True,
			result_filename:str=None):

		if split_type not in ["distance", "time"]:
			raise ValueError("split_type has to be one of \"distance\", \"time\"!")
		if synchronize_start not in ["no", "starttime", "distance"]:
			raise ValueError("synchronize_start has to be one of \"no\", \"starttime\", \"distance\"!")
		
		self._construct_map()

		if result_filename is not None:
			if result_filename.endswith(".png"):
				result_filename = result_filename[:-4]

		self.progress += 1
		self._plot_animated_tours_to_mp4(split_type=split_type, split_size=split_size, fps=fps, synchronize_start=synchronize_start, add_legend=add_legend, filename=result_filename)
