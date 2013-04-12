#!/usr/bin/env python
#-*- coding: utf-8 -*-

import sys
import math
import datetime
import geomath


class GPX():

	def __init__(self,location):
		'''Readies variables for use.
		
		Keyword arguments:
		location -- the directory of the file to be opened
		
		'''
		self.gpx_doc = ''
		self.gpx_file = ''
		self.gpx_location = location
		self.route_position = -1
		self.route_points = []
		self.route_distance = 0
		self.route_five = []
		self.track_size = 0
		self.unit_measure = None
		self.haversine = geomath.haversine

	def track_start(self):
		'''Creates a new track file for future use.'''
		self.gpx_file = str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M')) + '.gpx'
		out = '<?xml version="1.0" encoding="UTF-8" standalone="no" ?>\n<gpx>\n\t<trk>\n\t\t<name>NAVSTAT TRACK</name>\n\t\t<trkseg>\n'
		self.gpx_doc = open(self.gpx_location + self.gpx_file, 'a')
		self.track_out(out)

	def track_point(self,lat,lon,ele,tme):
		'''Readies a track point to be outputted to the track file.
		
		Keyword arguments:
		lat -- the latitude to output
		lon -- the longitude to output
		ele -- the elevation to output
		tme -- the time to output
		
		'''
		out = '\t\t\t<trkpt lat="' + str(lat) + '" lon="' + str(lon) + '">\n' + '\t\t\t\t<ele>' + str(ele) + '</ele>\n' + '\t\t\t\t<time>' + str(tme) + '</time>\n\t\t\t</trkpt>\n'
		self.track_out(out)

	def track_out(self, out):
		'''Outputs track text to the track gpx file.
		
		Keyword arguments:
		out -- the string to be outputted
		
		'''
		self.gpx_doc.write(out)
		self.track_size = self.track_size + sys.getsizeof(out)

	def track_close(self):
		'''Closes the current track gpx file.'''
		out = '\t\t</trkseg>\n\t</trk>\n</gpx>'
		self.track_out(out)
		self.gpx_doc.close()

	def route_start(self,gpx_file):
		'''Reads the entire GPX route file, and creates a list from it.
		
		Keyword arguments:
		gpx_file -- the GPX route file to open
		
		'''
		lat_lon = [0,0,'',0,0]
		#Open the gpx route file
		self.gpx_doc = open(self.gpx_location + gpx_file, 'r')
		self.gpx_file = gpx_file
		#Create a local version of functions
		route_append = self.route_points.append
		haversine = self.haversine
		con = 0
		#Run through each line of the route file
		for line in self.gpx_doc:
			line = line.lstrip()
			#Extract route point lat/long
			if line[1:6] == 'rtept':
				line = line.split('"')
				lat_lon[0] = float(line[1])
				lat_lon[1] = float(line[3])
				con = 1
			#Extract route point name
			elif line[1:5] == 'name' and con == 1:
				line = line.split('name>')
				lat_lon[2] = line[1][:-2]
				#As long as its not the first point
				if self.route_points:
					#Calculate the distance from the last point, to this point
					haversine_info = haversine(self.route_points[-1][0],self.route_points[-1][1],lat_lon[0],lat_lon[1])
					#Place distance in last point info
					self.route_points[-1][3] = haversine_info[0]
					self.route_points[-1][4] = haversine_info[1]
					#Add to the total distance
					self.route_distance = haversine_info[0] + self.route_distance
				route_append([lat_lon[0],lat_lon[1],lat_lon[2],0,0])
				con = 0
		self.gpx_doc.close()

	def route_get(self, mode):
		'''Returns the next or last point in the route list.

		Keyword arguments:
		mode -- determines whether to move forward (0) / backward (1)
		
		'''
		#Moves the route position forward or backward
		if mode == 0:
			self.route_position = self.route_position + 1
			if self.route_position >= len(self.route_points):
				self.route_position = self.route_position - 1
		elif mode == 1:
			self.route_position = self.route_position - 1
			if self.route_position < 0:
				self.route_position = 0
		#Recalculates the route distance
		self.route_calc(mode)
		#Returns the route point info
		return self.route_points[self.route_position]

	def route_calc(self,mode):
		'''Calculates the distance between the next route position, and all points after.'''
		#Removes the current route point from calculation
		x = self.route_position + 1
		self.route_distance = 0
		#The total number of remaining route points (-1 because of 0 list start)
		length = len(self.route_points) - 1
		#Adds the distance info
		while x < length:
			self.route_distance = self.route_distance + self.route_points[x][3]
			x += 1



#gpx_route = GPX('/home/home/NAVSTAT/Routes/')
#gpx_route.route_start('ride somewhere.gpx')
#hello = gpx_route.route_get()

#print gpx_route.route_points
#print gpx_route.route_distance
#print gpx_route.route_five
#print gpx_route.route_position
#print hello
