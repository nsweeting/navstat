import thread
import time
import datetime
import geomath
import math
import pygame
import sys


class GPS():

	def __init__(self, gui, cache, unit):
		#Degree character required for lat/long
		self.degree              = chr(176)
		#Top speed on the speedometer
		self.speed_top           = 2
		#Compass rose x,y points
		self.compass_rose_1      = [[393,40,'N'],[278,152,'W'],[393,263,'S'],[502,152,'E']]
		self.compass_rose_2      = [[298,75,'NW'],[298,232,'SW'],[475,232,'SE'],[475,75,'NE']]
		self.compass_rose_3      = [[(400,62),(400,82)],[(471,91),(461,101)],[(500,162),(480,162)],[(471,233),(461,223)],[(400,262),(400,242)],[(329,233),(339,223)],[(300,162),(320,162)],[(329,91),(339,101)]]
		#Used to calculate the location of text
		self.calc_size           = geomath.calc_size
		#Used to calculate the position of a line in a circle
		self.calc_line           = geomath.calc_line
		#Used to convert units
		self.unit                = unit
		#Holds GUI data
		self.gui                 = gui
		#Holds cached GPS data
		self.cache               = cache
		self.route               = ROUTE(self.cache, ALARM())
		self.track               = TRACK(self.cache)

	def interface(self):
		'''Draws all the basic gps interface graphics.'''
		#Draws the interface lines
		pygame.draw.lines(self.gui.screen, self.gui.colour_2, False, [(250,0),(250,550)], 2)
		pygame.draw.lines(self.gui.screen, self.gui.colour_2, False, [(550,0),(550,500)], 2)
		#If tracking is on, draw it
		if self.track.mode == True:
			self.gui.txt_out(self.gui.font_1.render('Tracking - ' + self.track.gpx_track.gpx_file, True, self.gui.colour_2),10,477)
		if self.route.mode == True:
			self.gui.txt_out(self.gui.font_1.render('Route - ' + self.route.gpx_route.gpx_file, True, self.gui.colour_2),560,477)

	def latlong(self):
		'''Positions and draws the lat/long interface.
		
		Keyword arguments:
		lat -- the current latitude position
		lon -- the current longitude position
		
		'''
		#Draws the basic latlon interface
		pygame.draw.rect(self.gui.screen, self.gui.colour_2, (0,0,250,20))
		self.gui.txt_out((self.gui.font_3.render('POS', True, self.gui.colour_1)),107,0)
		#Cuts the decimal count down to 5
		lat = self.cache.gps['lat']
		lon = self.cache.gps['lon']
		lat_out = ("%.5f" % self.cache.gps['lat'])
		lon_out = ("%.5f" % self.cache.gps['lon'])
		#Applies N/S, W/E based on negative value
		if lat < 0:
			lat_out = lat_out[1:] + ' S'
		elif lat > 0:
			lat_out = lat_out + ' N'
		if lon < 0:
			lon_out = lon_out[1:] + ' W'
		elif lon > 0:
			lon_out = lon_out + ' E'
		#Determines the lat length, and centres accordingly
		l_len = len(lat_out)
		if l_len == 10:
			ext_1 = 20
		elif l_len == 11:
			ext_1 = 1
		else:
			ext_1 = 40
		#Determines the lon length, and centres accordingly
		l_len = len(lon_out)
		if l_len == 10:
			ext_2 = 20
		elif l_len == 11:
			ext_2 = 1
		else:
			ext_2 = 40
		#Draws the lat/long interface text
		self.gui.txt_out((self.gui.font_4.render(lat_out, True, self.gui.colour_2)),20 + ext_1,30)
		self.gui.txt_out((self.gui.font_4.render(lon_out, True, self.gui.colour_2)),20 + ext_2,75)

	def speedometer(self):
		'''Positions and draws the speedometer interface.
		
		Keyword arguments:
		speed_out -- the current vessel speed
		
		'''
		#Draws the basic speedometer interface
		pygame.draw.rect(self.gui.screen, self.gui.colour_2, (0,128,250,20))
		self.gui.txt_out((self.gui.font_3.render('SOG', True, self.gui.colour_1)),107,128)
		#Rounds and converts speed to unit setting
		speed_out = round(self.unit.convert(1,self.cache.gps['speed']),1)
		#Determines speedometer position based on top speed
		speed_meter = (speed_out*220)/self.speed_top
		if speed_meter > 220:
			speed_meter = 220
		ext = self.calc_size(speed_out)
		#Draws the speedometer interface
		pygame.draw.rect(self.gui.screen, self.gui.colour_2, (15,210,220,40), 1)
		pygame.draw.rect(self.gui.screen, self.gui.colour_2, (15,210,speed_meter,40))
		self.gui.txt_out((self.gui.font_4.render(str(speed_out) + ' ' + self.unit.text[1], True, self.gui.colour_2)),30 + ext,158)
		self.gui.txt_out((self.gui.font_1.render(str(self.speed_top), True, self.gui.colour_2)),220,253)
		self.gui.txt_out((self.gui.font_1.render(str(self.speed_top/2), True, self.gui.colour_2)),116,253)
		self.gui.txt_out((self.gui.font_1.render('0', True, self.gui.colour_2)),15,253)

	def compass(self):
		'''Positions and draws the compass interface.'''
		#Draws the basic compass interface
		pygame.draw.rect(self.gui.screen, self.gui.colour_2, (250,0,300,20))
		self.gui.txt_out((self.gui.font_3.render('COG', True, self.gui.colour_1)),380,0)
		#Determines the x,y position on compass circumference in relation to degrees
		compass_out = self.cache.gps['track'] 
		compass_main = self.calc_line(compass_out,100,400,162)
		#Draws the compass rose
		for point in self.compass_rose_1:
			self.gui.txt_out(self.gui.font_2.render(point[2], True, self.gui.colour_2),point[0],point[1])
		for point in self.compass_rose_2:
			self.gui.txt_out(self.gui.font_3.render(point[2], True, self.gui.colour_2),point[0],point[1])
		for point in self.compass_rose_3:
			pygame.draw.lines(self.gui.screen, self.gui.colour_2, False, point, 3)
		#Repositions degree text based on size
		ext = self.calc_size(compass_out)
		#If routing is enabled, draws the current destination line 
		if self.route.mode == True:
			compass_destination = self.calc_line(self.route.waypoint_calc['bearing'],100,400,162)
			pygame.draw.lines(self.gui.screen, self.gui.colour_2, False, [(400,162),(compass_destination[0],compass_destination[1])], 1)
		#Draws the compass interface
		pygame.draw.circle(self.gui.screen, self.gui.colour_2, (400,162), 5)
		pygame.draw.circle(self.gui.screen, self.gui.colour_2, (400,162), 100,1)
		pygame.draw.lines(self.gui.screen, self.gui.colour_2, False, [(400,162),(compass_main[0],compass_main[1])], 5)
		self.gui.txt_out((self.gui.font_4.render(str(round(compass_out)).replace('.0','') + self.degree, True, self.gui.colour_2)),342 + ext,290)

	def destination(self):
		'''Positions and draws destination interface.'''
		#Positions and draws the route interface
		pygame.draw.rect(self.gui.screen, self.gui.colour_2, (250,350,300,20))
		pygame.draw.rect(self.gui.screen, self.gui.colour_2, (550,0,250,20))
		pygame.draw.rect(self.gui.screen, self.gui.colour_2, (550,85,250,20))
		pygame.draw.rect(self.gui.screen, self.gui.colour_2, (550,288,250,20))
		pygame.draw.rect(self.gui.screen, self.gui.colour_2, (550,376,250,20))
		self.gui.txt_out((self.gui.font_3.render('WPT', True, self.gui.colour_1)),385,350)
		self.gui.txt_out((self.gui.font_3.render('WTA', True, self.gui.colour_1)),655,376)
		self.gui.txt_out((self.gui.font_3.render('XTE', True, self.gui.colour_1)),655,0)
		self.gui.txt_out((self.gui.font_3.render('XTA', True, self.gui.colour_1)),655,85)
		self.gui.txt_out((self.gui.font_3.render('RTA', True, self.gui.colour_1)),655,288)
		if self.route.mode == True:
			#Gets current waypoint info for storage
			wpt_distance = self.unit.convert(0,self.route.waypoint_calc['distance'])
			wpt_xte = [self.unit.convert(0,self.route.waypoint_xte[0]),self.route.waypoint_xte[1]]
			wpt_bearing = self.route.waypoint_calc['bearing']
			#Positions destination distance and bearing text based on length
			ext1 = self.calc_size(wpt_distance)
			ext2 = self.calc_size(wpt_bearing)
			ext3 = self.calc_size(wpt_xte[0])
			#Draws the waypoint bearing info
			self.gui.txt_out((self.gui.font_4.render(str(wpt_distance) + ' ' + self.unit.text[0], True, self.gui.colour_2)),300 + ext1,418)
			self.gui.txt_out((self.gui.font_4.render(str(wpt_bearing).replace('.0','') + self.degree, True, self.gui.colour_2)),343 + ext2,378)
			#Positions and draws crosstrack error interface
			#Positions xte text based on length
			self.gui.txt_out((self.gui.font_4.render(wpt_xte[1] + str(wpt_xte[0]) + ' ' + self.unit.text[0], True, self.gui.colour_2)),555 + ext3,30)
			#Positions and draws the RTA info.
			self.gui.txt_out((self.gui.font_2.render(self.route.total_eta, True, self.gui.colour_2)),600,325)
			#WTA hours too large to display
			if self.route.waypoint_eta['hour'] == '1000':
				self.gui.txt_out((self.gui.font_4.render('1000h +', True, self.gui.colour_2)),615,406)
			else:
				#Positions and draws the WTA info
				ext = self.calc_size(self.route.waypoint_eta['hour'])
				self.gui.txt_out((self.gui.font_4.render(str(self.route.waypoint_eta['hour']) + 'h' + ' : ' + self.route.waypoint_eta['min'] + 'm', True, self.gui.colour_2)),565 + ext,406)
			#Draw crosstrack angle if available
			if self.route.waypoint_xte[1] != '':
				self.xtaline()

	def xtaline(self):
		pygame.draw.polygon(self.gui.screen, self.gui.colour_2, [(675,240),(669,260),(681,260)],1)
		pygame.draw.circle(self.gui.screen, self.gui.colour_2, (self.route.xte_angle[1][0],self.route.xte_angle[1][1]), 4)
		#Standard measurement lines
		pygame.draw.lines(self.gui.screen, self.gui.colour_2, False, [(self.route.xte_angle[0],240),(self.route.xte_angle[0],170)], 1)
		pygame.draw.lines(self.gui.screen, self.gui.colour_2, False, [(675,170),(self.route.xte_angle[0],170)], 1)
		pygame.draw.lines(self.gui.screen, self.gui.colour_2, False, [(675,240),(self.route.xte_angle[0],170)], 1)
		#Angle lines
		pygame.draw.lines(self.gui.screen, self.gui.colour_2, False, [(self.route.xte_angle[0],170),(self.route.xte_angle[1][0],self.route.xte_angle[1][1])], 3)
		pygame.draw.lines(self.gui.screen, self.gui.colour_2, False, [(self.route.xte_angle[0],170),(self.route.xte_angle[3][0],self.route.xte_angle[3][1])], 3)


class ROUTE():

	def __init__(self, cache, alarm):
		self.gpx_route           = None
		#Routing switch
		self.mode                = False
		#The location of route files
		self.location            = None
		#Lat, lon, name, distance, and bearing of current route waypoint
		self.waypoint_info       = {'lat': 0, 'lon': 0, 'name': '', 'distance': 0, 'bearing': 0}
		#Calculated distance and bearing to current waypoint
		self.waypoint_calc       = {'distance': 0, 'bearing': 0}
		#Hour and minutes to current waypoint
		self.waypoint_eta        = {'hour': '', 'min': ''}
		#Current crosstrack error for waypoint
		self.waypoint_xte        = [0,'']
		#The total distance of current route
		self.total_distance      = None
		#The estimated date of arrival for total route
		self.total_eta           = None
		self.xte_alarm           = 10
		self.xte_angle           = [0,[0,0],0,[0,0]]
		self.cache               = cache
		self.alarm               = alarm
		self.haversine           = geomath.haversine
		self.calc_line           = geomath.calc_line

	def switch(self):
		'''Checks whether Route Mode is enabled, and starts a routing, arrival and crosstrack thread if so.'''
		if self.mode == False:
			self.mode = True
			self.gpx_route = GPX(self.location)
			self.gpx_route.route_start('ride somewhere.gpx')
			thread.start_new_thread(self.position, ())
			thread.start_new_thread(self.arrival, ())
			thread.start_new_thread(self.crosstrack, ())
		else:
			self.mode = False

	def position(self):
		'''Used to keep track of current position in relation to current route - run as thread.'''
		#Gets the next route position
		self.get(0)
		#Run while routing is enabled
		while self.mode == True:
			#Calculates distance between current position, and destination point
			waypoint_info = self.haversine(self.cache.gps['lat'],self.cache.gps['lon'],self.waypoint_info['lat'],self.waypoint_info['lon'])
			self.waypoint_calc = {'distance': waypoint_info[0], 'bearing': waypoint_info[1]}
			#Calculates total route distance
			self.total_distance = self.waypoint_calc['distance'] + self.gpx_route.route_distance
			#Close to the destination - get the next point
			if self.waypoint_calc['distance'] < 0.02:
				self.get(0)
			time.sleep(1)

	def arrival(self):
		'''Calculates the estimated arrival time based on current speed - run as thread.'''
		#Loops until routing is turned off
		while self.mode == True:
			speed = round(self.cache.gps['speed'],2)
			#Make sure we do not divide by zero
			if speed > 0:
				time_current = datetime.datetime.now()
				#Determine time required for whole route
				time_total = self.total_distance / speed
				time_total_min, time_total_hour = math.modf(time_total)
				time_total_min = round(time_total_min*60)
				#Create a date/time object for ETA
				time_total = time_current + datetime.timedelta(hours=time_total_hour, minutes=time_total_min)
				self.total_eta = time_total.strftime("%Y-%m-%d %H:%M")
				#Determine time required for next point in route
				time_point = self.waypoint_calc['distance'] / speed
				time_point_min, time_point_hour = math.modf(time_point)
				time_point_min = round(time_point_min*60)
				#If time is too large to display properly
				if time_point_hour > 1000:
					self.waypoint_eta['hour'] = '1000'
				else:
					#Add a 0 if minutes are less then 10
					if time_point_min < 10:
						time_point_min = '0' + str(time_point_min)
					#Remove decimal points
					self.waypoint_eta['hour'] = int(str(time_point_hour).replace('.0',''))
					self.waypoint_eta['min'] = str(time_point_min).replace('.0','')
				time.sleep(4)
			#Do not estimate times if speed is 0
			else:
				self.total_eta = '           --'
				self.waypoint_eta['hour'] = '--'
				self.waypoint_eta['min'] = '--'

	def crosstrack(self):
		'''Calculates the crosstrack error for the current destination - run as thread.'''
		#Loops until routing is turned off
		while self.mode == True:
			#Make sure this is not the first point in the route (no standard bearing)
			if self.gpx_route.route_points[0][0] != self.waypoint_info['lat']:
				#Gets haversine info of last route point
				hav_start = self.haversine(self.gpx_route.route_points[self.gpx_route.route_position - 1][0], self.gpx_route.route_points[self.gpx_route.route_position - 1][1], self.cache.gps['lat'], self.cache.gps['lon'])
				#Crosstrack calculation
				self.waypoint_xte[0] = math.asin(math.sin(hav_start[0]/3443.92)*math.sin(hav_start[1]-self.gpx_route.route_points[self.gpx_route.route_position - 1][4]))*3443.92
				#Negative is left of course - making positive again
				if self.waypoint_xte[0] < 0:
					self.waypoint_xte[0] = self.waypoint_xte[0]*(-1)
					self.waypoint_xte[1] = 'L'
				#Right of course
				elif self.waypoint_xte[0] > 0:
					self.waypoint_xte[1] ='R'
				#Creates a crosstrack angle
				self.angle()
				#Checks for XTE alarm status
				if self.waypoint_xte[0] >= self.xte_alarm:
					self.alarm.xte = True
				elif self.waypoint_xte[0] < self.xte_alarm:
					self.alarm.xte = False
			#No current standard bearing
			else:
				self.alarm.xte = False
				self.waypoint_xte[0] = '    --'
				self.waypoint_xte[1] =''
			time.sleep(1)

	def angle(self):
		'''Calculates the crosstrack angle numbers for the interface.'''
		#Determines the positioning of the xte angle, based on xte distance
		if self.waypoint_xte[0] < 5:
			xte_lineadd = int(round(self.waypoint_xte[0]*10))
		else:
			xte_lineadd = 50
		#Adds/subs the above to the base position
		if self.waypoint_xte[1] == 'L':
			self.xte_angle[0] = 675 + xte_lineadd
		elif self.waypoint_xte[1] == 'R':
			self.xte_angle[0] = 675 - xte_lineadd
		#Determines how far away, in degrees, the current track is from the waypoint track
		self.xte_angle[2] = self.gpx_route.route_points[self.gpx_route.route_position - 1][4] - self.cache.gps['track']
		self.xte_angle[2] = round((self.xte_angle[2] + 180) % 360 - 180)
		#Negative is left, positive is right
		if self.xte_angle[2] < 0:
			xte_calc = 360 + self.xte_angle[2]
		elif self.xte_angle[2] > 0:
			xte_calc = 0 + self.xte_angle[2]
		else:
			xte_calc = 0
		xte_calc_opposite = (xte_calc + 180) % 360
		self.xte_angle[1] = self.calc_line(xte_calc,40,self.xte_angle[0],170)
		self.xte_angle[3] = self.calc_line(xte_calc_opposite,40,self.xte_angle[0],170)

	def get(self,pos):
		'''Grabs the next or last waypoint info.
		
		Keyword arguments:
		pos - tells whether to go forward (0), or backward (1)
		
		'''
		data = self.gpx_route.route_get(pos)
		self.waypoint_info = {'lat': data[0], 'lon': data[1], 'name': data[2], 'distance': data[3], 'bearing': data[4]}


class TRACK():

	def __init__(self, cache):
		#Tracking switch
		self.mode                = False
		#The location of track files
		self.location            = None
		#Holds track point info for future file output
		self.route               = []
		#Number of seconds between each track point. Number of points between each track file output
		self.save_info           = [10,6]
		#The max size of a track file
		self.maxsize             = None
		self.gpx_track           = None
		self.distance_total      = 0
		self.distance_track      = True
		self.cache               = cache

	def switch(self):
		'''Checks whether Track Mode is enabled, and starts a tracking thread if so.'''
		if self.mode == False:
			self.mode = True
			self.gpx_track = GPX(self.location)
			self.gpx_track.track_start()
			thread.start_new_thread(self.start, ())
		else:
			self.mode = False
			self.off()

	def start(self):
		'''Used as a thread to save tracking info for future file output.'''
		x = 0
		#Loop that keeps track of time, and saves track info based on this time
		while self.mode == True:
			self.route.append([self.cache.gps['lat'], self.cache.gps['lon'], self.cache.gps['utc']])
			x = x + 1
			if x > self.save_info[1]:
				self.make()
				#If the file hits the maximum size, start a new one
				if self.gpx_track.track_size > self.maxsize and self.track == True:
					self.gpx_track.track_close()
					self.gpx_track.track_size = 0
					self.gpx_track.track_start()
				self.route = []
				x = 0
			time.sleep(self.save_info[0])

	def off(self):
		'''Cleans up and closes the current track file open.'''
		if self.gpx_track:
			if self.route:
				self.make()
			#Cleans and closes track variables and files
			self.gpx_track.track_close()
			self.gpx_track = None
			self.route = []

	def make(self):
		'''Outputs the track info to the current track file.'''
		#Runs through each track point for output
		for point in self.route:
			self.gpx_track.track_point(point[0], point[1], 0, point[2])

	def distance(self):
		x = 0
		while self.distance_track == True:
			if x != 0:
				current_distance = geomath.haversine(self.cache.gps['lat'], self.cache.gps['lon'], last_point[0], last_point[1])
				print current_distance[0]
				self.distance_total = self.distance_total + current_distance[0]
				print self.distance_total
			last_point = [self.cache.gps['lat'], self.cache.gps['lon']]
			print last_point
			x = x + 1
			time.sleep(2)

	def distance_start(self):
		thread.start_new_thread(self.distance, ())

class ALARM():

	def __init__(self):
		self.xte        = False
		self.status     = False

	def check(self):
		self.status = False
		if self.xte == True:
			self.status = True


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