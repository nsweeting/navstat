#!/usr/bin/env python
#-*- coding: utf-8 -*-

import pygame
import thread
import sys
import time
import datetime
import lib.nmea
import lib.gpx
import lib.gps
import lib.geomath
import lib.alarm


class NAVSTAT():

	def __init__(self):
		pygame.init()
		#Colours that are required 
		self.ui_black            = (   0,   0,   0)
		self.ui_white            = ( 255, 255, 255)
		self.ui_red              = ( 255,   0,   0)
		self.ui_colour_1         = self.ui_black
		self.ui_colour_2         = self.ui_white
		self.ui_colour_1_2       = self.ui_colour_1
		self.ui_colour_2_2       = self.ui_colour_2
		#4 font sizes that are available
		self.ui_font_1           = pygame.font.Font(None, 18)
		self.ui_font_2           = pygame.font.Font(None, 30)
		self.ui_font_3           = pygame.font.Font(None, 25)
		self.ui_font_4           = pygame.font.Font(None, 50)
		#Switches for night, exit and fullscreen
		self.ui_night            = False
		self.ui_mini             = False
		self.ui_exit             = False
		#Pixel size of the screen, frame rate
		self.ui_size             = [0,0]
		self.ui_frame_rate       = 29
		self.ui_screen           = None
		self.ui_clock            = pygame.time.Clock()
		self.navstat_mode        = 0           
		#Switches for autopilot, routing, and AIS
		self.auto                = False
		self.ais                 = False
		self.aismap_data         = None
		#Degree character required for lat/long
		self.degree              = chr(176)
		#Top speed on the speedometer
		self.speed_top           = 2
		self.eng_tach_rose_1     = [[395,263,'0'],[273,152,'10'],[389,38,'20'],[506,152,'30']]
		self.eng_tach_rose_2     = [[312,232,'5'],[298,75,'15'],[476,71,'25'],[475,232,'35']]
		#Compass rose x,y points
		self.gps_compass_rose_1  = [[393,40,'N'],[278,152,'W'],[393,263,'S'],[502,152,'E']]
		self.gps_compass_rose_2  = [[298,75,'NW'],[298,232,'SW'],[475,232,'SE'],[475,75,'NE']]
		self.gps_compass_rose_3  = [[(400,62),(400,82)],[(471,91),(461,101)],[(500,162),(480,162)],[(471,233),(461,223)],[(400,262),(400,242)],[(329,233),(339,223)],[(300,162),(320,162)],[(329,91),(339,101)]]
		#File location of track files and of route files
		self.gpx_location        = ['','']
		#Location and baudrate of GPS serial device
		self.gps_info            = [None,None]
		#Unit measurement selected. Distance, speed.
		self.unit_measure        = [0,0]
		self.unit_text           = ['','']
		self.version             = None
		self.haversine           = lib.geomath.haversine
		self.calc_line           = lib.geomath.calc_line
		self.unit_convert        = lib.geomath.unit_convert
		self.calc_size           = lib.geomath.calc_size
		self.cache               = lib.nmea.CACHE()
		self.alarm               = lib.alarm.ALARM()
		self.route               = lib.gps.ROUTE(self.cache, self.alarm)
		self.track               = lib.gps.TRACK(self.cache)
		#Get settings
		self.settings()

	##############################################################
	##### NAVSTAT RELATED ########################################
	##############################################################

	def start(self):
		'''Starts the NAVSTAT program and contains main loop.'''
		pygame.display.set_caption("NAVSTAT")
		#Checks to enable fullscreen and colours
		self.mini_mode()
		self.night_mode()
		#Attempts to create a serial NMEA connection
		self.gps_check()
		#Throws splash on screen
		self.splash()
		#Main program loop - continue until quit
		while self.ui_exit == False:
			#Checks if buttons have been pressed
			self.keyevents()
			#Checks if any alarms have been activated
			self.alarm.check()
			#GPS mode enabled
			if self.navstat_mode == 0:
				if self.nmea_connection.exit == False:
					self.cache.cache_gps(self.nmea_connection.data_gps['lat'], self.nmea_connection.data_gps['lon'], self.nmea_connection.data_gps['speed'], self.nmea_connection.data_gps['track'], self.nmea_connection.data_gps['utc'], self.nmea_connection.data_gps['status'])
					self.gps_interface()
					self.gps_latlong()
					self.gps_speedometer()
					self.gps_compass()
					self.gps_destination()
				else:
					self.gps_error()
			#AIS mode enabled
			elif self.navstat_mode == 1:
				self.cache.cache_gps(self.nmea_connection.data_gps['lat'], self.nmea_connection.data_gps['lon'], self.nmea_connection.data_gps['speed'], self.nmea_connection.data_gps['track'], self.nmea_connection.data_gps['utc'], self.nmea_connection.data_gps['status'])
				self.map_interface()
			elif self.navstat_mode == 2:
				self.aismap(self.nmea_connection.track)
			elif self.navstat_mode == 3:
				self.eng_interface()
				self.eng_tachometer()
			self.menu()
			self.ui_clock.tick(self.ui_frame_rate)
			pygame.display.update()
			#Reduces CPU utilization with no significant performance decrease
			time.sleep(0.3)
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
						self.ui_size[1] = int(settings_item[1])
					elif settings_item[0] == 'frame_y':
						self.ui_size[0] = int(settings_item[1])
					elif settings_item[0] == 'top_speed':
						self.speed_top = int(settings_item[1])
					elif settings_item[0] == 'night_mode':
						if str(settings_item[1]) == 'OFF':
							self.ui_night = True
						else:
							self.ui_night = False
					elif settings_item[0] == 'track_mode':
						if str(settings_item[1]) == 'OFF':
							self.track.mode = True
						else:
							self.track.mode = False
					elif settings_item[0] == 'mini_mode':
						if str(settings_item[1]) == 'OFF':
							self.ui_mini = True
						else:
							self.ui_mini = False
					elif settings_item[0] == 'track_secs':
						self.track.save_info[0] = int(settings_item[1])
					elif settings_item[0] == 'track_save':
						self.track.save_info[1] = int(settings_item[1])
					elif settings_item[0] == 'track_location':
						self.gpx_location[0] = str(settings_item[1])
					elif settings_item[0] == 'track_maxsize':
						self.track.maxsize = int(settings_item[1])
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
						self.gps_info[0] = str(settings_item[1])
					elif settings_item[0] == 'gps_baudrate':
						self.gps_info[1] = int(settings_item[1])
					elif settings_item[0] == 'version':
						self.version = settings_item[1]
					elif settings_item[0] == 'xte_alarm':
						self.xte_alarm = settings_item[1]
		settings.close()

	def menu(self):
		'''Draws the menu interface common between all functions.'''
		#Display current time
		self.txt_out((self.ui_font_2.render(datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), True, self.ui_colour_2)),323,472)
		pygame.draw.rect(self.ui_screen, self.ui_colour_2, (0,500,800,30))
		pygame.draw.lines(self.ui_screen, self.ui_colour_2, False, [(0,465),(800,465)], 2)
		#Draw the various screen display options
		self.txt_out(self.ui_font_3.render('GPS', True, self.ui_colour_1),100,510)
		self.txt_out(self.ui_font_3.render('MAP', True, self.ui_colour_1),200,510)
		self.txt_out(self.ui_font_3.render('AIS', True, self.ui_colour_1),300,510)
		self.txt_out(self.ui_font_3.render('ENG', True, self.ui_colour_1),400,510)
		self.txt_out(self.ui_font_3.render('OFF', True, self.ui_colour_1),500,510)
		pygame.draw.rect(self.ui_screen, self.ui_colour_1, (68,500,100,10))
		#Monitors GPS status and displays problems
		if self.cache.gps['status'] == 'A':
			pygame.draw.circle(self.ui_screen, self.ui_colour_1, (30,515), 10)
		else:
			pygame.draw.circle(self.ui_screen, self.ui_colour_1, (30,515), 10,1)
		if self.alarm.status == True:
			self.txt_out(self.ui_font_3.render('!!!!', True, self.ui_colour_1),770,510)

	def keyevents(self):
		'''Checks whether a key has been pressed and activates event if so.'''
		for event in pygame.event.get():
			#Only KEYDOWN events
			if event.type == pygame.KEYDOWN:
				#Pressed 'Escape' to quit
				if event.key == pygame.K_ESCAPE:
					self.ui_exit = True
				#Pressed 'Tab' to mini mode
				elif event.key == pygame.K_TAB:
					self.mini_mode()
				#Pressed 'Space' to night mode
				elif event.key == pygame.K_SPACE:
					self.night_mode()
				#Pressed 'T' to tracking mode
				elif event.key == pygame.K_t:
					self.track.switch(self.gpx_location[0])
				#Pressed 'A' to autopilot kode
				elif event.key == pygame.K_a:
					self.auto_mode()
				#Pressed 'Right' to move forward on route
				elif event.key == pygame.K_RIGHT:
					self.route.get(0)
				#Pressed 'Left' to move backward on route
				elif event.key == pygame.K_LEFT:
					self.route.get(1)
				elif event.key == pygame.K_F1:
					self.navstat_mode = 0
				elif event.key == pygame.K_F2:
					self.navstat_mode = 1
				elif event.key == pygame.K_F4:
					self.navstat_mode = 3
			elif event.type == pygame.QUIT:
				self.quit()

	def splash(self):
		'''Creates a splash screen while first booting.'''
		self.ui_screen.fill(self.ui_colour_1)
		splash_font = pygame.font.Font(None, 60)
		self.txt_out((splash_font.render('NAVSTAT', True, self.ui_colour_2)),300,210)
		self.txt_out((self.ui_font_3.render('Bluewater Mechanics', True, self.ui_colour_2)),310,260)
		self.txt_out((self.ui_font_1.render('version ' + self.version, True, self.ui_colour_2)),740,480)
		pygame.display.update()
		time.sleep(2)
		self.ui_screen.fill(self.ui_colour_1)

	def night_mode(self):
		'''Checks whether Night Mode is enabled, and changes colour scheme to match.'''
		if self.ui_night == False:
			self.ui_colour_1 = self.ui_black
			self.ui_colour_2 = self.ui_red
			self.ui_night = True
		elif self.ui_night == True:
			self.ui_colour_1 = self.ui_colour_1_2
			self.ui_colour_2 = self.ui_colour_2_2
			self.ui_night = False

	def mini_mode(self):
		'''Checks whether Mini Mode is enabled, and alters screen size if so.'''
		if self.ui_mini == False: 
			self.ui_screen = pygame.display.set_mode(self.ui_size,pygame.RESIZABLE)
			self.ui_mini = True
		else: 
			self.ui_screen = pygame.display.set_mode(self.ui_size,pygame.FULLSCREEN)
			self.ui_mini = False

	##############################################################
	##### GPS RELATED ############################################
	##############################################################

	def gps_check(self):
		'''Determines whether a GPS connection is available.'''
		x = 0
		connection = False
		#Readies a serial connection for NMEA GPS data
		self.nmea_connection = lib.nmea.NMEA0183(self.gps_info[0], self.gps_info[1], 5)
		while connection == False:
			try:
				#Attempts to make a serial connection
				self.nmea_connection.read()
				connection = True
				#Waits until a proper data stream is available
				while self.nmea_connection.data_gps['lat'] == 0 and self.nmea_connection.data_gps['lon'] == 0:
					pass
			except:
				#Try 5 times - no serial connection - shut down
				if x == 5:
					self.nmea_connection.exit = True
					connection = True
				x = x + 1
		if self.nmea_connection.exit == False:
			self.track.switch(self.gpx_location[0])
			self.route.switch(self.gpx_location[1])
		else:
			self.track.mode = False
			self.route.mode = False

	def gps_interface(self):
		'''Draws all the basic gps interface graphics.'''
		#Fills the background color
		self.ui_screen.fill(self.ui_colour_1)
		#Draws the interface lines
		pygame.draw.lines(self.ui_screen, self.ui_colour_2, False, [(250,0),(250,550)], 2)
		pygame.draw.lines(self.ui_screen, self.ui_colour_2, False, [(550,0),(550,500)], 2)
		#If tracking is on, draw it
		if self.track.mode == True:
			self.txt_out(self.ui_font_1.render('Tracking - ' + self.track.gpx_track.gpx_file, True, self.ui_colour_2),10,477)
		if self.route.mode == True:
			self.txt_out(self.ui_font_1.render('Route - ' + self.route.gpx_route.gpx_file, True, self.ui_colour_2),560,477)
			self.gps_destination()

	def gps_latlong(self):
		'''Positions and draws the lat/long interface.
		
		Keyword arguments:
		lat -- the current latitude position
		lon -- the current longitude position
		
		'''
		#Draws the basic latlon interface
		pygame.draw.rect(self.ui_screen, self.ui_colour_2, (0,0,250,20))
		self.txt_out((self.ui_font_3.render('POS', True, self.ui_colour_1)),107,0)
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
		self.txt_out((self.ui_font_4.render(lat_out, True, self.ui_colour_2)),20 + ext_1,30)
		self.txt_out((self.ui_font_4.render(lon_out, True, self.ui_colour_2)),20 + ext_2,75)

	def gps_destination(self):
		'''Positions and draws destination interface.'''
		#Positions and draws the route interface
		pygame.draw.rect(self.ui_screen, self.ui_colour_2, (250,350,300,20))
		pygame.draw.rect(self.ui_screen, self.ui_colour_2, (550,0,250,20))
		pygame.draw.rect(self.ui_screen, self.ui_colour_2, (550,85,250,20))
		pygame.draw.rect(self.ui_screen, self.ui_colour_2, (550,288,250,20))
		pygame.draw.rect(self.ui_screen, self.ui_colour_2, (550,376,250,20))
		self.txt_out((self.ui_font_3.render('WPT', True, self.ui_colour_1)),385,350)
		self.txt_out((self.ui_font_3.render('WTA', True, self.ui_colour_1)),655,376)
		self.txt_out((self.ui_font_3.render('XTE', True, self.ui_colour_1)),655,0)
		self.txt_out((self.ui_font_3.render('XTA', True, self.ui_colour_1)),655,85)
		self.txt_out((self.ui_font_3.render('RTA', True, self.ui_colour_1)),655,288)
		if self.route.mode == True:
			#Gets current waypoint info for storage
			wpt_distance = self.unit_convert(self.unit_measure,0,self.route.waypoint_calc['distance'])
			wpt_xte = [self.unit_convert(self.unit_measure,0,self.route.waypoint_xte[0]),self.route.waypoint_xte[1]]
			wpt_bearing = self.route.waypoint_calc['bearing']
			#Positions destination distance and bearing text based on length
			ext1 = self.calc_size(wpt_distance)
			ext2 = self.calc_size(wpt_bearing)
			ext3 = self.calc_size(wpt_xte[0])
			#Draws the waypoint bearing info
			self.txt_out((self.ui_font_4.render(str(wpt_distance) + ' ' + self.unit_text[0], True, self.ui_colour_2)),300 + ext1,418)
			self.txt_out((self.ui_font_4.render(str(wpt_bearing).replace('.0','') + self.degree, True, self.ui_colour_2)),343 + ext2,378)
			#Positions and draws crosstrack error interface
			#Positions xte text based on length
			self.txt_out((self.ui_font_4.render(wpt_xte[1] + str(wpt_xte[0]) + ' ' + self.unit_text[0], True, self.ui_colour_2)),555 + ext3,30)
			#Positions and draws the RTA info.
			self.txt_out((self.ui_font_2.render(self.route.total_eta, True, self.ui_colour_2)),600,325)
			#WTA hours too large to display
			if self.route.waypoint_eta['hour'] == '1000':
				self.txt_out((self.ui_font_4.render('1000h +', True, self.ui_colour_2)),615,406)
			else:
				#Positions and draws the WTA info
				ext = self.calc_size(self.route.waypoint_eta['hour'])
				self.txt_out((self.ui_font_4.render(str(self.route.waypoint_eta['hour']) + 'h' + ' : ' + self.route.waypoint_eta['min'] + 'm', True, self.ui_colour_2)),565 + ext,406)
			#Draw crosstrack angle if available
			if self.route.waypoint_xte[1] != '':
				self.gps_xtaline()

	def gps_speedometer(self):
		'''Positions and draws the speedometer interface.
		
		Keyword arguments:
		speed_out -- the current vessel speed
		
		'''
		#Draws the basic speedometer interface
		pygame.draw.rect(self.ui_screen, self.ui_colour_2, (0,128,250,20))
		self.txt_out((self.ui_font_3.render('SOG', True, self.ui_colour_1)),107,128)
		#Rounds and converts speed to unit setting
		speed_out = round(self.unit_convert(self.unit_measure,1,self.cache.gps['speed']),1)
		#Determines speedometer position based on top speed
		speed_meter = (speed_out*220)/self.speed_top
		if speed_meter > 220:
			speed_meter = 220
		ext = self.calc_size(speed_out)
		#Draws the speedometer interface
		pygame.draw.rect(self.ui_screen, self.ui_colour_2, (15,210,220,40), 1)
		pygame.draw.rect(self.ui_screen, self.ui_colour_2, (15,210,speed_meter,40))
		self.txt_out((self.ui_font_4.render(str(speed_out) + ' ' + self.unit_text[1], True, self.ui_colour_2)),30 + ext,158)
		self.txt_out((self.ui_font_1.render(str(self.speed_top), True, self.ui_colour_2)),220,253)
		self.txt_out((self.ui_font_1.render(str(self.speed_top/2), True, self.ui_colour_2)),116,253)
		self.txt_out((self.ui_font_1.render('0', True, self.ui_colour_2)),15,253)

	def gps_compass(self):
		'''Positions and draws the compass interface.'''
		#Draws the basic compass interface
		pygame.draw.rect(self.ui_screen, self.ui_colour_2, (250,0,300,20))
		self.txt_out((self.ui_font_3.render('COG', True, self.ui_colour_1)),380,0)
		#Determines the x,y position on compass circumference in relation to degrees
		compass_out = self.cache.gps['track'] 
		compass_main = self.calc_line(compass_out,100,400,162)
		#Draws the compass rose
		for point in self.gps_compass_rose_1:
			self.txt_out(self.ui_font_2.render(point[2], True, self.ui_colour_2),point[0],point[1])
		for point in self.gps_compass_rose_2:
			self.txt_out(self.ui_font_3.render(point[2], True, self.ui_colour_2),point[0],point[1])
		for point in self.gps_compass_rose_3:
			pygame.draw.lines(self.ui_screen, self.ui_colour_2, False, point, 3)
		#Repositions degree text based on size
		ext = self.calc_size(compass_out)
		#If routing is enabled, draws the current destination line 
		if self.route.mode == True:
			compass_destination = self.calc_line(self.route.waypoint_calc['bearing'],100,400,162)
			pygame.draw.lines(self.ui_screen, self.ui_colour_2, False, [(400,162),(compass_destination[0],compass_destination[1])], 1)
		#Draws the compass interface
		pygame.draw.circle(self.ui_screen, self.ui_colour_2, (400,162), 5)
		pygame.draw.circle(self.ui_screen, self.ui_colour_2, (400,162), 100,1)
		pygame.draw.lines(self.ui_screen, self.ui_colour_2, False, [(400,162),(compass_main[0],compass_main[1])], 5)
		self.txt_out((self.ui_font_4.render(str(round(compass_out)).replace('.0','') + self.degree, True, self.ui_colour_2)),342 + ext,290)

	def gps_xtaline(self):
		pygame.draw.polygon(self.ui_screen, self.ui_colour_2, [(675,240),(669,260),(681,260)],1)
		pygame.draw.circle(self.ui_screen, self.ui_colour_2, (self.route.xte_angle[1][0],self.route.xte_angle[1][1]), 4)
		#Standard measurement lines
		pygame.draw.lines(self.ui_screen, self.ui_colour_2, False, [(self.route.xte_angle[0],240),(self.route.xte_angle[0],170)], 1)
		pygame.draw.lines(self.ui_screen, self.ui_colour_2, False, [(675,170),(self.route.xte_angle[0],170)], 1)
		pygame.draw.lines(self.ui_screen, self.ui_colour_2, False, [(675,240),(self.route.xte_angle[0],170)], 1)
		#Angle lines
		pygame.draw.lines(self.ui_screen, self.ui_colour_2, False, [(self.route.xte_angle[0],170),(self.route.xte_angle[1][0],self.route.xte_angle[1][1])], 3)
		pygame.draw.lines(self.ui_screen, self.ui_colour_2, False, [(self.route.xte_angle[0],170),(self.route.xte_angle[3][0],self.route.xte_angle[3][1])], 3)
	
	def gps_error(self):
		self.ui_screen.fill(self.ui_colour_1)
		self.txt_out((self.ui_font_2.render('There is currently no GPS connected.', True, self.ui_colour_2)),323,472)
		self.gps_check()

	##############################################################
	##### ENG RELATED ############################################
	##############################################################
	
	def eng_interface(self):
		'''Draws all the basic engine interface graphics.'''
		#Fills the background color
		self.ui_screen.fill(self.ui_colour_1)
		#Draws the interface lines
		pygame.draw.lines(self.ui_screen, self.ui_colour_2, False, [(250,0),(250,550)], 2)
		pygame.draw.lines(self.ui_screen, self.ui_colour_2, False, [(550,0),(550,500)], 2)
		pygame.draw.lines(self.ui_screen, self.ui_colour_2, False, [(0,465),(800,465)], 2)

	def eng_tachometer(self):
		'''Positions and draws the tachometer interface.'''
		rpm = 2100
		#Draws t he basic compass interface
		pygame.draw.rect(self.ui_screen, self.ui_colour_2, (250,0,300,20))
		self.txt_out((self.ui_font_3.render('TAC', True, self.ui_colour_1)),380,0)
		#Draws the tachometer rose
		for point in self.eng_tach_rose_1:
			self.txt_out(self.ui_font_2.render(point[2], True, self.ui_colour_2),point[0],point[1])
		for point in self.eng_tach_rose_2:
			self.txt_out(self.ui_font_2.render(point[2], True, self.ui_colour_2),point[0],point[1])
		for point in self.gps_compass_rose_3:
			pygame.draw.lines(self.ui_screen, self.ui_colour_2, False, point, 3)
		#Determines tach circle position based on rpm
		tach_rpm = (rpm*360)/4000
		tach_rpm = (tach_rpm + 180) % 360
		tach_main = self.calc_line(tach_rpm,100,400,162)
		ext = self.calc_size(rpm)
		pygame.draw.lines(self.ui_screen, self.ui_colour_2, False, [(400,162),(tach_main[0],tach_main[1])], 5)
		#Draws the compass interface
		pygame.draw.circle(self.ui_screen, self.ui_colour_2, (400,162), 5)
		pygame.draw.circle(self.ui_screen, self.ui_colour_2, (400,162), 100,1)
		self.txt_out((self.ui_font_4.render(str(round(rpm)).replace('.0',''), True, self.ui_colour_2)),348 + ext,290)

	##############################################################
	##### AIS RELATED ############################################
	##############################################################

	def aismap(self,compass_out):
		self.ui_screen.fill(self.ui_colour_1)
		self.aismap_data = [[121334543,44.54204,-80.03334, 175.0],[12123232,44.50679,-79.84108, 228.0],[12123232,44.42924,-79.97292, 115.0],[12123232,44.50471,-80.19505, 10.0]]
		for vessel in self.aismap_data:
			vessel_data = self.haversine(self.nmea_connection.lat,self.nmea_connection.lon,vessel[1],vessel[2])
			if vessel_data[0] < 20:
				vessel_distance = round(vessel_data[0]*10,1)
				vessel_position = self.calc_line(vessel_data[1],vessel_distance,400,225)
				vessel_cog = self.calc_line(vessel[3],12,vessel_position[0],vessel_position[1])
				pygame.draw.circle(self.ui_screen, self.ui_colour_2, (vessel_position[0],vessel_position[1]), 2)
				pygame.draw.circle(self.ui_screen, self.ui_colour_2, (vessel_position[0],vessel_position[1]), 12, 1)
				pygame.draw.lines(self.ui_screen, self.ui_colour_2, False, [(vessel_position[0],vessel_position[1]),(vessel_cog[0],vessel_cog[1])], 1)
		compass_main = self.calc_line(compass_out,200,400,225)
		pygame.draw.circle(self.ui_screen, self.ui_colour_2, (400,225), 200,1)
		pygame.draw.lines(self.ui_screen, self.ui_colour_2, False, [(400,225),(compass_main[0],compass_main[1])], 3)
	
	def ais_start(self):
		while self.ais == True:
			return

	def auto_start(self):
		while self.auto == True:
			return

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
		self.ui_screen.blit(text, [x,y])

	def error_out(self,error_text, x, y):
		'''Creates an error splash screen to output error detail.
		
		Keyword arguments:
		error_text -- the error number and text details
		x -- the x position of the text
		y -- the y position of the text
		
		'''
		while True:
			self.ui_screen.fill(self.ui_colour_1)
			self.txt_out((self.ui_font_2.render('Error', True, self.ui_colour_2)),375,230)
			self.txt_out((self.ui_font_3.render(error_text, True, self.ui_colour_2)),x,y)
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
		self.ui_screen.fill(self.ui_colour_1)
		self.txt_out((self.ui_font_3.render('Exiting cleanly...', True, self.ui_colour_2)),355,128)
		pygame.display.flip()
		try:
			#Closes GPS serial connection
			self.nmea_connection.quit()
		except:
			pass
		#Closes any open track files
		self.track.off()
		time.sleep(2)
		pygame.quit()
		sys.exit()



#import cProfile

gps = NAVSTAT()
gps.start()
#cProfile.run('gps.start()')


