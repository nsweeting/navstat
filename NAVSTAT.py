import pygame
import math
import thread
import NMEA
import GPX
import sys
import time
from datetime import datetime


class navstat():


	def __init__(self):
		pygame.init()
		self.gpscheck()

		self.black          = (   0,   0,   0)
		self.white          = ( 255, 255, 255)
		self.red            = ( 255,   0,   0)
		self.clr_1          = self.white
		self.clr_2          = self.black
		self.clr_1_2        = self.clr_1
		self.clr_2_2        = self.clr_2
		self.font_1         = pygame.font.Font(None, 18)
		self.font_2         = pygame.font.Font(None, 30)
		self.font_3         = pygame.font.Font(None, 25)
		self.font_4         = pygame.font.Font(None, 50)
		self.night          = False
		self.track          = False
		self.done           = False
		self.mini           = False
		self.degree         = chr(176)
		self.spd_top        = 2
		self.size           = [500,350]
		self.frame_rate     = 29
		self.screen         = None
		self.clock          = pygame.time.Clock()
		self.cps_add        = 0
		self.cps_nfo        = [108,268,210] #length,height,vertical
		self.des_brg        = 0.1
		self.int_pnt        = [[0,22,500,22],[0,150,500,150],[0,300,500,300],[250,150,250,300],[250,0,250,150]] 
		self.trk_rte        = []
		self.trk_nfo        = [10,6]
		self.gpx_loc        = ['','']
		self.lat_lon        = ['','']
		self.gpx_trk        = None
		self.unt_msr        = [0,0]


	def start(self):
		pygame.display.set_caption("NAVSTAT")
		self.cps_nfo[0] = self.cps_nfo[0] + 1
		self.settings()
		self.mini_mode()
		self.night_mode()
		self.track_mode()
		while self.done == False:
			self.keyevents()
			self.interface()
			self.latlong(self.gps.lat, self.gps.lon)
			self.speedometer(self.gps.spd)
			self.compass(self.gps.trk)
			self.local_time()
			self.destination()
			self.clock.tick(self.frame_rate)
			pygame.display.flip()
		self.quit()



	def settings(self):
		settings = open('navstat.config', 'r')
		for line in settings:
			if line != '\n' or '' or None:
				if line[0:1] != '#':
					set_itm = line.split('=')
					set_itm[1] = set_itm[1].rstrip()
					if set_itm[0] == 'frame_x': self.size[1] = int(set_itm[1])
					elif set_itm[0] == 'frame_y': self.size[0] = int(set_itm[1])
					elif set_itm[0] == 'font_1': self.font_1 = pygame.font.Font(None, int(set_itm[1]))
					elif set_itm[0] == 'font_2': self.font_2 = pygame.font.Font(None, int(set_itm[1]))
					elif set_itm[0] == 'font_3': self.font_3 = pygame.font.Font(None, int(set_itm[1]))
					elif set_itm[0] == 'font_4': self.font_4 = pygame.font.Font(None, int(set_itm[1]))
					elif set_itm[0] == 'top_speed': self.spd_top = int(set_itm[1])
					elif set_itm[0] == 'night_mode': 
						if str(set_itm[1]) == 'OFF': self.night = True
						else: self.night = False
					elif set_itm[0] == 'track_mode':
						if str(set_itm[1]) == 'OFF': self.track = True
						else: self.track = False
					elif set_itm[0] == 'mini_mode':
						if str(set_itm[1]) == 'OFF': self.mini = True
						else: self.mini = False
					elif set_itm[0] == 'track_secs': self.trk_nfo[0] = int(set_itm[1])
					elif set_itm[0] == 'track_secs': self.trk_nfo[0] = int(set_itm[1])
					elif set_itm[0] == 'track_save': self.trk_nfo[1] = int(set_itm[1])
					elif set_itm[0] == 'track_location': self.gpx_loc[0] = str(set_itm[1])
					elif set_itm[0] == 'route_location': self.gpx_loc[1] = str(set_itm[1])
					elif set_itm[0] == 'unit_distance':
						if str(set_itm[1]) == 'KM': self.unt_msr[0] = 0
						elif str(set_itm[1]) == 'MI': self.unt_msr[0] = 1
						elif str(set_itm[1]) == 'NM': self.unt_msr[0] = 2
					elif set_itm[0] == 'unit_speed':
						if str(set_itm[1]) == 'KPH': self.unt_msr[1] = 0
						elif str(set_itm[1]) == 'MPH': self.unt_msr[1] = 1
						elif str(set_itm[1]) == 'NMPH': self.unt_msr[1] = 2
		settings.close()


	def gpscheck(self):
		x = 0
		conn = False
		print 'Attempting to connect to GPS...'
		while conn == False:
			try:
				self.gps = NMEA.NMEA0183('/dev/ttyUSB0', 4800, 5,'GPS')
				self.gps.read()
				conn = True
			except:
				if x == 5:
					print 'No GPS connected. Cannot launch NAVSTAT.'
					sys.exit()
				time.sleep(1)
				x = x + 1


	def interface(self):
		self.screen.fill(self.clr_1)
		for point in self.int_pnt: pygame.draw.lines(self.screen, self.clr_2, False, [(point[0],point[1]),(point[2],point[3])], 2)
		if self.track == True: self.txt_out(self.font_1.render('Tracking', True, self.clr_2),445,312)


	def keyevents(self):
		for event in pygame.event.get(): 
			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_ESCAPE: self.done = True
				elif event.key == pygame.K_TAB: self.mini_mode()
				elif event.key == pygame.K_SPACE: self.night_mode()
				elif event.key == pygame.K_t: self.track_mode()


	def latlong(self,lat,lon):
		if lat < 0: dec = 1
		else: dec = 0
		if lat < 10 and lat >= 0: lat_out = str(lat)[0:7 + dec]
		elif lat > -10 and lat < 0: lat_out = str(lat)[0:7 + dec]
		else: lat_out = str(lat)[0:8 + dec]
		if lat_out[0:1] == '-': lat_out = lat_out[1:] + ' S'
		else: lat_out = lat_out + ' N'

		if lon < 0: dec = 1
		else: dec = 0
		if lon < 10 and lon >= 0: lon_out = str(lon)[0:7 + dec]
		elif lon > -10 and lon < 0: lon_out = str(lon)[0:7 + dec]
		elif lon >= 100: lon_out = str(lon)[0:9 + dec]
		elif lon <= -100: lon_out = str(lon)[0:9 + dec]
		else: lon_out = str(lon)[0:8 + dec]
		if lon_out[0:1] == '-': lon_out = lon_out[1:] + ' W'
		else: lon_out = lon_out + ' E'

		self.lat_lon = [lat, lon]
		l_len = len(lat_out)
		if l_len == 10: ext_1 = 20
		elif l_len == 11: ext_1 = 1
		else: ext_1 = 40
		l_len = len(lon_out)
		if l_len == 10: ext_2 = 20
		elif l_len == 11: ext_2 = 1
		else: ext_2 = 40

		self.txt_out((self.font_3.render('POS', True, self.clr_2)),107,0)		#POS text
		self.txt_out((self.font_4.render(lat_out, True, self.clr_2)),20 + ext_1,30)	#Latitude
		self.txt_out((self.font_4.render(lon_out, True, self.clr_2)),20 + ext_2,75)	#Longitude


	def destination(self):
		radius = 6378.137
		lat_1 = self.lat_lon[0]
		lon_1 = self.lat_lon[1]
		lat_2 = 55.263521
		lon_2 = 128.212321

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
		self.des_brg = round(brg_out)

		if dis_out >= 0 and dis_out < 10: ext1 = 40
		elif dis_out >= 10 and dis_out < 100: ext1 = 34
		elif dis_out >= 100 and dis_out < 1000: ext1 = 24
		elif dis_out >= 1000 and dis_out < 10000: ext1 = 14
		elif dis_out >= 10000 and dis_out < 100000: ext1 = 0

		if brg_out < 10: ext2 = 14
		elif brg_out >= 10 and brg_out < 100: ext2 = 7
		elif brg_out > 100: ext2 = 0

		self.txt_out((self.font_3.render('DST', True, self.clr_2)),355,0)
		self.txt_out((self.font_4.render(str(round(dis_out,2)), True, self.clr_2)),298 + ext1,30)
		self.txt_out((self.font_4.render(str(round(brg_out)).replace('.0','') + self.degree, True, self.clr_2)),344 + ext2,75)		


	def speedometer(self, spd_out):
		spd_out = round(self.unit_convert(1,spd_out),1)
		spd_mtr = (spd_out*220)/self.spd_top
		if spd_mtr > 220: spd_mtr = 220

		pygame.draw.rect(self.screen, self.clr_2, (15,210,220,60), 1)
		pygame.draw.rect(self.screen, self.clr_2, (15,210,spd_mtr,60))
		self.txt_out((self.font_3.render('SOG', True, self.clr_2)),107,128) 			#SOG text
		self.txt_out((self.font_4.render(str(spd_out), True, self.clr_2)),100,158) 			#Speed
		self.txt_out((self.font_1.render(str(self.spd_top), True, self.clr_2)),220,273) 	#Top speed
		self.txt_out((self.font_1.render(str(self.spd_top/2), True, self.clr_2)),116,273) 	#Mid speed
		self.txt_out((self.font_1.render('0', True, self.clr_2)),15,273) 			#0 speed


	def compass(self, cps_out):
		cps_out = round(self.gps.trk)    
		self.cps_add = 0
		self.cps_nfo[1] = 268
		self.cps_nfo[2] = 210
		cps_port = round(self.gps.trk) - (self.cps_nfo[0]/2)
		if cps_port < 0: cps_port = 360 + cps_port
		x = 0

		while x < self.cps_nfo[0]:
			if cps_port > 359: cps_port = -1
			self.cps_nfo[1] = self.cps_nfo[1] + 2
			cps_port = cps_port + 1
			x = x + 1
			if cps_port == 0: self.cps_mark('N',3)
			elif cps_port == 45: self.cps_mark('NE',8) 
			elif cps_port == 90: self.cps_mark('E',3)
			elif cps_port == 135: self.cps_mark('SE',8)
			elif cps_port == 180: self.cps_mark('S',3)
			elif cps_port == 225: self.cps_mark('SW',8)
			elif cps_port == 270: self.cps_mark('W',3)
			elif cps_port == 315: self.cps_mark('NW',8)
			elif cps_port == self.des_brg: pygame.draw.polygon(self.screen, self.clr_2, [(self.cps_nfo[1] - 10,self.cps_nfo[2]), (self.cps_nfo[1] + 10,self.cps_nfo[2]), (self.cps_nfo[1],self.cps_nfo[2] + 20)])
			pygame.draw.lines(self.screen, self.clr_2, False, [(self.cps_nfo[1],self.cps_nfo[2]), (self.cps_nfo[1],self.cps_nfo[2] + 10  + self.cps_add)], 1)
			self.cps_add = 0

		if cps_out < 10: ext = 14
		elif cps_out >= 10 and cps_out < 100: ext = 7
		else: ext = 0 
		pygame.draw.polygon(self.screen, self.clr_2, [(362,269), (377,259), (393,269)])	
		self.txt_out((self.font_3.render('COG', True, self.clr_2)),355,128)							#COG
		self.txt_out((self.font_4.render(str(cps_out).replace('.0','') + self.degree, True, self.clr_2)),344 + ext,158)		


	def local_time(self):
		self.txt_out((self.font_2.render(datetime.now().strftime('%Y-%m-%d %H:%M'), True, self.clr_2)),173,308)


	def cps_mark(self,direction,sub):
		self.cps_add = 10
		self.txt_out((self.font_1.render(direction, True, self.clr_2)),self.cps_nfo[1] - sub,self.cps_nfo[2] + 30)


	def tracking(self):
		x = 0
		while self.track == True:
			time.sleep(self.trk_nfo[0])
			self.trk_rte.append([self.lat_lon,self.gps.utc])
			x = x + 1
			if x > self.trk_nfo[1]:
				self.trk_mke()
				self.trk_rte = []
				x = 0
		if self.trk_rte: self.trk_mke()
		self.gpx_trk.trk_close()
		self.gpx_trk = None
		self.trk_rte = []


	def trk_mke(self):
		for point in self.trk_rte: self.gpx_trk.trkpt(point[0][0], point[0][1], 0, point[1])


	def night_mode(self):
		if self.night == False:
			self.clr_1 = self.black
			self.clr_2 = self.red
			self.night = True
		elif self.night == True:
			self.clr_1 = self.clr_1_2
			self.clr_2 = self.clr_2_2
			self.night = False


	def track_mode(self):
		if self.track == False:
			self.track = True
			self.gpx_trk = GPX.GPX(self.gpx_loc[0])
			self.gpx_trk.trk_start()
			thread.start_new_thread(self.tracking, ())
		else: self.track = False


	def mini_mode(self):
		if self.mini == False: 
			self.screen = pygame.display.set_mode(self.size,pygame.RESIZABLE)
			self.mini = True
		else: 
			self.screen = pygame.display.set_mode(self.size,pygame.FULLSCREEN)
			self.mini = False


	def txt_out(self,text, h, v):
		self.screen.blit(text, [h,v])


	def unit_convert(self,type,num):
		if type == 0:
			if self.unt_msr[0] == 0: return num
			elif self.unt_msr[0] == 1: return num*0.621371
			elif self.unt_msr[0] == 2: return num*0.539957
		elif type == 1:
			if self.unt_msr[1] == 0: return num*1.852
			elif self.unt_msr[1] == 1: return num*1.15078
			elif self.unt_msr[1] == 2: return num


	def quit(self):
		self.screen.fill(self.clr_1)
		self.txt_out((self.font_3.render('Exiting cleanly...', True, self.clr_2)),355,128)
		pygame.display.flip()
		self.gps.quit()
		if self.gpx_trk != None: 
			if self.trk_rte: self.trk_mke()
			self.gpx_trk.trk_close()
		time.sleep(2)
		pygame.quit()
		sys.exit()


gps = navstat()
gps.start()
#test = NMEA.NMEA0183('/dev/ttyUSB0', 4800, 5,'gps')
#test.read_serial()

