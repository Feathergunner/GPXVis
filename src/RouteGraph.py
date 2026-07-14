#!usr/bin/python
# -*- coding: utf-8 -*-import string

import os
import math
import numpy as np
#from matplotlib import pyplot as plt
import networkx as nx
#from PIL import Image

from src import OSMMapDownloader as osmmd
from src import GPXDataManager as GPXDM
from src.SubTask import SubTask

from src.misc_geometry import compute_angle_between_vectors, get_vector_as_mxb, project_point_on_vector, get_latlon_vector_length
from src.misc import load_gpx_file, parse_gps_from_gpx, ensure_dir_exists
from org import METER_PER_DEG_LAT, METER_PER_DEG_LON, NODE_MERGE_PRECISION, STRAIGHT_PATH_MAX_DEGREE

#LINEWIDTH = 1
#LINECOLOR = "red"
#{
#	"hiking" : red,
#	"running" : red,
#	"cycling" : red
#}


def round_gps(lat:float, lon:float, precision:int=NODE_MERGE_PRECISION):
	'''
	Rounds (lat,lon)-coordinates
	precision: precision of rounded coordinates in meter
	'''
	decimal_prec_lat = int(math.log(METER_PER_DEG_LAT/precision)/math.log(10))+1
	decimal_prec_lon = int(math.log(METER_PER_DEG_LON/precision)/math.log(10))+1
	rounded_lat = round(round((METER_PER_DEG_LAT/precision)*lat)/(METER_PER_DEG_LAT/precision), decimal_prec_lat)
	rounded_lon = round(round((METER_PER_DEG_LON/precision)*lon)/(METER_PER_DEG_LON/precision), decimal_prec_lon)
	return (rounded_lat, rounded_lon)
	#return (lat, lon)

def get_edge_key(node_id_a, node_id_b):
	return (min(node_id_a, node_id_b), max(node_id_a, node_id_b))

class RouteGraphNode():
	'''
	Class to represent nodes data with activity metadata
	'''
	n = 0
	def __init__(self, data):
		self.id = RouteGraphNode.n
		RouteGraphNode.n += 1
		self.data = [data]
		(self.rounded_lat, self.rounded_lon) = round_gps(self.get_latitude(), self.get_longitude())
		self.degree = 0
		self.angle = None

	def __str__(self):
		return "GraphNode: pos:("+str(self.get_latitude())+","+str(self.get_longitude())+"), elevation: "+str(self.get_elevation())+", time: "+str(self.get_time())

	def __repr__(self):
		return str(self)

	def get_label(self):
		return (self.rounded_lat, self.rounded_lon)

	def get_latitude(self):
		if "latitude" in self.data[0]:
			return self.data[0]["latitude"]
		else:
			return None

	def get_longitude(self):
		if "longitude" in self.data[0]:
			return self.data[0]["longitude"]
		else:
			return None

	def get_elevation(self):
		if "elevation" in self.data[0]:
			return self.data[0]["elevation"]
		else:
			return None

	def get_time(self):
		if "timestamp" in self.data[0]:
			return self.data[0]["timestamp"]
		else:
			return None

	def add_data(self, datapoint):
		self.data.append(datapoint)

	def get_position(self):
		return (self.get_longitude(), self.get_latitude())

class RouteGraphEdge():
	'''
	Class to represent graph edge with metadata
	'''
	n = 0
	def __init__(self, node_a:RouteGraphNode, node_b:RouteGraphNode, count:int=1, length:float=0):
		#print ("Construct new edge:")
		self.id = RouteGraphEdge.n
		RouteGraphEdge.n += 1
		if node_a.id < node_b.id:
			self.id_min = node_a.id
			self.id_max = node_b.id
		else:
			self.id_min = node_b.id
			self.id_max = node_a.id
		self.count = 1
		self.length = length

	def __str__(self):
		return "Edge "+str(self.id)+" between nodes "+str(self.id_min)+" - "+str(self.id_max)

	def __repr__(self):
		return str(self)

	def get_node_list(self):
		return [self.id_min, self.id_max]

	def get_key(self):
		return get_edge_key(self.id_min, self.id_max)

class RouteGraph():
	def __init__(self):
		self.nodes = {}
		self.edges = {}
		self.adjacencies = {}
		self.nodes_key_to_id = {}
		self.edges_key_to_id = {}
		self.basename = ""

	def __str__(self):
		_str = "Graph with "+str(len(self.nodes.keys()))+" nodes and "+str(len(self.edges.keys()))+" edges.\n"
		_str += "Adjacencies:\n"
		for n_id in self.adjacencies:
			if len(self.adjacencies[n_id].keys()) == 0:
				continue
			_str += str(n_id)+": "
			for nb_id in self.adjacencies[n_id].keys():
				_str += str(nb_id)+", "
			_str += "\n"
		return _str

	def number_of_nodes(self) -> int:
		return len([_ for _ in self.nodes.keys()])

	def number_of_edges(self) -> int:
		return len([_ for _ in self.edges.keys()])

	def edge_exists(self, node_id_a, node_id_b):
		if get_edge_key(node_id_a, node_id_b) in self.edges:
			return True
		else:
			return False

	def is_empty(self) -> bool:
		return self.number_of_nodes() == 0

	### BASIC GRAPH MANIPULATION:

	def add_node(self, node:RouteGraphNode):
		if node.get_label() in self.nodes_key_to_id.keys():
			# node at this approx. position exists already!
			node_id = self.nodes_key_to_id[node.get_label()]
			self.nodes[node_id].data.append(node.data[0])
		else:
			self.nodes[node.id] = node
			self.nodes_key_to_id[node.get_label()] = node.id

	def add_edge(self, edge:RouteGraphEdge):
		if edge.get_key() in self.edges_key_to_id.keys():
			# edge exists already!
			return
		self.edges[edge.id] = edge
		# update adjacency list:
		if edge.id_min not in self.adjacencies:
			self.adjacencies[edge.id_min] = {}
		self.adjacencies[edge.id_min][edge.id_max] = edge.id
		if edge.id_max not in self.adjacencies:
			self.adjacencies[edge.id_max] = {}
		self.adjacencies[edge.id_max][edge.id_min] = edge.id
		# add edge key:
		self.edges_key_to_id[edge.get_key()] = edge.id
		# update node degrees:
		self.nodes[edge.id_min].degree += 1
		self.nodes[edge.id_max].degree += 1

	def remove_edge(self, edge_id:int):
		# Remove an edge
		if edge_id not in self.edges.keys():
			# edge already non-existing!
			return
		edge = self.edges[edge_id]
		# remove edge in adjacency list:
		self.adjacencies[edge.id_min].pop(edge.id_max, None)
		self.adjacencies[edge.id_max].pop(edge.id_min, None)
		# remove edge key:
		self.edges_key_to_id.pop(self.edges[edge_id].get_key(), None)
		# remove edge entry:
		self.edges.pop(edge_id, None)
		# update node degrees:
		self.nodes[edge.id_min].degree -= 1
		self.nodes[edge.id_max].degree -= 1
		# delete object:
		del edge

	def remove_node(self, node_id:int):
		#print ("remove node",node_id)
		# Remove a node AND incident edges
		if node_id not in self.nodes.keys():
			# node already non-existing!
			return
		node = self.nodes[node_id]
		#print (" Got node data:",str(node))
		# remove incident edges:
		edges = [self.adjacencies[node_id][n] for n in self.adjacencies[node_id]]
		#print (" Remove incident edges:")
		for edge_id in edges:
			#print ("  remove edge", edge_id)
			self.remove_edge(edge_id)
		# remove node key:
		self.nodes_key_to_id.pop(node.get_label(), None)
		# remove node entry:
		self.nodes.pop(node_id)
		# delete object:
		del node

	def get_edges_as_nodepairs(self):
		edges = []
		for edge_id in self.edges:
			edges.append(self.edges[edge_id].get_node_list())
		return edges

	'''
	def compute_edge_length(self):
		lengths = []
		for e_key in self.edges:
			e = self.edges[e_key]
			u = self.nodes[e.id_min]
			v = self.nodes[e.id_max]
			d_lat = abs(u.get_latitude() - v.get_latitude())
			d_lon = abs(u.get_longitude() - v.get_longitude())
			dx = d_lon*METER_PER_DEG_LON
			dy = d_lat*METER_PER_DEG_LAT
			self.edges[e_key].length = math.sqrt(dx**2 + dy**2)
			lengths.append(self.edges[e_key].length)
			#lengths.append(math.sqrt(dx**2 + dy**2))
		print("node_distances:",np.mean(lengths))
	'''

	### SIMPLIFY GRAPH BY MERGING REDUNDANT NODES/EDGES
	### GRAPH MANIPULATION BASED ON ROUTE GPX-DATA:

	def simplify_graph(self, delta_angle:int=STRAIGHT_PATH_MAX_DEGREE, precision=NODE_MERGE_PRECISION):
		#self._contract_straight_paths(delta_angle)
		self._merge_parallels(precision)
		self._contract_straight_paths_by_precision(precision)
		#self._contract_straight_paths(delta_angle)
		#self._contract_straight_paths_by_precision(precision)
		
	def _compute_angles_at_d2_nodes(self):
		deg2_nodes = [n_id for n_id in self.nodes.keys() if self.nodes[n_id].degree == 2 and self.nodes[n_id].angle is None]
		for n_id in deg2_nodes:
			neighbor_ids = [nb_id for nb_id in self.adjacencies[n_id].keys()]
			# get direction vectors:
			n1n = [self.nodes[n_id].get_latitude()-self.nodes[neighbor_ids[0]].get_latitude(), self.nodes[n_id].get_longitude()-self.nodes[neighbor_ids[0]].get_longitude()]
			nn2 = [self.nodes[neighbor_ids[1]].get_latitude()-self.nodes[n_id].get_latitude(), self.nodes[neighbor_ids[1]].get_longitude()-self.nodes[n_id].get_longitude()]
			# compute angle between vectors:
			self.nodes[n_id].angle = compute_angle_between_vectors(n1n, nn2)

	def _find_d2_paths(self, delta_angle):
		'''
		Finds all paths that contain only nodes of degree 2
		'''
		self._compute_angles_at_d2_nodes()
		deg2_nodes = [n_id for n_id in self.nodes.keys() if self.nodes[n_id].degree == 2 and abs(self.nodes[n_id].angle)<delta_angle]
		#print ("nodes of degree 2:")
		#print ([(n_id, self.nodes[n_id].degree) for n_id in deg2_nodes])

		# construct all true paths, i.e. path where only endpoints have degree > 2:
		checked_nodes = []
		# paths are hashed by the ordered tuples of their endpoints:
		# each entry in the path-dictionary is a list of paths
		paths = {}
		for n_id in deg2_nodes:
			if n_id not in checked_nodes:
				points_interior = []
				points_end = []
				neighbors = [n_id]
				while len(neighbors) > 0:
					next_node = neighbors.pop(-1)
					if self.nodes[next_node].degree == 2:
						points_interior.append(next_node)
					else:
						points_end.append(next_node)
					if self.nodes[next_node].degree == 2:
						for nb_id in self.adjacencies[next_node].keys():
							if nb_id not in points_interior+points_end:
								neighbors.append(nb_id)
								#[nb_id for nb_id in self.adjacencies[n_id].keys()]
				path_key = (min(points_end),max(points_end))
				if path_key not in paths:
					paths[path_key] = []
				paths[path_key].append({"interior_nodes": points_interior, "endpoints": points_end})
				for n_id in points_interior+points_end:
					checked_nodes.append(n_id)

		#print ("found paths:")
		#print (paths)
		return paths

	def _contract_straight_paths_by_precision(self, precision):
		paths = self._find_d2_paths(2*STRAIGHT_PATH_MAX_DEGREE)

		for path_key in paths:
			for path in paths[path_key]:
				endpoints = path_key
				interior_nodes = path["interior_nodes"]
				ne1 = self.nodes[endpoints[0]]
				ne2 = self.nodes[endpoints[1]]
				ep1_lat = ne1.get_latitude()
				ep1_lon = ne1.get_longitude()
				ep2_lat = ne2.get_latitude()
				ep2_lon = ne2.get_longitude()
				# get vector as u1+x*u2, x \in \R,
				# with u1 = [0,b] and u2 = [1,m]
				(m,b) = get_vector_as_mxb((ep1_lat, ep1_lon),(ep2_lat,ep2_lon))

				all_nodes_close_to_diagonal = True
				for ip in interior_nodes:
					# get projection ipp of node ip onto mx+b:
					ip_lat = self.nodes[ip].get_latitude()
					ip_lon = self.nodes[ip].get_longitude()
					# (lat, lon) of projected point:
					(pp_lat, pp_lon) = project_point_on_vector(m, b, ip_lat, ip_lon)
					# approx. distance of ip to diagonal in meter
					distance = get_latlon_vector_length(ip_lat-pp_lat, ip_lon-pp_lon)
					if distance > precision:
						all_nodes_close_to_diagonal = False
						return False

				if all_nodes_close_to_diagonal:
					# delete all interior nodes, connect endpoints:
					for n_id in interior_nodes:
						self.remove_node(n_id)
						if not self.edge_exists(endpoints[0], endpoints[1]):
							new_edge = RouteGraphEdge(ne1, ne2)
						self.add_edge(new_edge)


	def _contract_straight_paths_by_angle(self, delta_angle:int):
		'''
		Simplifies graph by contracting nodes with degree 2 if both incident edges have similar direction,
		i.e. if node lies on straight route
		'''
		print ("contract straight paths...")
		affected_nodes = [node_id for node_id in self.adjacencies.keys() if len(self.adjacencies[node_id].keys()) == 2]
		removed_nodes = []
		while len(affected_nodes) > 0:
			nodes_to_inspect = [node_id for node_id in affected_nodes if len(self.adjacencies[node_id].keys()) == 2]
			affected_nodes = []
			#print ("nodes to inspect:")
			#print (nodes_to_inspect)
			for n_id in nodes_to_inspect:
				if n_id in affected_nodes or n_id in removed_nodes:
					continue
				#print ()
				#print ("consider node", n_id)
				# get adjacent nodes:
				neighbor_ids = [nb_id for nb_id in self.adjacencies[n_id].keys()]
				# get direction vectors:
				n1n = [self.nodes[n_id].get_latitude()-self.nodes[neighbor_ids[0]].get_latitude(), self.nodes[n_id].get_longitude()-self.nodes[neighbor_ids[0]].get_longitude()]
				nn2 = [self.nodes[neighbor_ids[1]].get_latitude()-self.nodes[n_id].get_latitude(), self.nodes[neighbor_ids[1]].get_longitude()-self.nodes[n_id].get_longitude()]
				#print ("n1n:",n1n)
				#print ("nn2:",nn2)
				# compute angle between vectors:
				angle = compute_angle_between_vectors(n1n, nn2)
				#print ("      = "+str(angle))
				if angle < delta_angle:
					#print ("angle <", delta_angle, "degrees: contract node!")
					# add new edge:
					#print ("Add new edge between nodes:")
					#print ("ids: ",neighbor_ids[0], neighbor_ids[1])
					#print ("node data:", self.nodes[neighbor_ids[0]], self.nodes[neighbor_ids[1]])
					self.add_edge(RouteGraphEdge(self.nodes[neighbor_ids[0]], self.nodes[neighbor_ids[1]]))
					# delete node:
					self.remove_node(n_id)
					affected_nodes += neighbor_ids# + [n_id]
					removed_nodes.append(n_id)
					#print (affected_nodes)
				#else:
				#	print ("significant change of direction. do not contract node.")


	def _merge_parallels(self, precision:int):
		'''
		Merges parallel paths.
		Searches for cycles with exactly two nodes of degree > 2 (call them endpoints).
		Then computes vector between endpoints
		'''
		print ("merge parallel paths...")
		finished = False
		while not finished:
			finished = True
			cycles = self._find_d2_cycles()
			for c in cycles:
				simplified_cycle = self._simplify_cyle(c, precision)
				if simplified_cycle:
					finished = False

	def _find_d2_cycles(self):
		'''
		Finds cycles that contain exactly two nodes with degree > 2.
		'''
		paths = self._find_d2_paths(180)
		cycles = []
		for path_key in paths:
			#print ("check path:",paths[path_key])
			if path_key[0] == path_key[1]:
				#print ("is a simple loop")
				# path is loop along another route: we do not want to delete these!
				continue
			elif len(paths[path_key]) == 1:
				#print ("contains only one nontrivial connection of endpoints")
				# path is a cycle if and only if endpoints are also directly connected:
				if path_key[1] in self.adjacencies[path_key[0]]:
					#print ("  but endpoints are also directly connected. is a cycle!")
					# found a cycle!
					new_cycle = {"endpoints": path_key, "interior_nodes": [path["interior_nodes"] for path in paths[path_key]]}
					cycles.append(new_cycle)
			else:
				# path is a cycle if there are multiple connections between the endpoints:
				if len(paths[path_key]) > 1:
					#print ("multiple connections between endpoints: is a cycle!")
					# found a cycle!
					new_cycle = {"endpoints": path_key, "interior_nodes": [path["interior_nodes"] for path in paths[path_key]]}
					cycles.append(new_cycle)
			
		#print ("Found cycles:")
		#print (cycles)
		return cycles

	def _simplify_cyle(self, cycle, precision) -> bool:
		'''
		cycle: a dictionary with keys "endpoints" and "interior_nodes",
			where "endpoints" contains a list of exactly two node ids,
			and "interior_nodes" contains a list of one or two lists, where each contains an arbitrary number of node ids

		returns True if cycle was removed
		'''
		# compute the diagonal, i.e. the direct connection between the two endpoints:
		ne1 = self.nodes[cycle["endpoints"][0]]
		ne2 = self.nodes[cycle["endpoints"][1]]
		ep1_lat = ne1.get_latitude()
		ep1_lon = ne1.get_longitude()
		ep2_lat = ne2.get_latitude()
		ep2_lon = ne2.get_longitude()
		# get vector as u1+x*u2, x \in \R,
		# with u1 = [0,b] and u2 = [1,m]
		(m,b) = get_vector_as_mxb((ep1_lat, ep1_lon),(ep2_lat,ep2_lon))

		all_interior_nodes = cycle["interior_nodes"][0]
		if len(cycle["interior_nodes"]) > 1:
			all_interior_nodes += cycle["interior_nodes"][1]
		all_nodes_close_to_diagonal = True
		for ip in all_interior_nodes:
			# get projection ipp of node ip onto mx+b:
			ip_lat = self.nodes[ip].get_latitude()
			ip_lon = self.nodes[ip].get_longitude()
			# (lat, lon) of projected point:
			(pp_lat, pp_lon) = project_point_on_vector(m, b, ip_lat, ip_lon)
			# approx. distance of ip to diagonal in meter
			distance = get_latlon_vector_length(ip_lat-pp_lat, ip_lon-pp_lon)
			if distance > precision:
				all_nodes_close_to_diagonal = False
				return False

		if all_nodes_close_to_diagonal:
			# delete all interior nodes, connect endpoints:
			for n_id in all_interior_nodes:
				self.remove_node(n_id)
				if not self.edge_exists(cycle["endpoints"][0], cycle["endpoints"][1]):
					new_edge = RouteGraphEdge(ne1, ne2)
				self.add_edge(new_edge)
		return True

	### EXPORT GRAPH:
	def get_networkx_graph(self):
		'''
		returns networkx-graph from nodes and edges of this graph

		# todo: add node positions
		'''
		g = nx.Graph()
		g.add_nodes_from([node_id for node_id in self.nodes.keys()])
		g.add_edges_from(self.get_edges_as_nodepairs())
		return g

class RouteGraphConstructor(SubTask):
	def __init__(
			self,
			gpx_dir:str,
			activity_type:str,
			use_unknown_type:bool=False,
			lat_ref:float=None,
			lon_ref:float=None,
			delta_km:float=None,
			dist_cutoff_km:int=None,
			date_min:str=None,
			date_max:str=None,
			use_unknown_date:bool=False):
		'''
		constructs a graph that contains all routes from a specified directory,
		if activity_type, lat/lon area, and date range fits into specified category
		'''
		super().__init__("RouteGraphConstructor", 6)
		self.gpx_dir = gpx_dir
		self.activity_type = activity_type
		self.use_unknown_type = use_unknown_type
		self.lat_ref = lat_ref
		self.lon_ref = lon_ref
		self.delta_km = delta_km
		self.dist_cutoff_km = dist_cutoff_km
		self.date_min = date_min
		self.date_max = date_max
		self.use_unknown_date = use_unknown_date
		self.rg = RouteGraph()

	def get_routegraph(self):
		dm = GPXDM.GPXDataManager(self.gpx_dir)
		gpxs_filenames = dm.get_list_of_gpx_files(self.lat_ref, self.lon_ref, self.delta_km, self.activity_type, self.use_unknown_type, self.date_min, self.date_max, self.use_unknown_date)

		for i in range(len(gpxs_filenames)):
			print ("load gpx from "+gpxs_filenames[i])
			(gpxdata, metadata) = load_gpx_file(gpxs_filenames[i])
			self._add_subgraph_from_gpx(gpxdata)
		self.progress += 1
		self.rg.simplify_graph()
		self.progress += 2
		self.rg._contract_straight_paths_by_angle(STRAIGHT_PATH_MAX_DEGREE)
		self.progress += 2
		self.rg.basename = self.activity_type
		if self.date_min is not None:
			self.rg.basename += "_from_"+str(self.date_min)
		if self.date_max is not None:
			self.rg.basename += "_until_"+str(self.date_max)
		self.finish_progress()
		return self.rg

	def _add_subgraph_from_gpx(self, gpxdata):
		'''
		loads the gpx data from a single gpx-file and add them to the graph
		'''
		gpsdata = parse_gps_from_gpx(gpxdata)
		previous_node = None
		datapoint_dists = []

		#last_distance = 0
		#tmp_distance = 0
		for datapoint in gpsdata:
			#print (datapoint)
			# construct node:
			lat = datapoint["latitude"]
			lon = datapoint["longitude"]
			if lat is None or lon is None:
				continue
			if lat == 0 or lon == 0:
				continue
			if self.dist_cutoff_km is not None:
				if get_latlon_vector_length(lat-self.lat_ref, lon-self.lon_ref)/1000 > self.dist_cutoff_km:
					previous_node = None
					continue
			(node_pos_lat, node_pos_lon) = round_gps(lat, lon)
			if (node_pos_lat, node_pos_lon) not in self.rg.nodes_key_to_id:
				# construct new node:
				new_node = RouteGraphNode(datapoint)
				self.rg.add_node(new_node)
				#tmp_distance = 0
			else:
				# map datapoint to existing node:
				new_node = self.rg.nodes[self.rg.nodes_key_to_id[(node_pos_lat, node_pos_lon)]]
				new_node.add_data(datapoint)
			
			if previous_node is not None:
				# check if new node is different from the previous node:
				if not previous_node.get_label() == (node_pos_lat, node_pos_lon):
					# construct edge:
					if not self.rg.edge_exists(previous_node.id, new_node.id):
						new_edge = RouteGraphEdge(previous_node, new_node)
						self.rg.add_edge(new_edge)
					else:
						edge_key = get_edge_key(previous_node.id, new_node.id)
						self.rg.edges[edge_key].count += 1
			previous_node = new_node
		#print ("datapoint_distances:",np.mean(datapoint_dists))

def construct_routegraph(gpx_dir:str, activity_type:str, lat_ref:float, lon_ref:float, delta_km:float, dist_cutoff_km:int=None, min_date:str=None, max_date:str=None):
	RGC = RouteGraphConstructor(gpx_dir, activity_type, lat_ref, lon_ref, delta_km, dist_cutoff_km, min_date, max_date)
	return RGC.rg

if __name__ == '__main__':
	pass