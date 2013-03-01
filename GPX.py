import sys
import math
import datetime


class GPX():

	def __init__(self,location):
		'''Readies variables for use.
		
		Keyword arguments:
		location -- the directory of the file to be opened
		
		'''
		self.gpx_doc = ''
		self.gpx_location = location
		self.route_position = -1
		self.route_points = []
		self.route_distance = 0
		self.route_five = []
		self.track_size = 0
		self.unit_measure = None

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
		lat_lon = [0,0,'',0,0]
		self.gpx_doc = open(self.gpx_location + gpx_file, 'r')
		con = 0
		for line in self.gpx_doc:
			if line.find('<rtept') != -1:
				start = line.find('lat=')
				end = line.find('lon=')
				lat_lon[0] = float(line[start + 5:end - 2])
				start = line.find('lon=')
				end = line.find('">')
				lat_lon[1] = float(line[start + 5:end])
				con = 1
			if line.find('<name>') != -1 and con == 1:
				start = line.find('<name>')
				end = line.find('</name>')
				lat_lon[2] = line[start + 6:end]
				if len(self.route_points) >= 1:
					haversine_info = self.haversine(self.route_points[-1][0],self.route_points[-1][1],lat_lon[0],lat_lon[1])
					self.route_points[-1][3] = haversine_info
					self.route_distance = haversine_info + self.route_distance
				self.route_points.append([lat_lon[0],lat_lon[1],lat_lon[2],0])
				con = 0

	def route_get(self):
		x = 1
		self.route_five = []
		self.route_position = self.route_position + 1
		while x < 6:
			self.route_five.append(self.route_points[self.route_position + x])
			x += 1
		self.route_calc()
		return self.route_points[self.route_position]

	def route_calc(self):
		x = self.route_position + 1
		self.route_distance = 0
		length = len(self.route_points) - 1
		while x < length:
			self.route_distance = self.route_distance + self.route_points[x][3]
			x += 1

	def haversine(self,lat_1,lon_1,lat_2,lon_2):
		'''Calculates the distance between two coordinates.
		
		Keyword arguments:
		lat_1 -- the base coordinate latitude
		lon_1 -- the base coordinate longitude
		lat_2 -- the alternate coordinate latitude
		lon_2 -- the alternate coordinate longitude
		
		'''
		#Earth radius
		radius = 6378.137
		lon_1, lat_1, lon_2, lat_2 = map(math.radians, [lon_1, lat_1, lon_2, lat_2])
		dst_lon = lon_2 - lon_1
		dst_lat = lat_2 - lat_1
		a = math.sin(dst_lat/2)**2 + math.cos(lat_1) * math.cos(lat_2) * math.sin(dst_lon/2)**2
		c = 2 * math.asin(math.sqrt(a))
		dis_out = radius * c
		return round(dis_out,2)



#gpx_route = GPX('/home/home/NAVSTAT/Routes/')
#gpx_route.route_start('Example.gpx',1)
#hello = gpx_route.route_get()

#print gpx_route.route_points
#print gpx_route.route_distance
#print gpx_route.route_five
#print gpx_route.route_position
#print hello
