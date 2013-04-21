#!/usr/bin/env python
#-*- coding: utf-8 -*-

import pygame
import thread
import sys
import time
import datetime
import lib.nmea
import lib.gpx
import lib.geomath
import lib.route
import lib.track


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
		#Interface lines x,y points
		self.interface_points    = [[0,22,800,22],[0,150,250,150],[0,300,250,300],[250,150,250,500],[250,0,250,150],[250,0,250,150],[250,370,550,370],[550,0,550,500],[0,465,800,465],[550,311,800,311],[550,399,800,399],[550,110,800,110]] 
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
		self.cache         		 = CACHE()
		self.route               = lib.route.ROUTE(self.cache)
		self.track               = lib.track.TRACK(self.cache)
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
		self.track.switch(self.gpx_location[0])
		self.route.switch(self.gpx_location[1])
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
				self.cache.cache([self.nmea_connection.lat, self.nmea_connection.lon], self.nmea_connection.speed, self.nmea_connection.track, self.nmea_connection.utc, self.nmea_connection.status)
				self.gps_interface()
				self.gps_latlong()
				self.gps_speedometer()
				self.gps_compass()
				self.gps_destination()
			#AIS mode enabled
			elif self.navstat_mode == 1:
				self.aismap(self.nmea_connection.track)
			self.menu()
			self.clock.tick(self.frame_rate)
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
							self.track.mode = True
						else:
							self.track.mode = False
					elif settings_item[0] == 'mini_mode':
						if str(settings_item[1]) == 'OFF':
							self.mini = True
						else:
							self.mini = False
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

	def gpscheck(self):
		'''Determines whether a GPS connection is available - shuts down if not.'''
		x = 0
		connection = False
		while connection == False:
			try:
				#Opens a serial connection for NMEA GPS data
				self.nmea_connection = lib.nmea.NMEA0183(self.gps_info[0], self.gps_info[1], 5)
				self.nmea_connection.read()
				connection = True
			except:
				#Wait 5 secs - no serial connection - shut down
				if x == 5:
					self.error_out('Err1: There is currently no GPS connected to NAVSTAT.',175,260)
				x = x + 1

	def menu(self):
		'''Draws the menu interface common between all functions.'''
		#Display current time
		self.txt_out((self.font_2.render(datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), True, self.colour_2)),323,472)
		pygame.draw.rect(self.screen, self.colour_2, (0,500,800,30))
		#Draw the various screen display options
		self.txt_out(self.font_3.render('GPS', True, self.colour_1),100,510)
		self.txt_out(self.font_3.render('AIS', True, self.colour_1),200,510)
		self.txt_out(self.font_3.render('ENG', True, self.colour_1),300,510)
		pygame.draw.rect(self.screen, self.colour_1, (68,500,100,10))
		#Monitors GPS status and displays problems
		if self.cache.status == 'A':
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
		if self.track.mode == True:
			self.txt_out(self.font_1.render('Tracking - ' + self.track.gpx_track.gpx_file, True, self.colour_2),10,477)
		if self.route.mode == True:
			self.txt_out(self.font_1.render('Route - ' + self.route.gpx_route.gpx_file, True, self.colour_2),560,477)
			self.gps_destination()

	def gps_latlong(self):
		'''Positions and draws the lat/long interface.
		
		Keyword arguments:
		lat -- the current latitude position
		lon -- the current longitude position
		
		'''
		#Cuts the decimal count down to 5
		lat = self.cache.lat_lon[0]
		lon = self.cache.lat_lon[1]
		lat_out = ("%.5f" % self.cache.lat_lon[0])
		lon_out = ("%.5f" % self.cache.lat_lon[1])
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
		#Positions and draws the route interface
		self.txt_out((self.font_3.render('WPT', True, self.colour_2)),385,347)
		self.txt_out((self.font_3.render('WTA', True, self.colour_2)),655,376)
		self.txt_out((self.font_3.render('XTE', True, self.colour_2)),655,0)
		self.txt_out((self.font_3.render('RTA', True, self.colour_2)),655,288)
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
			self.txt_out((self.font_4.render(str(wpt_distance) + ' ' + self.unit_text[0], True, self.colour_2)),300 + ext1,418)
			self.txt_out((self.font_4.render(str(wpt_bearing).replace('.0','') + self.degree, True, self.colour_2)),343 + ext2,378)
			#Positions and draws crosstrack error interface
			#Positions xte text based on length
			self.txt_out((self.font_4.render(wpt_xte[1] + str(wpt_xte[0]) + ' ' + self.unit_text[0], True, self.colour_2)),555 + ext3,30)
			if self.route.xte_status == True:
				print 'hello'
			#Positions and draws the RTA info.
			self.txt_out((self.font_2.render(self.route.total_eta, True, self.colour_2)),600,325)
			#WTA hours too large to display
			if self.route.waypoint_eta['hour'] == '1000':
				self.txt_out((self.font_4.render('1000h +', True, self.colour_2)),615,406)
			else:
				#Positions and draws the WTA info
				ext = self.calc_size(self.route.waypoint_eta['hour'])
				self.txt_out((self.font_4.render(str(self.route.waypoint_eta['hour']) + 'h' + ' : ' + self.route.waypoint_eta['min'] + 'm', True, self.colour_2)),565 + ext,406)
			#Draw crosstrack angle if available
			if self.route.waypoint_xte[1] != '':
				self.txt_out((self.font_4.render(str(self.route.xte_angle[2]).replace('.0','') + self.degree, True, self.colour_2)),580,220)
				pygame.draw.polygon(self.screen, self.colour_2, [(675,170),(669,190),(681,190)],1)
				pygame.draw.circle(self.screen, self.colour_2, (self.route.xte_angle[1][0],self.route.xte_angle[1][1]), 2)
				pygame.draw.lines(self.screen, self.colour_2, False, [(self.route.xte_angle[0],170),(self.route.xte_angle[1][0],self.route.xte_angle[1][1])], 1)
				pygame.draw.lines(self.screen, self.colour_2, False, [(self.route.xte_angle[0],170),(self.route.xte_angle[3][0],self.route.xte_angle[3][1])], 1)

	def gps_speedometer(self):
		'''Positions and draws the speedometer interface.
		
		Keyword arguments:
		speed_out -- the current vessel speed
		
		'''
		#Rounds and converts speed to unit setting
		speed_out = round(self.unit_convert(self.unit_measure,1,self.cache.speed),1)
		#Determines speedometer position based on top speed
		speed_meter = (speed_out*220)/self.speed_top
		if speed_meter > 220:
			speed_meter = 220
		ext = self.calc_size(speed_out)
		#Draws the speedometer interface
		pygame.draw.rect(self.screen, self.colour_2, (15,210,220,40), 1)
		pygame.draw.rect(self.screen, self.colour_2, (15,210,speed_meter,40))
		self.txt_out((self.font_3.render('SOG', True, self.colour_2)),107,128)
		self.txt_out((self.font_4.render(str(speed_out) + ' ' + self.unit_text[1], True, self.colour_2)),30 + ext,158)
		self.txt_out((self.font_1.render(str(self.speed_top), True, self.colour_2)),220,253)
		self.txt_out((self.font_1.render(str(self.speed_top/2), True, self.colour_2)),116,253)
		self.txt_out((self.font_1.render('0', True, self.colour_2)),15,253)

	def gps_compass(self):
		'''Positions and draws the compass interface.
		
		Keyword arguments:
		compass_out -- the current vessel heading
		
		'''
		#Determines the x,y position on compass circumference in relation to degrees
		compass_out = self.cache.track 
		compass_main = self.calc_line(compass_out,100,400,162)
		#Draws the compass rose
		for point in self.compass_rose_1:
			self.txt_out(self.font_2.render(point[2], True, self.colour_2),point[0],point[1])
		for point in self.compass_rose_2:
			self.txt_out(self.font_3.render(point[2], True, self.colour_2),point[0],point[1])
		for point in self.compass_rose_3:
			pygame.draw.lines(self.screen, self.colour_2, False, point, 3)
		#Repositions degree text based on size
		ext = self.calc_size(compass_out)
		#If routing is enabled, draws the current destination line 
		if self.route.mode == True:
			compass_destination = self.calc_line(self.route.waypoint_calc['bearing'],100,400,162)
			pygame.draw.lines(self.screen, self.colour_2, False, [(400,162),(compass_destination[0],compass_destination[1])], 1)
		#Draws the compass interface
		self.txt_out((self.font_3.render('COG', True, self.colour_2)),380,0)
		pygame.draw.circle(self.screen, self.colour_2, (400,162), 5)
		pygame.draw.circle(self.screen, self.colour_2, (400,162), 100,1)
		pygame.draw.lines(self.screen, self.colour_2, False, [(400,162),(compass_main[0],compass_main[1])], 5)
		self.txt_out((self.font_4.render(str(round(compass_out)).replace('.0','') + self.degree, True, self.colour_2)),342 + ext,290)

	def gps_xteline(self):
		return

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
	
	def ais_start(self):
		while self.ais == True:
			return

	def auto_start(self):
		while self.auto == True:
			return

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
		self.track.off()
		time.sleep(2)
		pygame.quit()
		sys.exit()

class CACHE():

	def __init__(self):
		self.speed        = 0
		self.lat_lon      = [0,0]
		self.track        = 0
		self.utc          = 0
		self.status       = ''

	def cache(self,lat_lon,speed,track,utc,status):
		self.speed = speed
		self.lat_lon = lat_lon
		self.track = track
		self.utc = utc
		self.status = status

#import cProfile

gps = NAVSTAT()
gps.start()
#cProfile.run('gps.start()')


