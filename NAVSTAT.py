#!/usr/bin/env python
#-*- coding: utf-8 -*-

import pygame
import thread
import sys
import time
import math
import datetime
import lib.nmea
import lib.gpx
import lib.geomath


class NAVSTAT():

	def __init__(self):
		pygame.init()
		#Colours that are required 
		self.black               = (   0,   0,   0)
		self.white               = ( 255, 255, 255)
		self.red                 = ( 255,   0,   0)
		self.colour_1            = self.black
		self.colour_2            = self.white
		self.colour_1_2          = self.colour_1
		self.colour_2_2          = self.colour_2
		#4 font sizes that are available
		self.font_1              = pygame.font.Font(None, 18)
		self.font_2              = pygame.font.Font(None, 30)
		self.font_3              = pygame.font.Font(None, 25)
		self.font_4              = pygame.font.Font(None, 50)
		self.navstat_mode        = 0           
		#Switches for night, tracking, and fullscreen
		self.night               = False
		self.track               = False
		self.done                = False
		self.mini                = False
		#Switches for autopilot, routing, and AIS
		self.auto                = False
		self.route               = False
		self.ais                 = False
		self.aismap_data         = None
		#Degree character required for lat/long
		self.degree              = chr(176)
		#Top speed on the speedometer
		self.speed_top           = 2
		#Pixel size of the screen
		self.size                = [0,0]
		self.frame_rate          = 29
		self.screen              = None
		self.clock               = pygame.time.Clock()
		#Compass rose x,y points
		self.compass_rose_1      = [[393,40,'N'],[278,152,'W'],[393,263,'S'],[502,152,'E']]
		self.compass_rose_2      = [[298,75,'NW'],[298,232,'SW'],[475,232,'SE'],[475,75,'NE']]
		self.compass_rose_3      = [[(400,62),(400,82)],[(471,91),(461,101)],[(500,162),(480,162)],[(471,233),(461,223)],[(400,262),(400,242)],[(329,233),(339,223)],[(300,162),(320,162)],[(329,91),(339,101)]]
		#Distance and bearing to current route point
		self.destination_info    = [0,0]
		#Base km distance to next route point - for ETA
		self.destination_distance= 0
		self.destination_eta     = ['','']
		self.destination_xte     = 0
		self.xte_alarm           = 0
		self.xte_status          = False
		#Interface lines x,y points
		self.interface_points    = [[0,22,800,22],[0,150,250,150],[0,300,250,300],[250,150,250,500],[250,0,250,150],[250,0,250,150],[250,370,800,370],[550,0,550,500],[0,465,800,465],[550,111,800,111],[550,199,800,199]] 
		#Holds track point info for future file output
		self.track_route         = []
		#Number of seconds between each track point. Number of points between each track file output.
		self.track_info          = [10,6]
		#The max size of a track file.
		self.track_maxsize       = None
		self.route_current       = [0,0,'',0,0]
		self.route_distance      = None
		self.route_eta           = None
		#File location of track files. File location of route files.
		self.gpx_location        = ['','']
		#Tracking and route object.
		self.gpx_track           = None
		self.gpx_route           = None
		#Location of GPS serial device
		self.gps_location        = None
		#Baudrate of GPS serial device
		self.gps_baudrate        = None
		#Current lat/lon position
		self.lat_lon             = [0,0]
		#Unit measurement selected. Distance, speed.
		self.unit_measure        = [0,0]
		self.unit_text           = ['','']
		self.version             = None
		self.haversine           = lib.geomath.haversine
		#Get settings
		self.settings()

	def start(self):
		'''Starts the NAVSTAT program and contains main loop.'''
		pygame.display.set_caption("NAVSTAT")
		#Checks to enabled fullscreen and colours
		self.mini_mode()
		self.night_mode()
		#Attempts to create a serial NMEA connection
		self.gpscheck()
		#Checks to enabled tracking and routing
		self.track_mode()
		self.route_mode()
		#Throws splash on screen while connecting gps
		self.splash()
		while self.nmea_connection.lat == 0 and self.nmea_connection.lon == 0:
			pass
		#Main program loop - continue until quit
		while self.done == False:
			#Checks the serial connection status
			if self.nmea_connection.exit == True:
				self.error_out('Err2: Serial connection lost. No incoming data.',210,260)
			#Checks if buttons have been pressed
			self.keyevents()
			#GPS mode enabled
			if self.navstat_mode == 0:
				self.gps_interface()
				self.gps_latlong(self.nmea_connection.lat, self.nmea_connection.lon)
				self.gps_speedometer(self.nmea_connection.speed)
				self.gps_compass(self.nmea_connection.track)
			#AIS mode enabled
			elif self.navstat_mode == 1:
				self.aismap(self.nmea_connection.track)
			self.menu()
			self.clock.tick(self.frame_rate)
			pygame.display.update()
		self.quit()

	def settings(self):
		'''Open navstat.config and load settings into respective variables'''
		settings = open('navstat.config', 'r')
		#Run through each line and load a setting
		for line in settings:
			#Line is not blank
			if line != '\n' or '' or None:
				#Line is not a comment
				if line[0:1] != '#':
					#Break up the setting name from contents
					settings_item = line.split('=')
					settings_item[1] = settings_item[1].rstrip()
					#Load settings - more info in navstat.config
					if settings_item[0] == 'frame_x':
						self.size[1] = int(settings_item[1])
					elif settings_item[0] == 'frame_y':
						self.size[0] = int(settings_item[1])
					elif settings_item[0] == 'font_1':
						self.font_1 = pygame.font.Font(None, int(settings_item[1]))
					elif settings_item[0] == 'font_2':
						self.font_2 = pygame.font.Font(None, int(settings_item[1]))
					elif settings_item[0] == 'font_3':
						self.font_3 = pygame.font.Font(None, int(settings_item[1]))
					elif settings_item[0] == 'font_4':
						self.font_4 = pygame.font.Font(None, int(settings_item[1]))
					elif settings_item[0] == 'top_speed':
						self.speed_top = int(settings_item[1])
					elif settings_item[0] == 'night_mode':
						if str(settings_item[1]) == 'OFF':
							self.night = True
						else:
							self.night = False
					elif settings_item[0] == 'track_mode':
						if str(settings_item[1]) == 'OFF':
							self.track = True
						else:
							self.track = False
					elif settings_item[0] == 'mini_mode':
						if str(settings_item[1]) == 'OFF':
							self.mini = True
						else:
							self.mini = False
					elif settings_item[0] == 'track_secs':
						self.track_info[0] = int(settings_item[1])
					elif settings_item[0] == 'track_save':
						self.track_info[1] = int(settings_item[1])
					elif settings_item[0] == 'track_location':
						self.gpx_location[0] = str(settings_item[1])
					elif settings_item[0] == 'track_maxsize':
						self.track_maxsize = int(settings_item[1])
					elif settings_item[0] == 'route_location':
						self.gpx_location[1] = str(settings_item[1])
					elif settings_item[0] == 'unit_distance':
						if str(settings_item[1]) == 'KM':
							self.unit_measure[0] = 0
						elif str(settings_item[1]) == 'MI':
							self.unit_measure[0] = 1
						elif str(settings_item[1]) == 'NM':
							self.unit_measure[0] = 2
						self.unit_text[0] = settings_item[1]
					elif settings_item[0] == 'unit_speed':
						if str(settings_item[1]) == 'KPH':
							self.unit_measure[1] = 0
						elif str(settings_item[1]) == 'MPH':
							self.unit_measure[1] = 1
						elif str(settings_item[1]) == 'NMPH':
							self.unit_measure[1] = 2
						self.unit_text[1] = settings_item[1].replace('PH','')
					elif settings_item[0] == 'gps_location':
						self.gps_location = str(settings_item[1])
					elif settings_item[0] == 'gps_baudrate':
						self.gps_baudrate = int(settings_item[1])
					elif settings_item[0] == 'version':
						self.version = settings_item[1]
					elif settings_item[0] == 'xte_alarm':
						self.xte_alarm = settings_item[1]
		settings.close()

	def gpscheck(self):
		'''Determines whether a GPS connection is available - shuts down if not.'''
		x = 0
		connection = False
		while connection == False:
			try:
				#Opens a serial connection for NMEA GPS data
				self.nmea_connection = lib.nmea.NMEA0183(self.gps_location, self.gps_baudrate, 5)
				self.nmea_connection.read()
				connection = True
			except:
				#Wait 5 secs - no serial connection - shut down
				if x == 5:
					self.error_out('Err1: There is currently no GPS connected to NAVSTAT.',175,260)
				x = x + 1

	def menu(self):
		self.txt_out((self.font_2.render(datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), True, self.colour_2)),323,475)
		pygame.draw.rect(self.screen, self.colour_2, (0,500,800,30))
		self.txt_out(self.font_3.render('GPS', True, self.colour_1),100,510)
		self.txt_out(self.font_3.render('AIS', True, self.colour_1),200,510)
		self.txt_out(self.font_3.render('ENG', True, self.colour_1),300,510)
		pygame.draw.rect(self.screen, self.colour_1, (68,500,100,10))
		if self.nmea_connection.status == 'A':
			pygame.draw.circle(self.screen, self.colour_1, (30,515), 10)
		else:
			pygame.draw.circle(self.screen, self.colour_1, (30,515), 10,1)

	def keyevents(self):
		'''Checks whether a key has been pressed and activates event if so.'''
		for event in pygame.event.get():
			#Only KEYDOWN events
			if event.type == pygame.KEYDOWN:
				#Pressed 'Escape' to quit
				if event.key == pygame.K_ESCAPE:
					self.done = True
				#Pressed 'Tab' to mini mode
				elif event.key == pygame.K_TAB:
					self.mini_mode()
				#Pressed 'Space' to night mode
				elif event.key == pygame.K_SPACE:
					self.night_mode()
				#Pressed 'T' to tracking mode
				elif event.key == pygame.K_t:
					self.track_mode()
				#Pressed 'A' to autopilot kode
				elif event.key == pygame.K_a:
					self.auto_mode()
				elif event.key == pygame.K_RIGHT:
					self.route_current = self.gpx_route.route_get()
				elif event.key == pygame.K_F1:
					self.navstat_mode = 0
				elif event.key == pygame.K_F2:
					self.navstat_mode = 1
			elif event.type == pygame.QUIT:
				self.quit()

	def splash(self):
		'''Creates a splash screen while first booting.'''
		self.screen.fill(self.colour_1)
		splash_font = pygame.font.Font(None, 60)
		self.txt_out((splash_font.render('NAVSTAT', True, self.colour_2)),300,210)
		self.txt_out((self.font_3.render('Bluewater Mechanics', True, self.colour_2)),310,260)
		self.txt_out((self.font_1.render('build ' + self.version, True, self.colour_2)),740,480)
		pygame.display.update()
		time.sleep(2)

	def gps_interface(self):
		'''Draws all the basic gps interface graphics.'''
		#Fills the background color
		self.screen.fill(self.colour_1)
		#Runs through each interface line and draws it
		for point in self.interface_points:
			pygame.draw.lines(self.screen, self.colour_2, False, [(point[0],point[1]),(point[2],point[3])], 2)
		#If tracking is on, draw it
		if self.track == True:
			self.txt_out(self.font_1.render('Tracking - ' + self.gpx_track.gpx_file, True, self.colour_2),10,480)
		if self.route == True:
			self.txt_out(self.font_1.render('Route - ' + self.gpx_route.gpx_file, True, self.colour_2),560,480)
			self.gps_destination()

	def gps_latlong(self,lat,lon):
		'''Positions and draws the lat/long interface.
		
		Keyword arguments:
		lat -- the current latitude position
		lon -- the current longitude position
		
		'''
		#Makes the current lat/lon available to the class
		self.lat_lon = [lat, lon]
		#Cuts the decimal count down to 5
		lat_out = ("%.5f" % lat)
		lon_out = ("%.5f" % lon)
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
		self.txt_out((self.font_3.render('POS', True, self.colour_2)),107,0)
		self.txt_out((self.font_4.render(lat_out, True, self.colour_2)),20 + ext_1,30)
		self.txt_out((self.font_4.render(lon_out, True, self.colour_2)),20 + ext_2,75)

	def gps_destination(self):
		'''Positions and draws destination interface.'''
		lat_1 = self.lat_lon[0]
		lon_1 = self.lat_lon[1]
		lat_2 = self.route_current[0]
		lon_2 = self.route_current[1]
		#Positions destination distance text based on length
		if self.destination_info[0] >= 0 and self.destination_info[0] < 10:
			ext1 = 40
		elif self.destination_info[0] >= 10 and self.destination_info[0] < 100:
			ext1 = 34
		elif self.destination_info[0] >= 100 and self.destination_info[0] < 1000:
			ext1 = 24
		elif self.destination_info[0] >= 1000 and self.destination_info[0] < 10000:
			ext1 = 14
		elif self.destination_info[0] >= 10000 and self.destination_info[0] < 100000:
			ext1 = 0
		#Positions destination bearing text based on length
		if self.destination_info[1] < 10:
			ext2 = 14
		elif self.destination_info[1] >= 10 and self.destination_info[1] < 100:
			ext2 = 7
		elif self.destination_info[1] > 100:
			ext2 = 0
		#Draws the destination interface text
		self.txt_out((self.font_3.render('NXT', True, self.colour_2)),655,347)
		self.txt_out((self.font_3.render('DST', True, self.colour_2)),385,347)
		self.txt_out((self.font_4.render(str(self.destination_info[0]) + ' ' + self.unit_text[0], True, self.colour_2)),300 + ext1,418)
		self.txt_out((self.font_4.render(str(self.destination_info[1]).replace('.0','') + self.degree, True, self.colour_2)),370 + ext2,378)
		#Positions and draws crosstrack error interface.
		#Positions xte text based on length
		if self.destination_xte < 10:
			ext3 = 14
		elif self.destination_xte >= 10 and self.destination_xte < 100:
			ext3 = 7
		elif self.destination_xte > 100:
			ext3 = 0
		self.txt_out((self.font_3.render('XTE', True, self.colour_2)),655,0)
		self.txt_out((self.font_4.render(str(self.destination_xte) + ' ' + self.unit_text[0], True, self.colour_2)),615 + ext3,30)
		if self.xte_status == True:
			print 'hello'
		#Positions and draws the RTA interface.
		self.txt_out((self.font_3.render('RTA', True, self.colour_2)),655,88)
		self.txt_out((self.font_2.render(self.route_eta, True, self.colour_2)),600,125)
		#Positions and draws the DTA interface.
		self.txt_out((self.font_3.render('DTA', True, self.colour_2)),655,176)
		self.txt_out((self.font_4.render(self.destination_eta[0] + 'h' + ' : ' + self.destination_eta[1] + 'm', True, self.colour_2)),615,206)

	def gps_speedometer(self, speed_out):
		'''Positions and draws the speedometer interface.
		
		Keyword arguments:
		speed_out -- the current vessel speed
		
		'''
		#Rounds and converts speed to unit setting
		speed_out = round(self.unit_convert(1,speed_out),1)
		#Determines speedometer position based on top speed
		speed_meter = (speed_out*220)/self.speed_top
		if speed_meter > 220:
			speed_meter = 220
		#Draws the speedometer interface
		pygame.draw.rect(self.screen, self.colour_2, (15,210,220,40), 1)
		pygame.draw.rect(self.screen, self.colour_2, (15,210,speed_meter,40))
		self.txt_out((self.font_3.render('SOG', True, self.colour_2)),107,128)
		self.txt_out((self.font_4.render(str(speed_out) + ' ' + self.unit_text[1], True, self.colour_2)),100,158)
		self.txt_out((self.font_1.render(str(self.speed_top), True, self.colour_2)),220,253)
		self.txt_out((self.font_1.render(str(self.speed_top/2), True, self.colour_2)),116,253)
		self.txt_out((self.font_1.render('0', True, self.colour_2)),15,253)

	def gps_compass(self, compass_out):
		'''Positions and draws the compass interface.
		
		Keyword arguments:
		compass_out -- the current vessel heading
		
		'''
		#Determines the x,y position on compass circumference in relation to degrees
		compass_main = self.calc_line(compass_out,100,400,162)
		#Draws the compass rose
		for point in self.compass_rose_1:
			self.txt_out(self.font_2.render(point[2], True, self.colour_2),point[0],point[1])
		for point in self.compass_rose_2:
			self.txt_out(self.font_3.render(point[2], True, self.colour_2),point[0],point[1])
		for point in self.compass_rose_3:
			pygame.draw.lines(self.screen, self.colour_2, False, point, 3)
		#Repositions degree text based on size
		if compass_out < 10: 
			ext = 14
		elif compass_out >= 100:
			ext = 0
		else:
			ext = 7
		#If routing is enabled, draws the current destination line 
		if self.route == True:
			compass_destination = self.calc_line(self.destination_info[1],100,400,162)
			pygame.draw.lines(self.screen, self.colour_2, False, [(400,162),(compass_destination[0],compass_destination[1])], 1)
		#Draws the compass interface
		self.txt_out((self.font_3.render('COG', True, self.colour_2)),380,0)
		pygame.draw.circle(self.screen, self.colour_2, (400,162), 5)
		pygame.draw.circle(self.screen, self.colour_2, (400,162), 100,1)
		pygame.draw.lines(self.screen, self.colour_2, False, [(400,162),(compass_main[0],compass_main[1])], 5)
		self.txt_out((self.font_4.render(str(round(compass_out)).replace('.0','') + self.degree, True, self.colour_2)),370+ext,290)

	def calc_line(self,degree,radius,x,y):
		'''Calculates the x,y coordinates of a point within a circle circumference based on degrees.
		
		Keyword arguments:
		degree -- the degree to calculate upon
		radius -- the radius of the circle
		x -- the x position of the circle centre
		y -- the y position of the circle centre
		
		'''
		rad = math.radians(degree)
		x = int(round(x + radius * math.sin(rad)))
		y = int(round(y - radius * math.cos(rad)))
		return [x,y]

	def aismap(self,compass_out):
		self.screen.fill(self.colour_1)
		self.aismap_data = [[121334543,44.54204,-80.03334, 175.0],[12123232,44.50679,-79.84108, 228.0],[12123232,44.42924,-79.97292, 115.0],[12123232,44.50471,-80.19505, 10.0]]
		for vessel in self.aismap_data:
			vessel_data = self.haversine(self.nmea_connection.lat,self.nmea_connection.lon,vessel[1],vessel[2])
			if vessel_data[0] < 20:
				vessel_distance = round(vessel_data[0]*10,1)
				vessel_position = self.calc_line(vessel_data[1],vessel_distance,400,225)
				vessel_cog = self.calc_line(vessel[3],12,vessel_position[0],vessel_position[1])
				pygame.draw.circle(self.screen, self.colour_2, (vessel_position[0],vessel_position[1]), 2)
				pygame.draw.circle(self.screen, self.colour_2, (vessel_position[0],vessel_position[1]), 12, 1)
				pygame.draw.lines(self.screen, self.colour_2, False, [(vessel_position[0],vessel_position[1]),(vessel_cog[0],vessel_cog[1])], 1)
		compass_main = self.calc_line(compass_out,200,400,225)
		pygame.draw.circle(self.screen, self.colour_2, (400,225), 200,1)
		pygame.draw.lines(self.screen, self.colour_2, False, [(400,225),(compass_main[0],compass_main[1])], 3)


	def route_start(self):
		'''Used to keep track of current position in relation to current route - run as thread.'''
		#Gets the next route position, and the next five
		self.route_current = self.gpx_route.route_get()
		#Run while routing is enabled
		while self.route == True:
			#Calculates distance between current position, and destination point
			self.destination_info = self.haversine(self.lat_lon[0],self.lat_lon[1],self.route_current[0],self.route_current[1])
			#Provides a non unit converted distance
			self.destination_distance = self.destination_info[0]
			#Converts to selected unit
			self.destination_info[0] = self.unit_convert(0,self.destination_info[0])
			#Calculates total route distance
			self.route_distance = self.destination_info[0] + self.unit_convert(0,self.gpx_route.route_distance)
			#We're close to the destination - get the next point
			if self.destination_info[0] < 0.02:
				self.route_current = self.gpx_route.route_get()
			time.sleep(1)

	def arrival_start(self):
		'''Calculates the estimated arrival time based on current speed - run as thread.'''
		#Loops until routing is turned off
		while self.route == True:
			speed = self.nmea_connection.speed
			#Make sure we do not divide by zero
			if speed > 0:
				#Converts the standard NM/H speed into KM/H
				speed = round(speed*1.852,2)
				time_current = datetime.datetime.now()
				#Determine time required for whole route
				time_total = (self.destination_distance + self.gpx_route.route_distance) / speed
				time_total_min, time_total_hour = math.modf(time_total)
				time_total_min = round(time_total_min*60)
				#Create a date/time object for ETA
				time_total = time_current + datetime.timedelta(hours=time_total_hour, minutes=time_total_min)
				self.route_eta = time_total.strftime("%Y-%m-%d %H:%M")
				#Determine time required for next point in route
				time_point = self.destination_distance / speed
				time_point_min, time_point_hour = math.modf(time_point)
				time_point_min = round(time_point_min*60)
				#Add a 0 if minutes are less then 10
				if time_point_min < 10:
					time_point_min = '0' + str(time_point_min)
				#Remove decimal points
				self.destination_eta[0] = str(time_point_hour).replace('.0','')
				self.destination_eta[1] = str(time_point_min).replace('.0','') 
				time.sleep(5)
			#Do not estimate times if speed is 0
			else:
				self.route_eta = '--'
				self.destination_eta[0] = '-'
				self.destination_eta[1] = '--'

	def crosstrack_start(self):
		'''Calculates the crosstrack error for the current destination - run as thread.'''
		#Loops until routing is turned off
		while self.route == True:
			#Make sure this is not the first point in the route (no standard bearing)
			if self.gpx_route.route_points[0][0] != self.route_current[0]:
				#Gets haversine info of last route point
				hav_start = self.haversine(self.gpx_route.route_points[self.gpx_route.route_position - 1][0], self.gpx_route.route_points[self.gpx_route.route_position - 1][1], self.lat_lon[0], self.lat_lon[1])
				self.destination_xte = math.asin(math.sin(hav_start[0]/6378.137)*math.sin(hav_start[1]-self.gpx_route.route_points[self.gpx_route.route_position - 1][4]))*6378.137
				self.destination_xte = self.unit_convert(0,self.destination_xte)
				if self.destination_xte < 0:
					self.destination_xte = self.destination_xte*(-1)
			else:
				self.destination_xte = '--'
			if self.destination_xte >= self.xte_alarm:
				if self.xte_status == True:
					self.xte_status == False
				elif self.xte_status == False:
					self.xte_status == True
			time.sleep(1)

	def ais_start(self):
		while self.ais == True:
			return

	def auto_start(self):
		while self.auto == True:
			return

	def track_start(self):
		'''Used as a thread to save tracking info for future file output.'''
		x = 0
		#Loop that keeps track of time, and saves track info based on this time
		while self.track == True:
			self.track_route.append([self.lat_lon,self.nmea_connection.utc])
			x = x + 1
			if x > self.track_info[1]:
				self.track_make()
				#If the file hits the maximum size, start a new one
				if self.gpx_track.track_size > self.track_maxsize and self.track == True:
					self.gpx_track.track_close()
					self.gpx_track.track_size = 0
					self.gpx_track.track_start()
				self.track_route = []
				x = 0
			time.sleep(self.track_info[0])

	def track_make(self):
		'''Outputs the track info to the current track file.'''
		#Runs through each track point for output
		for point in self.track_route:
			self.gpx_track.track_point(point[0][0], point[0][1], 0, point[1])

	def night_mode(self):
		'''Checks whether Night Mode is enabled, and changes colour scheme to match.'''
		if self.night == False:
			self.colour_1 = self.black
			self.colour_2 = self.red
			self.night = True
		elif self.night == True:
			self.colour_1 = self.colour_1_2
			self.colour_2 = self.colour_2_2
			self.night = False

	def route_mode(self):
		'''Checks whether Route Mode is enabled, and starts a routing thread if so.'''
		if self.route == False:
			self.route = True
			self.gpx_route = lib.gpx.GPX(self.gpx_location[1])
			self.gpx_route.route_start('ride somewhere.gpx')
			thread.start_new_thread(self.route_start, ())
			thread.start_new_thread(self.arrival_start, ())
			thread.start_new_thread(self.crosstrack_start, ())

		else:
			self.route = False

	def track_mode(self):
		'''Checks whether Track Mode is enabled, and starts a tracking thread if so.'''
		if self.track == False:
			self.track = True
			self.gpx_track = lib.gpx.GPX(self.gpx_location[0])
			self.gpx_track.track_start()
			thread.start_new_thread(self.track_start, ())
		else:
			self.track = False
			self.track_off()

	def track_off(self):
		'''Cleans up and closes the current track file open.'''
		if self.gpx_track:
			if self.track_route:
				self.track_make()
			#Cleans and closes track variables and files
			self.gpx_track.track_close()
			self.gpx_track = None
			self.track_route = []

	def mini_mode(self):
		'''Checks whether Mini Mode is enabled, and alters screen size if so.'''
		if self.mini == False: 
			self.screen = pygame.display.set_mode(self.size,pygame.RESIZABLE)
			self.mini = True
		else: 
			self.screen = pygame.display.set_mode(self.size,pygame.FULLSCREEN)
			self.mini = False

	def auto_mode(self):
		'''Checks whether Auto Mode is enabled, and turns it on if so.'''
		if self.auto == False: 
			thread.start_new_thread(self.auto_start, ())
			self.auto = True
		else: 
			self.auto = False

	def txt_out(self,text, x, y):
		'''Gets pygame text ready to be outputted on screen.
		
		Keyword arguments:
		text -- the text that will be outputted
		x -- the horizontal position of the text
		y -- the vertical position of the text
		
		'''
		self.screen.blit(text, [x,y])

	def unit_convert(self,type,num):
		'''Converts unit output units to the units of choice.
		
		Keyword arguments:
		type -- The type of unit to convert, distance = 0, speed = 1.
		num -- The number that needs to be converted.
		
		'''
		#This converts distance to choice of unit. Starts in km.
		if type == 0:
			#Kilometers
			if self.unit_measure[0] == 0:
				return num
			#Miles
			elif self.unit_measure[0] == 1:
				return round(num*0.621371,2)
			#Nautical Miles
			elif self.unit_measure[0] == 2:
				return round(num*0.539957,2)
		#This converts speed to choice of unit. Starts in knots.
		elif type == 1:
			#Kilometers / Hour
			if self.unit_measure[1] == 0:
				return round(num*1.852,2)
			#Miles / Hour
			elif self.unit_measure[1] == 1:
				return round(num*1.15078,2)
			#Nautical Miles / Hour
			elif self.unit_measure[1] == 2:
				return num

	def error_out(self,error_text, x, y):
		'''Creates an error splash screen to output error detail.
		
		Keyword arguments:
		error_text -- the error number and text details
		x -- the x position of the text
		y -- the y position of the text
		
		'''
		while True:
			self.screen.fill(self.colour_1)
			self.txt_out((self.font_2.render('Error', True, self.colour_2)),375,230)
			self.txt_out((self.font_3.render(error_text, True, self.colour_2)),x,y)
			pygame.display.update()
			for event in pygame.event.get():
				if event.type == pygame.KEYDOWN:
					#Pressed 'Escape' to quit
					if event.key == pygame.K_ESCAPE:
						self.quit()
				if event.type == pygame.QUIT:
					self.quit()

	def quit(self):
		'''Gets NAVSTAT ready to quit.'''
		self.screen.fill(self.colour_1)
		self.txt_out((self.font_3.render('Exiting cleanly...', True, self.colour_2)),355,128)
		pygame.display.flip()
		try:
			#Closes GPS serial connection
			self.nmea_connection.quit()
		except:
			pass
		#Closes any open track files
		self.track_off()
		time.sleep(2)
		pygame.quit()
		sys.exit()

#import cProfile

gps = NAVSTAT()
gps.start()
#cProfile.run('gps.start()')


