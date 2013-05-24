#!/usr/bin/env python
#-*- coding: utf-8 -*-

import pygame
import thread
import sys
import time
import datetime
import lib.nmea
import lib.gps
import lib.geomath
import lib.alarm
import lib.gui


class NAVSTAT():

	def __init__(self):

		self.exit                = False
		self.navstat_mode        = 0           
		#Switches for autopilot, routing, and AIS
		self.auto                = False
		self.ais                 = False
		self.aismap_data         = None
		#Location and baudrate of serial device
		self.serial_info         = [None,None]

		self.eng_tach_rose_1     = [[395,263,'0'],[273,152,'10'],[389,38,'20'],[506,152,'30']]
		self.eng_tach_rose_2     = [[312,232,'5'],[298,75,'15'],[476,71,'25'],[475,232,'35']]
		self.unit                = lib.geomath.UNIT()
		self.alarm               = lib.alarm.ALARM()
		self.gui                 = lib.gui.GUI()
		self.cache               = lib.nmea.CACHE()

		self.gps                 = lib.gps.GPS(self.gui, self.cache, self.unit)
		#Get settings
		self.settings()

	def start(self):
		'''Starts the NAVSTAT program and contains main loop.'''
		#Checks to enable fullscreen and colours
		self.gui.night_mode()
		self.gui.mini_mode()
		#Attempts to create a serial NMEA connection
		self.connect()
		#Throws splash on screen
		self.gui.splash()
		self.gps.track.distance_start()
		#Main program loop - continue until quit
		while self.exit == False:
			#Checks if buttons have been pressed
			self.keyevents()
			#Checks if any alarms have been activated
			self.alarm.check()
			#Displays the common menu
			self.gui.menu()
			#GPS mode enabled
			if self.navstat_mode == 0:
				if self.nmea.exit == False:
					self.cache.cache_gps(self.nmea.data_gps['lat'], self.nmea.data_gps['lon'], self.nmea.data_gps['speed'], self.nmea.data_gps['track'], self.nmea.data_gps['utc'], self.nmea.data_gps['status'])
					self.gps.interface()
					self.gps.latlong()
					self.gps.speedometer()
					self.gps.compass()
					self.gps.destination()
				else:
					self.error()
			#AIS mode enabled
			elif self.navstat_mode == 1:
				self.cache.cache_gps(self.nmea_connection.data_gps['lat'], self.nmea_connection.data_gps['lon'], self.nmea_connection.data_gps['speed'], self.nmea_connection.data_gps['track'], self.nmea_connection.data_gps['utc'], self.nmea_connection.data_gps['status'])
				self.map_interface()
			elif self.navstat_mode == 2:
				self.cache.cache_gps(self.nmea.data_gps['lat'], self.nmea.data_gps['lon'], self.nmea.data_gps['speed'], self.nmea.data_gps['track'], self.nmea.data_gps['utc'], self.nmea.data_gps['status'])
			elif self.navstat_mode == 3:
				self.aismap(self.nmea_connection.track)
			elif self.navstat_mode == 4:
				self.eng_interface()
				self.eng_tachometer()
			self.gui.clock.tick(self.gui.frame_rate)
			#Updates the screen
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
						self.gui.size[1] = int(settings_item[1])
					elif settings_item[0] == 'frame_y':
						self.gui.size[0] = int(settings_item[1])
					elif settings_item[0] == 'top_speed':
						self.gps.speed_top = int(settings_item[1])
					elif settings_item[0] == 'night_mode':
						if str(settings_item[1]) == 'OFF':
							self.gui.night = True
						else:
							self.gui.night = False
					elif settings_item[0] == 'track_mode':
						if str(settings_item[1]) == 'OFF':
							self.gps.track.mode = True
						else:
							self.gps.track.mode = False
					elif settings_item[0] == 'mini_mode':
						if str(settings_item[1]) == 'OFF':
							self.gui.mini = True
						else:
							self.gui.mini = False
					elif settings_item[0] == 'track_secs':
						self.gps.track.save_info[0] = int(settings_item[1])
					elif settings_item[0] == 'track_save':
						self.gps.track.save_info[1] = int(settings_item[1])
					elif settings_item[0] == 'track_location':
						self.gps.track.location = str(settings_item[1])
					elif settings_item[0] == 'track_maxsize':
						self.gps.track.maxsize = int(settings_item[1])
					elif settings_item[0] == 'route_location':
						self.gps.route.location = str(settings_item[1])
					elif settings_item[0] == 'unit_distance':
						if str(settings_item[1]) == 'KM':
							self.unit.measure[0] = 0
						elif str(settings_item[1]) == 'MI':
							self.unit.measure[0] = 1
						elif str(settings_item[1]) == 'NM':
							self.unit.measure[0] = 2
						self.unit.text[0] = settings_item[1]
					elif settings_item[0] == 'unit_speed':
						if str(settings_item[1]) == 'KPH':
							self.unit.measure[1] = 0
						elif str(settings_item[1]) == 'MPH':
							self.unit.measure[1] = 1
						elif str(settings_item[1]) == 'NMPH':
							self.unit.measure[1] = 2
						self.unit.text[1] = settings_item[1].replace('PH','')
					elif settings_item[0] == 'gps_location':
						self.serial_info[0] = str(settings_item[1])
					elif settings_item[0] == 'gps_baudrate':
						self.serial_info[1] = int(settings_item[1])
					elif settings_item[0] == 'version':
						self.gui.version = settings_item[1]
					elif settings_item[0] == 'xte_alarm':
						self.xte_alarm = settings_item[1]
		settings.close()

	def connect(self):
		'''Determines whether a serial connection is available.'''
		x = 0
		connection = False
		#Readies a serial connection for NMEA GPS data
		self.nmea = lib.nmea.NMEA0183(self.serial_info[0], self.serial_info[1], 5)
		while connection == False:
			try:
				#Attempts to make a serial connection
				self.nmea.read()
				connection = True
				failed = False
				#Waits until a proper data stream is available
				while self.nmea.data_gps['lat'] == 0 and self.nmea.data_gps['lon'] == 0:
					pass
				#Turns on tracking and routing if activated
				self.gps.track.switch()
				self.gps.route.switch()
			except:
				#Try 5 times - no serial connection - shut down
				if x == 5:
					self.nmea.exit = True
					connection = True
					#Returns tracking and routing to OFF
					self.gps.track.mode = False
					self.gps.route.mode = False
				x = x + 1

	def keyevents(self):
		'''Checks whether a key has been pressed and activates event if so.'''
		for event in pygame.event.get():
			#Only KEYDOWN events
			if event.type == pygame.KEYDOWN:
				#Pressed 'Escape' to quit
				if event.key == pygame.K_ESCAPE:
					self.exit = True
				#Pressed 'Tab' to mini mode
				elif event.key == pygame.K_TAB:
					self.gui.mini_mode()
				#Pressed 'Space' to night mode
				elif event.key == pygame.K_SPACE:
					self.gui.night_mode()
				#Pressed 'T' to tracking mode
				elif event.key == pygame.K_t:
					self.gps.track.switch()
				#Pressed 'A' to autopilot kode
				elif event.key == pygame.K_a:
					self.auto_mode()
				#Pressed 'Right' to move forward on route
				elif event.key == pygame.K_RIGHT:
					self.gps.route.get(0)
				#Pressed 'Left' to move backward on route
				elif event.key == pygame.K_LEFT:
					self.gps.route.get(1)
				elif event.key == pygame.K_F1:
					self.navstat_mode = 0
				elif event.key == pygame.K_F2:
					self.navstat_mode = 1
				elif event.key == pygame.K_F4:
					self.navstat_mode = 3
			elif event.type == pygame.QUIT:
				self.quit()

	def error(self):
		if self.navstat_mode == 0:
			self.gui.txt_out((self.gui.font_2.render('There is currently no GPS connected.', True, self.gui.colour_2)),323,472)
			#Turns off track and route threads
			if self.gps.track.mode == True:
				self.gps.track.switch()
			if self.gps.route.mode == True:
				self.gps.route.switch()
			#Clears the current cache
			self.cache.gps = {'lat': 0, 'lon': 0, 'speed': 0, 'track': 0, 'utc': 0, 'status': ''}
			#Reload settings
			self.settings()
			#Attempt to reconect to serial data
			self.connect()
			time.sleep(1)


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
		self.gui.screen.fill(self.gui.colour_1)
		self.gui.txt_out((self.gui.font_3.render('Exiting cleanly...', True, self.gui.colour_2)),355,128)
		pygame.display.flip()
		try:
			#Closes GPS serial connection
			self.nmea.quit()
		except:
			pass
		#Closes any open track files
		self.gps.track.off()
		time.sleep(2)
		pygame.quit()
		sys.exit()



#import cProfile

gps = NAVSTAT()
gps.start()
#cProfile.run('gps.start()')


