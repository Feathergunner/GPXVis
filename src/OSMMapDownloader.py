#!usr/bin/python
# -*- coding: utf-8 -*-import string

import os
import math
import urllib.request
from PIL import Image, ImageDraw, ImageFont

from src.SubTask import SubTask

# online source of maptiles:
MAPSERVER:str = "https://tile.openstreetmap.org/"
# dimension of square maptile images:
MAP_DIM_TILE:int = 256

# default values:
MAP_DEFAULT_ZOOM:int = 14
DIR_MAPS:str = "maps"
DIR_TILE_CACHE:str = "tilecache"

# Test/Example: download map of central Berlin
EXAMPLE_LATITUDE = 52.5
EXAMPLE_LONGITUDE = 13.4

def ensure_dir_exists(directory:str):
	if not os.path.exists(directory):
		os.makedirs(directory)

def latlong_to_merccoords(lat:float, lon:float, zoom:int):
	'''
	computes the (x,y)-coordinates of the maptile that covers a (latitude, longitude)-coordinate.
	longitude corresponds to x, and latitude corresponds to y
	but note that y-coordinates are inverse to latitude: with increasing latitude, y decreases.

	maths from https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Derivation_of_tile_names
	'''
	x = int((lon+180)/360 * 2**zoom)
	y = int((1-(math.log(math.tan(lat*(math.pi/180))+(1/(math.cos(lat*(math.pi/180))))))/math.pi)*2**(zoom-1))
	return (x,y)

def tile_xy_to_latlon(x:int, y:int, zoom:int):
	'''
	computes latitude and longitude of (0,0) position on a maptile specified by x,y,zoom.

	maths from https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Derivation_of_tile_names
	'''
	lon = (x/(2**zoom))*360-180
	lat = math.atan(math.sinh(math.pi-(y/2**zoom)*2*math.pi))*(180/math.pi)
	return (lat, lon)


class MapTile:
	'''
	Class to organize maptiles and download tile images from webserver.

		param:x		x-coordinate of tile
		param:y		y-coordinate of tile
		param:zoom	zoom-level of tile

	For explanation of these parameters see:
		https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Derivation_of_tile_names
	'''
	def __init__(self, x:int, y:int, zoom:int):
		self.x:int = x
		self.y:int = y
		self.zoom:int = zoom
		self.name:str = self._construct_tile_name()
		#self.filename:str = self.name+".png"
		self.filepath = os.path.join(DIR_MAPS, DIR_TILE_CACHE, self.name+".png")
		self.filewebpath:str = self._construct_tile_webpath()

	def __str__(self):
		return "tile_z:"+str(self.zoom)+"_x:"+str(self.x)+"_y:"+str(self.y)

	def __repr__(self):
		return str(self)

	def _construct_tile_name(self) -> str:
		'''
		Constructs a unique name for this tile
		'''
		return str(self.zoom)+"-"+str(self.x)+"-"+str(self.y)

	def _construct_tile_webpath(self) -> str:
		'''
		Constructs the filename of this tile on the OSM-server
		'''
		return str(self.zoom)+"/"+str(self.x)+"/"+str(self.y)+".png"

	def check_if_cached(self, cachedir:str=None) -> bool:
		'''
		To run before download.
		Ensures the cache-directory exists and checks if tile-image-file is already present.
		'''
		if cachedir is None:
			cachedir = os.path.join(DIR_MAPS, DIR_TILE_CACHE)
		ensure_dir_exists(cachedir)
		return os.path.isfile(self.filepath)

	def download(self, force_download:bool=False, verbose:bool=False):
		'''
		Downloads the tile from open street map server,
		but only if it is not cached or force_download == True
		'''
		if (not self.check_if_cached()) or force_download:
			fullurl = MAPSERVER+self.filewebpath
			webopener = urllib.request.URLopener()
			webopener.addheader('User-Agent', 'Magic Browser')
			_filename, _headers = webopener.retrieve(fullurl, self.filepath)
			if verbose:
				print ("downloaded",str(self))
		elif verbose:
			print (str(self),"already cached")


class OSMMapDownloader(SubTask):
	def __init__(self, lat_min:int, lat_max:int, lon_min:int, lon_max:int, zoom:int=MAP_DEFAULT_ZOOM, add_border:bool=False, route:list=None):
		'''
		lat_min, lat_max, lon_min, lon_max: range of latitude and longitude to be covered
		zoom: detail level of map. zoom = 0 covers the whole world, maximum is zoom = 19.
			At default zoom level, one pixel of the map represents about approx 10m.
			For more information see https://wiki.openstreetmap.org/wiki/Zoom_levels
		add_border: if set to True, a 1-tile wide border is added to the area.
			This is intended for the case where one wants to make sure the map is big enough,
			this it could happen that the specified lat/lon-coordinates are very close to a tile border
		route: a list of (lat, lon)-coordinates. If route is not None, then ONLY those tiles are downloaded
			that are required for the route (the logic of add_border is applied to each individual tile).
			Therefore the returned map will most likely have empty patches,
			but the time for downloading and creating the map is reduced.
		'''
		if lat_min < -180 or lat_min > 180:
			raise ValueError("lat_min out of range [-180, 180]")
		if lat_max < -180 or lat_max > 180:
			raise ValueError("lat_max out of range [-180, 180]")
		if lon_min < -180 or lon_min > 180:
			raise ValueError("lon_min out of range [-180, 180]")
		if lon_max < -180 or lon_max > 180:
			raise ValueError("lon_max out of range [-180, 180]")
		if zoom < 0 or zoom > 19:
			raise ValueError("zoom out of range {0,...,19}")

		self.lat_min:int = lat_min
		self.lat_max:int = lat_max
		self.lon_min:int = lon_min
		self.lon_max:int = lon_max
		self.zoom:int = zoom
		self.add_border:bool = add_border
		self.route:list = route
		self._compute_maptile_coords()
		self._compute_map_dimensions()
		super().__init__("MapDownloader", 2+(self.n_tx*self.n_ty)//20)
		self._init_maptiles()
		self.name = self._construct_map_name()
		self.filename:str = self.name+".png"
		self.progress += 1

	def __str__(self):
		return self.name

	def __repr__(self):
		return str(self)

	def _compute_maptile_coords(self):
		'''
		computes range of tiles (x_min, x_max), (y_min, y_max) that are
		required to cover specified latitudes and longitudes at specified zoom level.
		'''
		mincoords = latlong_to_merccoords(self.lat_min, self.lon_min, self.zoom)
		maxcoords = latlong_to_merccoords(self.lat_max, self.lon_max, self.zoom)
		x_1 = mincoords[0]
		y_1 = mincoords[1]
		x_2 = maxcoords[0]
		y_2 = maxcoords[1]
		self.x_min = min(x_1, x_2)
		self.x_max = max(x_1, x_2)
		self.y_min = min(y_1, y_2)
		self.y_max = max(y_1, y_2)
		if self.add_border:
			self.x_min -= 1
			self.y_min -= 1
			self.x_max += 1
			self.y_max += 1

	def _compute_map_dimensions(self):
		'''
		compute total dimension of map
		in tiles (n_tx, n_ty)
		and in pixels (n_px, n_py).

		requires that self._compute_maptile_coords() has been executed.
		'''
		self.n_tx = self.x_max-self.x_min+1
		self.n_ty = self.y_max-self.y_min+1
		self.n_px = self.n_tx * MAP_DIM_TILE
		self.n_py = self.n_ty * MAP_DIM_TILE

	def _init_maptiles(self):
		'''
		Initializes maptiles.
		'''
		# if route is specified: construct lists of required tiles:
		self.required_tile_ids = {}
		if self.route is not None:
			for (lat, lon) in self.route:
				(x,y) = latlong_to_merccoords(lat, lon, self.zoom)
				borderdim = 0
				if self.add_border:
					borderdim = 1
				tiles_this_point = []
				for tx in range(x-borderdim, x+borderdim+1):
					if tx not in self.required_tile_ids:
						self.required_tile_ids[tx] = []
					for ty in range(y-borderdim, y+borderdim+1):
						if ty not in self.required_tile_ids[tx]:
							self.required_tile_ids[tx].append(ty)
		
		self.tiles = {}
		for tx in range(self.x_min, self.x_max+1):
			self.tiles[tx-self.x_min] = {}
			for ty in range(self.y_min, self.y_max+1):
				if self.route is None or ty in self.required_tile_ids[tx]:
					self.tiles[tx-self.x_min][ty-self.y_min] = MapTile(tx, ty, self.zoom)

	def _construct_map_name(self) -> str:
		'''
		Constructs a name based on tile range and zoom.
		'''
		mapname = "map_z:"+str(self.zoom)+"_x:"+str(self.x_min)+"-"+str(self.x_max)+"_y:"+str(self.y_min)+"-"+str(self.y_max)
		if self.route is not None:
			mapname += "_routeonly"
		return mapname

	def _download_tiles(self, ask_before_huge_download:bool=False) -> bool:
		'''
		Ensure all tiles are downloaded.

		Checks total number of tiles to fetch. If too large, user gets a chance to interrupt.
		Returns False if user interrupted download.

		Returns True when all tiles are downloaded/cached.
		'''
		if self.route is None:
			# number of tiles depends on map dimensions :
			total_number_of_tiles = self.n_tx*self.n_ty
		else:
			# number of tiles has to be counted:
			total_number_of_tiles = sum([len(self.tiles[x]) for x in self.tiles])
		# update subtask-weight to correspond to correct number of required downloads:
		self.weight = 2+total_number_of_tiles
		print ("Fetching",total_number_of_tiles,"map tiles...")
		if ask_before_huge_download and total_number_of_tiles > 1000:
			print ("Number of tiles is very large! Proceed (Y/n)?")
			r = input()
			if not r == "Y":
				return False
		elif total_number_of_tiles > 100:
			print (" ... this may take some time.")
		for tx in self.tiles:
			for ty in self.tiles[tx]:
				self.tiles[tx][ty].download()
				# track progress:
				self.progress += 1
		return True

	def _combine_tiles(self, debug_tiles:bool=False) -> Image:
		'''
		Combines all tiles into a single image and saves it in DIR_MAPS

		Assumes tiles are downloaded, i.e. self._download_tiles() has been executed.
		'''
		ensure_dir_exists(DIR_MAPS)	
		print ("Generate image of dimensions",self.n_px,"x",self.n_py)
		mapimage = Image.new('RGB', (self.n_px, self.n_py))

		draw = None
		if debug_tiles:
			draw = ImageDraw.Draw(mapimage)

		for ix in range(self.n_tx):
			for iy in range(self.n_ty):
				if self.route is None or (ix+self.x_min in self.required_tile_ids and iy+self.y_min in self.required_tile_ids[ix+self.x_min]):
					#tile_filepath = os.path.oin(DIR_MAPS, DIR_TILE_CACHE, self.tiles[ix][iy].filename)
					tile_image = Image.open(self.tiles[ix][iy].filepath)
					mapimage.paste(tile_image, (ix*MAP_DIM_TILE, iy*MAP_DIM_TILE))
					if debug_tiles:
						draw.line((ix*MAP_DIM_TILE, iy*MAP_DIM_TILE, (ix+1)*MAP_DIM_TILE, iy*MAP_DIM_TILE), fill=128)
						draw.line((ix*MAP_DIM_TILE, iy*MAP_DIM_TILE, (ix)*MAP_DIM_TILE, (iy+1)*MAP_DIM_TILE), fill=128)
						draw.line(((ix+1)*MAP_DIM_TILE, iy*MAP_DIM_TILE, (ix+1)*MAP_DIM_TILE, (iy+1)*MAP_DIM_TILE), fill=128)
						draw.line((ix*MAP_DIM_TILE, (iy+1)*MAP_DIM_TILE, (ix+1)*MAP_DIM_TILE, (iy+1)*MAP_DIM_TILE), fill=128)
						draw.text((ix*MAP_DIM_TILE+10, iy*MAP_DIM_TILE+10),"("+str(ix+self.x_min)+","+str(iy+self.y_min)+")",(200,0,0))
		return mapimage

	def get_map(self, custom_filename:str=None, debug_tiles:bool=False):
		'''
		Downloads required tiles (if not already cached) and constructs the map.
		If custom_filename is not specified,
			then zoomlevel and tileranges are used to create a unique filename.
			Also in this case it can be checked if the map already exists.
		If a unique filename is specified, a map will always be constructed (but cached tiles will not be downloaded again).

		debug_tiles: if True, map tile borders and map coordinates are plotted on the map
		'''
		if custom_filename is None:
			# construct unique filename and check if map already exists:
			self.filepath = os.path.join(DIR_MAPS, self.filename)
			if os.path.exists(self.filepath):
				print ("Requested map already exists at",self.filepath)
				self.finish_progress()
				return
		else:
			# ensure custom filename end with .png:
			if not custom_filename.endswith(".png"):
				custom_filename = custom_filename.split(".")[0]+".png"
			self.filepath = os.path.join(DIR_MAPS, custom_filename)

		download_success = self._download_tiles()
		if download_success:
			mapimage = self._combine_tiles(debug_tiles=debug_tiles)
			mapimage.save(self.filepath)
			print ("Generated map saved in: "+self.filepath)
		else:
			print ("Map generation interrupted")
		self.finish_progress()

def example():
	# Download map of berlin at zoom level 14:
	mapdownloader = OSMMapDownloader(
		lat_min = EXAMPLE_LATITUDE-0.05,
		lat_max = EXAMPLE_LATITUDE+0.05,
		lon_min = EXAMPLE_LONGITUDE-0.1,
		lon_max = EXAMPLE_LONGITUDE+0.1
		)
	mapdownloader.get_map("Berlin")

if __name__ == '__main__':
	example()