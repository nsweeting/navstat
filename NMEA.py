import re
import serial
from threading import Thread


class NMEA0183():


	def __init__(self, location, baud_rate, timeout,type):
		'''Initiates variables and opens serial connection.
		
		Keyword arguments:
		location -- the location of the serial connection
		baud_rate -- the baud rate of the connection
		timeout -- the timeout of the connection
		type -- the type of connection.'GPS'
		
		'''
		self.exit = False
		self.ser_dev = serial.Serial(location, baud_rate, timeout)
		self.ser_dat = None
		#If the serial connection is for a GPS - ready the variables
		if type == 'GPS':
			self.lat = float(0.0)
			self.lon = float(0.0)
			self.speed = float(0.0)
			self.track = float(0.0)
			self.utc = '0.0'


	def read(self):
		'''Creates a thread to read serial connection data.'''
		trd_itm = Thread(None,self.read_thread,None,())
		trd_itm.start()


	def read_thread(self):
		'''The thread used to read incoming serial data.'''
		dat_new = ''
		dat_old = ''
		try:
			#Loops until the connection is broken, or is instructed to quit
			while self.is_open():
				#Instructed to quit
				if self.exit: break
				if dat_new: 
					dat_old = dat_new
					dat_new = ''
				dat_old = dat_old + self.buffer()
				if re.search("\r\n", dat_old):
					self.ser_dat, dat_new = dat_old.split("\r\n")
					if self.ser_dat[0:3] == '$GP':
						self.gps()
					dat_old = ''
		except:
			return


	def is_open(self):
		return self.ser_dev.isOpen()


	def buffer(self):
		dat_cur = self.ser_dev.read(1)
		x = self.ser_dev.inWaiting()
		if x: dat_cur = dat_cur + self.ser_dev.read(x)
		return dat_cur


	def gps(self):
		if self.ser_dat[3:6] == 'RMC':
			self.ser_dat = self.ser_dat.split(',')
			self.utc = self.gps_nmea2utc()
			self.lat = self.gps_nmea2dec(0)
			self.lon = self.gps_nmea2dec(1)
			self.speed = float(self.ser_dat[7])
			self.track = float(self.ser_dat[8])


	def gps_nmea2dec(self,type):
		mul = type*2
		data = float(self.ser_dat[3+mul][0:2+type]) + float(self.ser_dat[3+mul][2+type:9+type])/60
		if self.ser_dat[4+mul] == 'S': data = data*(-1)
		elif self.ser_dat[4+mul] == 'W': data = data*(-1)
		return data


	def gps_nmea2utc(self):
		time = self.ser_dat[1][0:2] + ':' + self.ser_dat[1][2:4] + ':' + self.ser_dat[1][4:6]
		date = '20' + self.ser_dat[9][4:6] + '-' + self.ser_dat[9][2:4] + '-' + self.ser_dat[9][0:2]
		return date + 'T' + time + 'Z'


	def quit(self):
		self.exit = True
