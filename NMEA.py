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
		self.serial_dev = serial.Serial(location, baud_rate, timeout)
		self.serial_data = None

		#If the serial connection is for a GPS - ready the variables
		if type == 'GPS':
			self.lat = float(0.0)
			self.lon = float(0.0)
			self.speed = float(0.0)
			self.track = float(0.0)
			self.utc = '0.0'

	def read(self):
		'''Creates a thread to read serial connection data.'''
		serial_thread = Thread(None,self.read_thread,None,())
		serial_thread.start()

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
					self.serial_data, dat_new = dat_old.split("\r\n")
					if self.serial_data[0:3] == '$GP':
						self.gps()
					dat_old = ''
		except:
			print 'error'


	def is_open(self):
		return self.serial_dev.isOpen()


	def buffer(self):
		dat_cur = self.serial_dev.read(1)
		x = self.serial_dev.inWaiting()
		if x: dat_cur = dat_cur + self.serial_dev.read(x)
		return dat_cur


	def gps(self):
		if self.serial_data[3:6] == 'RMC':
			self.serial_data = self.serial_data.split(',')
			self.utc = self.gps_nmea2utc()
			self.lat = self.gps_nmea2dec(0)
			self.lon = self.gps_nmea2dec(1)
			self.speed = float(self.serial_data[7])
			self.track = float(self.serial_data[8])


	def gps_nmea2dec(self,type):
		mul = type*2
		data = float(self.serial_data[3+mul][0:2+type]) + float(self.serial_data[3+mul][2+type:9+type])/60
		if self.serial_data[4+mul] == 'S': data = data*(-1)
		elif self.serial_data[4+mul] == 'W': data = data*(-1)
		return data


	def gps_nmea2utc(self):
		time = self.serial_data[1][0:2] + ':' + self.serial_data[1][2:4] + ':' + self.serial_data[1][4:6]
		date = '20' + self.serial_data[9][4:6] + '-' + self.serial_data[9][2:4] + '-' + self.serial_data[9][0:2]
		return date + 'T' + time + 'Z'


	def quit(self):
		self.exit = True
