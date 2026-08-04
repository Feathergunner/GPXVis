#!usr/bin/python
# -*- coding: utf-8 -*-import string

import os
import math
import numpy as np
from matplotlib import pyplot as plt

from org import METER_PER_DEG_LAT, METER_PER_DEG_LON, NODE_MERGE_PRECISION

def compute_angle_between_vectors(v1:tuple, v2:tuple) -> float:
	'''
	compute the angle between two 2d-vectors v1=[x1, y1], v2=[x2,y2].

	Returns the degree in range (-180, 180)
	'''
	dotprod = np.dot(v1, v2)
	l_1 = np.linalg.norm(v1,2)
	l_2 = np.linalg.norm(v2,2)
	div = dotprod/(l_1*l_2)
	div = min(1,max(div, -1))
	angle = (np.arccos(div)*180)/math.pi
	return angle

def get_vector_as_mxb(v1:tuple, v2:tuple) -> tuple:
	# construct representation of 2d-vector (v2-v1) as u1+x*u2, x \in \R,
	# with u1 = [0,b] and u2 = [1,m]
	denom = (v1[0]-v2[0])
	if denom == 0:
		# set difference to be approx. 10cm to avoid numerical problems
		denom = 0.1/METER_PER_DEG_LAT
	m = (v1[1]-v2[1])/denom
	b = v1[1] - v1[0]*m
	return (m,b)

def project_point_on_vector(m:float, b:float, p_x:float, p_y:float) -> tuple:
	# projects a 2d-point p=(p_x, p_y) onto a 2d-vector given by
	# x*u1+u2, x \in \R,
	# with u1 = (1,m) and u2 = (0,b)
	# returns the projected point pp=(pp_x, pp_y)

	# compute the projected point pp:
	pp_x = (p_x + m*(p_y-b))/(1+m*m)
	pp_y = pp_x*m + b
	return (pp_x, pp_y)

def get_latlon_vector_length(d_lat:float, d_lon:float) -> float:
	# scales a vector from (lat, lon) to meters
	# and returns length in meters
	dx = d_lat*METER_PER_DEG_LAT
	dy = d_lon*METER_PER_DEG_LON
	return np.linalg.norm([dx,dy],2)

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

def test_projection():
	def _test_representation(p1, p2):
		(m,b) = get_vector_as_mxb(p1,p2)
		print ("(m,b) from",p1,p2,":",m,b )
		return (m,b)
	def _test_projection(m,b,p):
		(ppx, ppy) = project_point_on_vector(m,b,p[0], p[1])
		print ("projection of point (",p[0],",",p[1],"): (",ppx,",",ppy,")")

	testpoints = [(1,1), (2,2), (1,-1), (-1,1), (5,1), (3,1)]

	(m,b) = _test_representation((0,0),(1,0))
	for tp in testpoints:
		_test_projection(m,b,tp)
	(m,b) = _test_representation((0,0),(1,1))
	for tp in testpoints:
		_test_projection(m,b,tp)
	(m,b) = _test_representation((0,1),(1,0))
	for tp in testpoints:
		_test_projection(m,b,tp)
	(m,b) = _test_representation((0,1),(1,1))
	for tp in testpoints:
		_test_projection(m,b,tp)
	(m,b) = _test_representation((1,2),(2,3))
	for tp in testpoints:
		_test_projection(m,b,tp)
	(m,b) = _test_representation((1,3),(2,4))
	for tp in testpoints:
		_test_projection(m,b,tp)

if __name__ == '__main__':
	test_projection()
