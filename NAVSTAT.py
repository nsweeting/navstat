import pygame
import math
import thread
import sys
import time
import datetime
import NMEA
import GPX


class NAVSTAT():

	def __init__(self):
		pygame.init()
		#Colours that are required 
		self.black               = (   0,   0,   0)
		self.white               = ( 255, 255, 255)
		self.red                 = ( 255,   0,   0)
		self.colour_1            = self.white
		self.colour_2            = self.black
		self.colour_1_2          = self.colour_1
		self.colour_2_2          = self.colour_2
		#4 font sizes that are available
		self.font_1              = pygame.font.Font(None, 18)
		self.font_2              = pygame.font.Font(None, 30)
		self.font_3              = pygame.font.Font(None, 25)
		self.font_4              = pygame.font.Font(None, 50)
		#Switches for night, tracking, and fullscreen
		self.night               = False
		self.track               = False
		self.done                = False
		self.mini                = False
		#Degree character required for lat/long
		self.degree              = chr(176)
		#Top speed on the speedometer
		self.speed_top           = 2
		#Pixel size of the screen
		self.size                = [500,350]
		self.frame_rate          = 29
		self.screen              = None
		self.clock               = pygame.time.Clock()
		#Compass rose x,y points
		self.compass_rose_1      = [[643,40,'N'],[528,152,'W'],[643,263,'S'],[752,152,'E']]
		self.compass_rose_2      = [[548,75,'NW'],[548,232,'SW'],[725,232,'SE'],[725,75,'NE']]
		self.compass_rose_3      = [[(650,62),(650,82)],[(721,91),(711,101)],[(750,162),(730,162)],[(721,233),(711,223)],[(650,262),(650,242)],[(579,233),(589,223)],[(550,162),(570,162)],[(579,91),(589,101)]]
		self.destination_bear    = 0.1
		#Interface lines x,y points
		self.interface_points    = [[0,22,800,22],[0,150,500,150],[0,300,800,300],[250,150,250,300],[250,0,250,150],[500,0,500,300]] 
		#Holds track point info for future file output
		self.track_route         = []
		#Number of seconds between each track point. Number of points between each track file output.
		self.track_info          = [10,6]
		#The max size of a track file.
		self.track_maxsize       = None
		#File location of track files. File location of route files.
		self.gpx_location        = ['','']
		#Tracking object.
		self.gpx_track           = None
		#Location of GPS serial device
		self.gps_location        = None
		#Baudrate of GPS serial device
		self.gps_baudrate        = None
		#Current lat/lon position
		self.lat_lon             = ['','']
		#Unit measurement selected. Distance, speed.
		self.unit_measure        = [0,0]
		#Get settings
		self.settings()

	def start(self):
		'''Starts the NAVSTAT program and contains main loop.'''
		pygame.display.set_caption("NAVSTAT")
		self.gpscheck()
		#If a mode setting is on, switch it on
		self.mini_mode()
		self.night_mode()
		self.track_mode()
		#Main program loop - continue until quit
		while self.done == False:
			self.keyevents()
			self.interface()
			self.latlong(self.gps.lat, self.gps.lon)
			self.speedometer(self.gps.speed)
			self.compass(self.gps.track)
			self.destination()
			self.local_time()
			self.clock.tick(self.frame_rate)
			pygame.display.flip()
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
					elif settings_item[0] == 'unit_speed':
						if str(settings_item[1]) == 'KPH':
							self.unit_measure[1] = 0
						elif str(settings_item[1]) == 'MPH':
							self.unit_measure[1] = 1
						elif str(settings_item[1]) == 'NMPH':
							self.unit_measure[1] = 2
					elif settings_item[0] == 'gps_location':
						self.gps_location = str(settings_item[1])
					elif settings_item[0] == 'gps_baudrate':
						self.gps_baudrate = int(settings_item[1])
		settings.close()

	def gpscheck(self):
		'''Determines whether a GPS connection is available - shuts down if not.'''
		x = 0
		connection = False
		print 'Attempting to connect to GPS...'
		while connection == False:
			try:
				#Opens a serial connection for NMEA GPS data
				self.gps = NMEA.NMEA0183(self.gps_location, self.gps_baudrate, 5,'GPS')
				self.gps.read()
				connection = True
			except:
				#Wait 5 secs - no serial connection - shut down
				if x == 5:
					print 'No GPS connected. Cannot launch NAVSTAT.'
					sys.exit()
				time.sleep(1)
				x = x + 1

	def interface(self):
		'''Draws all the basic interface graphics.'''
		#Fills the background color
		self.screen.fill(self.colour_1)
		#Runs through each interface line and draws it
		for point in self.interface_points:
			pygame.draw.lines(self.screen, self.colour_2, False, [(point[0],point[1]),(point[2],point[3])], 2)
		#If tracking is on, draw it
		if self.track == True:
			self.txt_out(self.font_1.render('Tracking', True, self.colour_2),445,312)


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

	def latlong(self,lat,lon):
		'''Positions and draws the lat/long interface.
		
		Keyword arguments:
		lat -- the current latitude position
		lon -- the current longitude position
		
		'''
		#Determines how long the lat string is, and provides correct decimal count
		if lat < 0:
			dec = 1
		else:
			dec = 0
		if lat < 10 and lat > -10:
			lat_out = str(lat)[0:7 + dec]
		else:
			lat_out = str(lat)[0:8 + dec]
		#Determines how long the lat string is, and provides correct decimal count
		if lon < 0:
			dec = 1
		else:
			dec = 0
		if lon < 10 and lon > -10:
			lon_out = str(lon)[0:7 + dec]
		elif lon >= 100 or lon <= -100:
			lon_out = str(lon)[0:9 + dec]
		else:
			lon_out = str(lon)[0:8 + dec]
		#Applies North/South based on - value
		if lat_out[0:1] == '-':
			lat_out = lat_out[1:] + ' S'
		else:
			lat_out = lat_out + ' N'
		#Applies West/East based on - value
		if lon_out[0:1] == '-':
			lon_out = lon_out[1:] + ' W'
		else:
			lon_out = lon_out + ' E'
		#Makes the current lat/lon available to the class
		self.lat_lon = [lat, lon]
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

	def destination(self):
		'''Positions and draws destination interface. Does math to determine distance.'''
		#Earth radius
		radius = 6378.137
		lat_1 = self.lat_lon[0]
		lon_1 = self.lat_lon[1]
		lat_2 = 55.263521
		lon_2 = 128.212321
		#Haversine formula determines distance between two points
		lon_1, lat_1, lon_2, lat_2 = map(math.radians, [lon_1, lat_1, lon_2, lat_2])
		dst_lon = lon_2 - lon_1
		dst_lat = lat_2 - lat_1
		a = math.sin(dst_lat/2)**2 + math.cos(lat_1) * math.cos(lat_2) * math.sin(dst_lon/2)**2
		c = 2 * math.asin(math.sqrt(a))
		dis_out = radius * c
		dis_out = self.unit_convert(0,dis_out)
		y = math.sin(dst_lon) * math.cos(lat_2)
		x = math.cos(lat_1) * math.sin(lat_2) - math.sin(lat_1) * math.cos(lat_2) * math.cos(dst_lon)
		brg_out = math.degrees(math.atan2(y, x))
		brg_out = (brg_out + 360) % 360
		self.destination_bear = round(brg_out)
		#Positions destination distance text based on length
		if dis_out >= 0 and dis_out < 10:
			ext1 = 40
		elif dis_out >= 10 and dis_out < 100:
			ext1 = 34
		elif dis_out >= 100 and dis_out < 1000:
			ext1 = 24
		elif dis_out >= 1000 and dis_out < 10000:
			ext1 = 14
		elif dis_out >= 10000 and dis_out < 100000:
			ext1 = 0
		#Positions destination bearing text based on length
		if brg_out < 10:
			ext2 = 14
		elif brg_out >= 10 and brg_out < 100:
			ext2 = 7
		elif brg_out > 100:
			ext2 = 0
		#Draws the destination interface text
		self.txt_out((self.font_3.render('DST', True, self.colour_2)),355,0)
		self.txt_out((self.font_4.render(str(round(dis_out,2)), True, self.colour_2)),298 + ext1,30)
		self.txt_out((self.font_4.render(str(round(brg_out)).replace('.0','') + self.degree, True, self.colour_2)),344 + ext2,75)

	def speedometer(self, speed_out):
		'''Positions and draws the speedometer interface.
		
		Keyword arguments:
		speed_out -- The current vessel speed
		
		'''
		#Rounds and converts speed to unit setting
		speed_out = round(self.unit_convert(1,speed_out),1)
		#Determines speedometer position based on top speed
		speed_meter = (speed_out*220)/self.speed_top
		if speed_meter > 220:
			speed_meter = 220
		#Draws the speedometer interface
		pygame.draw.rect(self.screen, self.colour_2, (15,210,220,60), 1)
		pygame.draw.rect(self.screen, self.colour_2, (15,210,speed_meter,60))
		self.txt_out((self.font_3.render('SOG', True, self.colour_2)),107,128)
		self.txt_out((self.font_4.render(str(speed_out), True, self.colour_2)),100,158)
		self.txt_out((self.font_1.render(str(self.speed_top), True, self.colour_2)),220,273)
		self.txt_out((self.font_1.render(str(self.speed_top/2), True, self.colour_2)),116,273)
		self.txt_out((self.font_1.render('0', True, self.colour_2)),15,273)

	def compass(self, compass_out):
		'''Positions and draws the compass interface.
		
		Keyword arguments:
		compass_out -- The current vessel heading
		
		'''
		#Determines the x,y position in compass in relation to degrees
		rad = math.radians(compass_out)
		x = round(650 + 100 * math.sin(rad))
		y = round(162 - 100 * math.cos(rad))
		#Draws the compass rose
		for point in self.compass_rose_1:
			self.txt_out(self.font_2.render(point[2], True, self.colour_2),point[0],point[1])
		for point in self.compass_rose_2:
			self.txt_out(self.font_3.render(point[2], True, self.colour_2),point[0],point[1])
		for point in self.compass_rose_3:
			pygame.draw.lines(self.screen, self.colour_2, False, point, 3)
		pygame.draw.circle(self.screen, self.colour_2, (650,162), 5)
		pygame.draw.circle(self.screen, self.colour_2, (650,162), 100,3)
		pygame.draw.lines(self.screen, self.colour_2, False, [(650,162),(x,y)], 4)

	def local_time(self):
		'''Draws the current time/date interface.'''
		self.txt_out((self.font_2.render(datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), True, self.colour_2)),173,308)

	def tracking(self):
		'''Used as a thread to save tracking info for future file output.'''
		x = 0
		#Loop that keeps track of time, and saves track info based on this time
		while self.track == True:
			time.sleep(self.track_info[0])
			self.track_route.append([self.lat_lon,self.gps.utc])
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
		#Checks whether there is leftover track info, and outputs if so
		if self.track_route:
			self.track_make()
		#Cleans and closes track variables and files
		self.gpx_track.track_close()
		self.gpx_track = None
		self.track_route = []

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

	def track_mode(self):
		'''Checks whether Track Mode is enabled, and starts a tracking thread if so.'''
		if self.track == False:
			self.track = True
			self.gpx_track = GPX.GPX(self.gpx_location[0])
			self.gpx_track.track_start()
			thread.start_new_thread(self.tracking, ())
		else:
			self.track = False

	def mini_mode(self):
		'''Checks whether Mini Mode is enabled, and alters screen size if so.'''
		if self.mini == False: 
			self.screen = pygame.display.set_mode(self.size,pygame.RESIZABLE)
			self.mini = True
		else: 
			self.screen = pygame.display.set_mode(self.size,pygame.FULLSCREEN)
			self.mini = False

	def txt_out(self,text, h, v):
		self.screen.blit(text, [h,v])

	def unit_convert(self,type,num):
		'''Converts GPS output units to the units of choice.'''
		#This converts distance to choice of unit. Starts in km.
		if type == 0:
			#Kilometers
			if self.unit_measure[0] == 0:
				return num
			#Miles
			elif self.unit_measure[0] == 1:
				return num*0.621371
			#Nautical Miles
			elif self.unit_measure[0] == 2:
				return num*0.539957
		#This converts speed to choice of unit. Starts in knots.
		elif type == 1:
			#Kilometers / Hour
			if self.unit_measure[1] == 0:
				return num*1.852
			#Miles / Hour
			elif self.unit_measure[1] == 1:
				return num*1.15078
			#Nautical Miles / Hour
			elif self.unit_measure[1] == 2:
				return num

	def quit(self):
		'''Gets NAVSTAT ready to quit.'''
		self.screen.fill(self.colour_1)
		self.txt_out((self.font_3.render('Exiting cleanly...', True, self.colour_2)),355,128)
		pygame.display.flip()
		#Closes GPS serial connection
		self.gps.quit()
		#Closes any open track files
		if self.gpx_track != None: 
			if self.track_route:
				self.track_make()
			self.gpx_track.track_close()
		time.sleep(2)
		pygame.quit()
		sys.exit()


gps = NAVSTAT()
gps.start()


