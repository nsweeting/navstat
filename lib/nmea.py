#!/usr/bin/env python
#-*- coding: utf-8 -*-

import re
import serial
import binascii
import ais
from threading import Thread


class NMEA0183():


	def __init__(self, location, baud_rate, timeout):
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
		self.ais_data = None

		#Ready the GPS variables
		self.lat = float(0.0)
		self.lon = float(0.0)
		self.speed = float(0.0)
		self.track = float(0.0)
		self.utc = '0.0'

	def read(self):
		'''Creates a thread to read serial connection data.'''
		serial_thread = Thread(None,self.read_thread,None,())
		serial_thread.start()

	def send(self):
		return

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
					if self.checksum(self.serial_data):
						if self.serial_data[0:3] == '$GP':
							self.gps()
						elif self.serial_data[0:3] == '!AI':
							self.ais_data = telegramparser(self.serial_data)
					dat_old = ''
		except:
			self.quit()

	def is_open(self):
		'''Checks whether the serial connection is still open.'''
		return self.serial_dev.isOpen()

	def buffer(self):
		'''Creates a buffer for serial data reading. Avoids reading lines for better performance.'''
		dat_cur = self.serial_dev.read(1)
		x = self.serial_dev.inWaiting()
		if x: dat_cur = dat_cur + self.serial_dev.read(x)
		return dat_cur

	def makechecksum(self,data):
		'''Calculates a checksum from a NMEA sentence.
		
		Keyword arguments:
		data -- the NMEA sentence to create
		
		'''
		csum = 0
		i = 0
		# Remove ! or $ and *xx in the sentence
		data = data[1:data.rfind('*')]
		while (i < len(data)):
			input = binascii.b2a_hex(data[i])
			input = int(input,16)
			#xor
			csum = csum ^ input
			i += 1
		return csum

	def checksum(self,data):
		'''Initiates variables and opens serial connection.
		
		Keyword arguments:
		data -- the NMEA sentence to check
		
		'''
		try:
			# Create an integer of the two characters after the *, to the right
			supplied_csum = int(data[data.rfind('*')+1:data.rfind('*')+3], 16)
		except:
			return ''
		# Create the checksum
		csum = self.makechecksum(data)
		# Compare and return
		if csum == supplied_csum:
			return True
		else:
			return False

	def gps(self):
		'''Deconstructs NMEA gps readings.'''
		if self.serial_data[3:6] == 'RMC':
			self.serial_data = self.serial_data.split(',')
			self.utc = self.gps_nmea2utc()
			self.lat = self.gps_nmea2dec(0)
			self.lon = self.gps_nmea2dec(1)
			self.speed = float(self.serial_data[7])
			self.track = float(self.serial_data[8])

	def gps_nmea2dec(self,type):
		'''Converts NMEA lat/long format to decimal format.
		
		Keyword arguments:
		type -- tells whether it is a lat or long. 0=lat,1=long
		
		'''
		#Represents the difference in list position between lat/long
		x = type*2
		#Converts NMEA format to decimal format
		data = float(self.serial_data[3+x][0:2+type]) + float(self.serial_data[3+x][2+type:9+type])/60
		#Adds negative value based on N/S, W/E
		if self.serial_data[4+x] == 'S': data = data*(-1)
		elif self.serial_data[4+x] == 'W': data = data*(-1)
		return data

	def gps_nmea2utc(self):
		'''Converts NMEA utc format to more standardized format.'''
		time = self.serial_data[1][0:2] + ':' + self.serial_data[1][2:4] + ':' + self.serial_data[1][4:6]
		date = '20' + self.serial_data[9][4:6] + '-' + self.serial_data[9][2:4] + '-' + self.serial_data[9][0:2]
		return date + 'T' + time + 'Z'

	def quit(self):
		'''Enables quiting the serial connection.'''
		self.exit = True
