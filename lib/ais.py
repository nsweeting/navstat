#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# decode.py (part of "AIS Logger")
# Simple AIS sentence parsing
#
# This parser has support for both standard !AIVDM type messages and for
# $PAIS type messages received from SAAB TransponderTech transponders
#
# Copyright (c) 2006-2008 Erik I.J. Olsson <olcai@users.sourceforge.net>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import binascii
import datetime
import math
import decimal

def jointelegrams(inputstring):
	# Creates an AIVDM-message combined of several sentences with a
	# row break between each sentence
	telegrams = inputstring.splitlines()
	joinedphrase = ''
	# Check the checksum of each sentence and join them
	for x in telegrams[:]:
		if not checksum(x):
			return
		phrase = x.split(',')
		joinedphrase = joinedphrase + phrase[5]
	# Create a full AIVDM-sentence
	fullphrase = '!AIVDM,1,1,,,' + joinedphrase + ',0*'
	# Create a checksum
	csum = hex(makechecksum(fullphrase))
	# Combine the sentence and the checksum and create a single
	# AIVDM-message
	fullphrase = fullphrase + csum[2:]
	return fullphrase

def telegramparser(inputstring):
	# This function decodes certain types of messages from the
	# receiver and returns the interesting data as a dictionary where
	# each key describes the information of each message part

	# Observe that the navigational status is set as an integer
	# according to ITU-R M.1371, and is thus converted for SAAB
	# PAIS messages to these values

	# For each value where we have a N/A-state None is returned

	# Convert the raw input string to a list of separated values
	telegram = inputstring.split(',')

	# Depending on what sentence the list contains, extract the
	# information and create a dictionary with the MMSI number as key
	# and a value which contain another dictionary with the actual
	# data

	# If the sentence follows the SAAB TransponderTech standard:
	if telegram[0] == '$PAIS':
		# Check the checksum
		if not checksum(inputstring):
			return

		# Get the source MMSI number
		mmsi = int(telegram[2],16)

		# Extract the message type number and prefix the number with
		# an 'S' to indicate SAAB messages
		message = 'S' + telegram[1]

		# Get current computer time to timestamp messages
		timestamp = datetime.datetime.now()

		# If the sentence contains 02 - AIS Standard Position:
		if message == 'S02':
			# Rate of turn in degrees/minute from -127 to +127 where 128=N/A
			rateofturn = int(telegram[3], 16)
			if rateofturn >=0 and rateofturn <128: # Turning right
				# Convert between ROTais and ROTind
				rateofturn = int(math.pow((rateofturn/4.733), 2))
				if rateofturn > 720:
					rateofturn = 720 # Full
			elif rateofturn >128 and rateofturn <=255: # Turning left
				rateofturn = 256 - rateofturn
				# Convert between ROTais and ROTind
				rateofturn = -int(math.pow((rateofturn/4.733), 2))
				if rateofturn < -720:
					rateofturn = -720 # Full
			else:
				rateofturn = None # N/A
			# Navigation status converted to ITU-R M.1371 standard
			navstatus = telegram[4]
			if navstatus == '1': navstatus = 0 # Under Way
			elif navstatus == '2': navstatus = 2 # Not Under Command
			elif navstatus == '3': navstatus = 3 # Restricted Manoeuvrability
			elif navstatus == '4': navstatus = 1 # At Anchor
			elif navstatus == '5': navstatus = None # (MAYDAY?) sets to N/A
			else: navstatus = None # N/A
			# Latitude in decimal degrees (DD)
			latitude = calclatitude(tobin(int(telegram[5],16),27))
			# Longitude in decimal degrees (DD)
			longitude = calclongitude(tobin(int(telegram[6],16),28))
			# Speed over ground in 1/10 knots
			sog = decimal.Decimal(int(telegram[7],16)) / 10
			if sog > decimal.Decimal("102.2"):
				sog = None # N/A
			# Course over ground in 1/10 degrees where 0=360
			cog = decimal.Decimal(int(telegram[8],16)) / 10
			if cog > 360: # 360 and above means 360=N/A
				cog = None
			# Heading in whole degrees between 0-359 and 511=N/A
			heading = int(telegram[9],16)
			if heading > 359:
				heading = None # N/A
			# Position accuracy where 0=bad and 1=good/DGPS
			posacc = int(telegram[11])
			# Return a dictionary with descriptive keys
			return {'mmsi': mmsi,
					'rot': rateofturn,
					'navstatus': navstatus,
					'latitude': latitude,
					'longitude': longitude,
					'sog': sog,
					'cog': cog,
					'heading': heading,
					'posacc': posacc,
					'time': timestamp,
					'message': message}

		# If the sentence contains message 04 - Addressed Text Telegram:
		elif message == 'S04':
			# Content of message in ASCII (replace any " with ')
			content = telegram[4].replace('''"''',"'")
			# Destination MMSI number
			to_mmsi = int(telegram[5],16)
			# Return a dictionary with descriptive keys
			return {'mmsi': mmsi,
					'content': content,
					'to_mmsi': to_mmsi,
					'time': timestamp,
					'message': message}

		# If the sentence contains message 06 - Broadcast Text Telegram:
		elif message == 'S06':
			# Content of message in ASCII (replace any " with ')
			content = str(telegram[4]).replace('''"''',"'")
			# Return a dictionary with descriptive keys
			return {'mmsi': mmsi,
					'content': content,
					'time': timestamp,
					'message': message}

		# If the sentence contains message 07 - Addressed Binary Telegram:
		elif message == 'S07':
			# Binary data payload
			payload = []
			for char in telegram[4]:
				payload.append(tobin(int(char,16),4))
			payload = ''.join(payload)
			# Destination MMSI number
			to_mmsi = int(telegram[5],16)
			# Application ID (Designated Area Code, DAC) + (Function
			# Identification, FI)
			appid = []
			for char in telegram[7]:
				appid.append(tobin(int(char,16),4))
			appid = ''.join(appid)
			dac = int(appid[0:10],2)
			fi = int(appid[10:16],2)
			# Try to decode message payload
			decoded = binaryparser(dac,fi,payload)
			# Return a dictionary with descriptive keys
			return {'mmsi': mmsi,
					'to_mmsi': to_mmsi,
					'dac': dac,
					'fi': fi,
					'decoded': decoded,
					'time': timestamp,
					'message': message}

		# If the sentence contains message 09 - Broadcast Binary Telegram:
		elif message == 'S09':
			# Binary data payload
			payload = []
			for char in telegram[4]:
				payload.append(tobin(int(char,16),4))
			payload = ''.join(payload)
			# Application ID (Designated Area Code, DAC) + (Function
			# Identification, FI)
			appid = []
			for char in telegram[6]:
				appid.append(tobin(int(char,16),4))
			appid = ''.join(appid)
			dac = int(appid[0:10],2)
			fi = int(appid[10:16],2)
			# Try to decode message payload
			decoded = binaryparser(dac,fi,payload)
			# Return a dictionary with descriptive keys
			return {'mmsi': mmsi,
					'dac': dac,
					'fi': fi,
					'decoded': decoded,
					'time': timestamp,
					'message': message}

		# If the sentence contains message 0D - Standard Position,
		# aviation, or message 11 - SAR Standard Position
		elif message == 'S0D' or message == 'S11':
			# Latitude in decimal degrees (DD)
			latitude = calclatitude(tobin(int(telegram[3],16),27))
			# Longitude in decimal degrees (DD)
			longitude = calclongitude(tobin(int(telegram[4],16),28))
			# Speed over ground in knots
			sog = int(telegram[5],16)
			if sog > 1022:
				sog = None # N/A
			# Course over ground in 1/10 degrees where 0=360
			cog = decimal.Decimal(int(telegram[6],16)) / 10
			if cog > 360: # 360 and above means 360=N/A
				cog = None
			# Altitude in meters, 4095=N/A
			altitude = int(telegram[7],16)
			if altitude == 4095:
				altitude = None # N/A
			# Return a dictionary with descriptive keys
			return {'mmsi': mmsi,
					'altitude': altitude,
					'sog': sog,
					'latitude': latitude,
					'longitude': longitude,
					'cog': cog,
					'time': timestamp,
					'message': message}

		# If the sentence contains 0E - Identification Data:
		elif message == 'S0E':
			# Name, removes the characters @, ' ' and "
			name = telegram[3].strip('''@ ''').replace('''"''',"'")
			# Callsign, removes the characters @, ' ' and "
			callsign = telegram[4].strip('''@ ''').replace('''"''',"'")
			# IMO number where 00000000=N/A
			imo = int(telegram[5],16)
			if imo == 0:
				imo = None
			# Return a dictionary with descriptive keys
			return {'mmsi': mmsi,
					'name': name,
					'callsign': callsign,
					'imo': imo,
					'time': timestamp,
					'message': message}

		# If the sentence contains 0F - Vessel Data:
		elif message == 'S0F':
			# Ship type, a two-digit code where 00=N/A
			type = int(telegram[3],16)
			if type == 0:
				type = None # N/A
			# Draught in 1/10 meters, where 0.0 = N/A
			draught = decimal.Decimal(int(telegram[4],16)) / 10
			if draught == 0:
				draught = None
			# Calculate ship width and length in meters from
			# antenna position in hex
			# Convert hex->int->bits
			ant_binnumber = tobin(int(telegram[5],16),count=30)
			# Add integers from the two parts to form length
			length = int(ant_binnumber[12:21],2) + int(ant_binnumber[21:30],2)
			# Add integers from the two parts to form width
			width = int(ant_binnumber[0:6],2) + int(ant_binnumber[6:12],2)
			# Destination, removes the characters @, ' ' and "
			destination = telegram[6].strip('''@ ''').replace('''"''',"'")
			# Received estimated time of arrival in format
			# month-day-hour-minute: MMDDHHMM where 00000000=N/A
			eta = telegram[8]
			if eta == '00000000':
				eta = None
			# Return a dictionary with descriptive keys
			return {'mmsi': mmsi,
					'type': type,
					'draught': draught,
					'length': length,
					'width': width,
					'destination': destination,
					'eta': eta,
					'time': timestamp,
					'message': message}

		else:
			# If we don't decode the message, at least return message type
			return {'mmsi': mmsi, 'time': timestamp, 'message': message, 'decoded': False}


	# If the sentence follows the ITU-R M.1371 standard:
	if telegram[0] == '!AIVDM':
		# Check the checksum
		if not checksum(inputstring):
			return

		# Convert the 6-bit string to a binary string
		bindata = sixtobin(telegram[5])

		# Extract the message type number
		message = str(int(bindata[0:6],2))

		# Get the source MMSI number
		mmsi = int(bindata[8:38],2)

		# Get current computer time to timestamp messages
		timestamp = datetime.datetime.now()

		# If the sentence contains message 1, 2 or 3 - Position Report:
		if message == '1' or message == '2' or message == '3':
			# Navigation status according to ITU-R M.1371
			navstatus = int(bindata[38:42],2)
			if navstatus == 0: navstatus = 0 # Under Way
			elif navstatus == 1: navstatus = 1 # At Anchor
			elif navstatus == 2: navstatus = 2 # Not Under Command
			elif navstatus == 3: navstatus = 3 # Restricted Manoeuvrability
			elif navstatus == 4: navstatus = 4 # Constrained by her draught
			elif navstatus == 5: navstatus = 5 # Moored
			elif navstatus == 6: navstatus = 6 # Aground
			elif navstatus == 7: navstatus = 7 # Engaged in Fishing
			elif navstatus == 8: navstatus = 8 # Under way sailing
			else: navstatus = None # N/A
			# Rate of turn in degrees/minute from -127 to +127 where 128=N/A
			sign_rateofturn = int(bindata[42])
			rateofturn = int(bindata[43:50],2)
			if rateofturn > 126:
				rateofturn = None # N/A
			elif sign_rateofturn and rateofturn > 1:
				# Turning left
				rateofturn = 128 - rateofturn
				# Convert between ROTais and ROTind
				rateofturn = -int(math.pow((rateofturn/4.733), 2))
				if rateofturn < -720:
					rateofturn = -720 # Full
			else:
				# Turning right
				# Convert between ROTais and ROTind
				rateofturn = int(math.pow((rateofturn/4.733), 2))
				if rateofturn > 720:
					rateofturn = 720 # Full
			# Speed over ground in 1/10 knots
			sog = decimal.Decimal(int(bindata[50:60],2)) / 10
			if sog > decimal.Decimal("102.2"):
				sog = None # N/A
			# Position accuracy where 0=bad and 1=good/DGPS
			posacc = int(bindata[60],2)
			# Longitude in decimal degrees (DD)
			longitude = calclongitude(bindata[61:89])
			# Latitude in decimal degrees (DD)
			latitude = calclatitude(bindata[89:116])
			# Course over ground in 1/10 degrees between 0-359
			cog = decimal.Decimal(int(bindata[116:128],2)) / 10
			if cog > 360: # 360 and above means 360=N/A
				cog = None
			# Heading in whole degrees between 0-359 and 511=N/A
			heading = int(bindata[128:137],2)
			if heading > 359:
				heading = None # N/A
			# Return a dictionary with descriptive keys
			return {'mmsi': mmsi,
					'rot': rateofturn,
					'navstatus': navstatus,
					'latitude': latitude,
					'longitude': longitude,
					'sog': sog,
					'cog': cog,
					'heading': heading,
					'posacc': posacc,
					'time': timestamp,
					'message': message}

		# If the sentence contains message 4 - Base Station Report:
		elif message == '4':
			# Bits 38-78 contains current station time in UTC
			try:
				station_time = datetime.datetime(int(bindata[38:52],2),
												 int(bindata[52:56],2),
												 int(bindata[56:61],2),
												 int(bindata[61:66],2),
												 int(bindata[66:72],2),
												 int(bindata[72:78],2))
			except ValueError:
				station_time = None # N/A
			# Position accuracy where 0=bad and 1=good/DGPS
			posacc = int(bindata[78],2)
			# Longitude in decimal degrees (DD)
			longitude = calclongitude(bindata[79:107])
			# Latitude in decimal degrees (DD)
			latitude = calclatitude(bindata[107:134])
			# Return a dictionary with descriptive keys
			return {'mmsi': mmsi,
					'station_time': station_time,
					'posacc': posacc,
					'latitude': latitude,
					'longitude': longitude,
					'time': timestamp,
					'message': message}

		# If the sentence contains message 5 - Ship Static and Voyage
		# Related Data:
		elif message == '5' and int(bindata[38:40],2) == 0:
			# IMO number where 00000000=N/A
			imo = int(bindata[40:70],2)
			if imo == 0:
				imo = None # N/A
			# Callsign, removes the characters @, ' ' and "
			callsign = bintoascii(bindata[70:112]).strip('''@ ''').replace('''"''',"'")
			# Name, removes the characters @, ' ' and "
			name = bintoascii(bindata[112:232]).strip('''@ ''').replace('''"''',"'")
			# Ship type, a two-digit code where 00=N/A
			type = int(bindata[232:240],2)
			if type == 0:
				type = None # N/A
			# Ship length calculated from antenna position
			length = (int(bindata[240:249],2) + int(bindata[249:258],2))
			# Ship width calculated from antenna position
			width = (int(bindata[258:264],2) + int(bindata[264:270],2))
			# Received estimated time of arrival in format
			# month-day-hour-minute: MMDDHHMM where 00000000=N/A
			eta = (str(int(bindata[274:278],2)).zfill(2) +
				  str(int(bindata[278:283],2)).zfill(2) +
				  str(int(bindata[283:288],2)).zfill(2) +
				  str(int(bindata[288:294],2)).zfill(2))
			if eta == '00000000':
				eta = None
			# Draught in 1/10 meters, where 0.0 == N/A
			draught = decimal.Decimal(int(bindata[294:302],2)) / 10
			if draught == 0:
				draught = None
			# Destination, removes the characters @, ' ' and "
			destination = bintoascii(bindata[302:422]).strip('''@ ''').replace('''"''',"'")
			# Return a dictionary with descriptive keys
			return {'mmsi': mmsi,
					'imo': imo,
					'callsign': callsign,
					'name': name,
					'type': type,
					'length': length,
					'width': width,
					'eta': eta,
					'destination': destination,
					'draught': draught,
					'time': timestamp,
					'message': message}

		# If the sentence contains message 6 - Addressed Binary Message:
		elif message == '6':
			# Sequence number
			sequence = int(bindata[38:40],2)
			# Destination MMSI number
			to_mmsi = int(bindata[40:70],2)
			# Application ID (Designated Area Code, DAC) + (Function
			# Identification, FI)
			dac = int(bindata[72:82],2)
			fi = int(bindata[82:88],2)
			# Binary data payload
			payload = bindata[88:1048]
			# Try to decode message payload
			decoded = binaryparser(dac,fi,payload)
			# Return a dictionary with descriptive keys
			return {'mmsi': mmsi,
					'sequence': sequence,
					'to_mmsi': to_mmsi,
					'dac': dac,
					'fi': fi,
					'decoded': decoded,
					'time': timestamp,
					'message': message}

		# If the sentence contains message 8 - Binary Broadcast Message:
		elif message == '8':
			# Application ID (Designated Area Code, DAC) + (Function
			# Identification, FI)
			dac = int(bindata[40:50],2)
			fi = int(bindata[50:56],2)
			# Binary data payload
			payload = bindata[56:1008]
			# Try to decode message payload
			decoded = binaryparser(dac,fi,payload)
			# Return a dictionary with descriptive keys
			return {'mmsi': mmsi,
					'dac': dac,
					'fi': fi,
					'decoded': decoded,
					'time': timestamp,
					'message': message}

		# If the sentence contains message 9 - SAR Aircraft position
		# report:
		elif message == '9':
			# Altitude in meters, 4095=N/A, 4094=>4094
			altitude = int(bindata[38:50],2)
			if altitude == 4095:
				altitude = None # N/A
			# Speed over ground in knots, 1023=N/A, 1022=>1022
			sog = int(bindata[50:60],2)
			if sog == 1023:
				sog = None # N/A
			# Position accuracy where 0=bad and 1=good/DGPS
			posacc = int(bindata[60],2)
			# Longitude in decimal degrees (DD)
			longitude = calclongitude(bindata[61:89])
			# Latitude in decimal degrees (DD)
			latitude = calclatitude(bindata[89:116])
			# Course over ground in 1/10 degrees between 0-359
			cog = decimal.Decimal(int(bindata[116:128],2)) / 10
			if cog > 360: # 360 and above means 360=N/A
				cog = None
			# Return a dictionary with descriptive keys
			return {'mmsi': mmsi,
					'altitude': altitude,
					'sog': sog,
					'posacc': posacc,
					'latitude': latitude,
					'longitude': longitude,
					'cog': cog,
					'time': timestamp,
					'message': message}

		# If the sentence contains message 12 - Addressed safety
		# related message:
		elif message == '12':
			# Sequence number
			sequence = int(bindata[38:40],2)
			# Destination MMSI number
			to_mmsi = int(bindata[40:70],2)
			# Content of message in ASCII (replace any " with ')
			content = bintoascii(bindata[72:1008]).replace('''"''',"'")
			# Return a dictionary with descriptive keys
			return {'mmsi': mmsi,
					'sequence': sequence,
					'to_mmsi': to_mmsi,
					'content': content,
					'time': timestamp,
					'message': message}

		# If the sentence contains message 14 - Safety related
		# Broadcast Message:
		elif message == '14':
			# Content of message in ASCII (replace any " with ')
			content = bintoascii(bindata[40:1008]).replace('''"''',"'")
			# Return a dictionary with descriptive keys
			return {'mmsi': mmsi,
					'content': content,
					'time': timestamp,
					'message': message}

		# If the sentence contains message 18 - Standard Class B CS
		# Position Report:
		elif message == '18':
			# Speed over ground in 1/10 knots
			sog = decimal.Decimal(int(bindata[46:56],2)) / 10
			if sog > decimal.Decimal("102.2"):
				sog = None # N/A
			# Position accuracy where 0=bad and 1=good/DGPS
			posacc = int(bindata[56],2)
			# Longitude in decimal degrees (DD)
			longitude = calclongitude(bindata[57:85])
			# Latitude in decimal degrees (DD)
			latitude = calclatitude(bindata[85:112])
			# Course over ground in 1/10 degrees between 0-359
			cog = decimal.Decimal(int(bindata[112:124],2)) / 10
			if cog > 360: # 360 and above means 360=N/A
				cog = None
			# Heading in whole degrees between 0-359 and 511=N/A
			heading = int(bindata[124:133],2)
			if heading > 359:
				heading = None # N/A
			# Return a dictionary with descriptive keys
			return {'mmsi': mmsi,
					'latitude': latitude,
					'longitude': longitude,
					'sog': sog,
					'cog': cog,
					'heading': heading,
					'posacc': posacc,
					'time': timestamp,
					'message': message}

		# If the sentence contains message 19 - Extended Class B
		# Equipment Position Report:
		elif message == '19':
			# Speed over ground in 1/10 knots
			sog = decimal.Decimal(int(bindata[46:56],2)) / 10
			if sog > decimal.Decimal("102.2"):
				sog = None # N/A
			# Position accuracy where 0=bad and 1=good/DGPS
			posacc = int(bindata[56],2)
			# Longitude in decimal degrees (DD)
			longitude = calclongitude(bindata[57:85])
			# Latitude in decimal degrees (DD)
			latitude = calclatitude(bindata[85:112])
			# Course over ground in 1/10 degrees between 0-359
			cog = decimal.Decimal(int(bindata[112:124],2)) / 10
			if cog > 360: # 360 and above means 360=N/A
				cog = None
			# Heading in whole degrees between 0-359 and 511=N/A
			heading = int(bindata[124:133],2)
			if heading > 359:
				heading = None # N/A
			# Name, removes the characters @, ' ' and "
			name = bintoascii(bindata[143:263]).strip('''@ ''').replace('''"''',"'")
			# Ship type, a two-digit code where 00=N/A
			type = int(bindata[263:271],2)
			if type == 0:
				type = None # N/A
			# Ship length calculated from antenna position
			length = (int(bindata[271:280],2) + int(bindata[280:289],2))
			# Ship width calculated from antenna position
			width = (int(bindata[289:295],2) + int(bindata[295:301],2))
			# Return a dictionary with descriptive keys
			return {'mmsi': mmsi,
					'latitude': latitude,
					'longitude': longitude,
					'sog': sog,
					'cog': cog,
					'heading': heading,
					'posacc': posacc,
					'name': name,
					'type': type,
					'length': length,
					'width': width,
					'time': timestamp,
					'message': message}

		# If the sentence contains message 24 - Class B CS Static Data
		# Report:
		elif message == '24':
			# See if it is message part A or B
			if int(bindata[38:40]) == 0: # Part A
				# Name, removes the characters @, ' ' and "
				name = bintoascii(bindata[40:160]).strip('''@ ''').replace('''"''',"'")
				# Return a dictionary with descriptive keys
				return {'mmsi': mmsi,
						'name': name,
						'time': timestamp,
						'message': message}
			else: # Part B
				# Ship type, a two-digit code where 00=N/A
				type = int(bindata[40:48],2)
				if type == 0:
					type = None # N/A
				# Vendor ID, removes the characters @, ' ' and "
				vendor = bintoascii(bindata[48:90]).strip('''@ ''').replace('''"''',"'")
				# Callsign, removes the characters @, ' ' and "
				callsign = bintoascii(bindata[90:132]).strip('''@ ''').replace('''"''',"'")
				# Ship length calculated from antenna position
				length = (int(bindata[132:141],2) + int(bindata[141:150],2))
				# Ship width calculated from antenna position
				width = (int(bindata[150:156],2) + int(bindata[156:162],2))
				# Return a dictionary with descriptive keys
				return {'mmsi': mmsi,
						'type': type,
						'vendor': vendor,
						'callsign': callsign,
						'length': length,
						'width': width,
						'time': timestamp,
						'message': message}

		else:
			# If we don't decode the message, at least return message type
			return {'mmsi': mmsi, 'time': timestamp, 'message': message, 'decoded': False}


	# If the sentence contains NMEA-compliant position data (from own GPS):
	if telegram[0] == '$GPGGA':
		# Check the checksum
		if not checksum(inputstring):
			return
		# Latitude
		degree = int(telegram[2][0:2])
		minutes = decimal.Decimal(telegram[2][2:9])
		if telegram[3] == 'N':
			latitude = degree + (minutes / 60)
		else:
			latitude = -(degree + (minutes / 60))
		latitude = latitude.quantize(decimal.Decimal('1E-6'))
		# Longitude
		degree = int(telegram[4][0:3])
		minutes = decimal.Decimal(telegram[4][3:10])
		if telegram[5] == 'E':
			longitude = degree + (minutes / 60)
		else:
			longitude = -(degree + (minutes / 60))
		longitude = longitude.quantize(decimal.Decimal('1E-6'))
		# Timestamp the message with local time
		timestamp = datetime.datetime.now()
		# Return a dictionary with descriptive keys
		return {'ownlatitude': latitude, 'ownlongitude': longitude, 'time': timestamp}


def binaryparser(dac,fi,data):
	# This function decodes known binary messages and returns the
	# interesting data as a dictionary where each key describes
	# the information of each message part.

	# For each value where we have a N/A-state None is returned

	# Initiate a return dict
	retdict = {}

	# If the message is IFM 0: free text message
	if dac == 1 and fi == 0:
		return {'text': bintoascii(data[12:]).strip('''@ ''').replace('''"''',"'")}

	# If the message is an IMO Meterology and Hydrology Message,
	# as specified in IMO SN/Circ. 236, Annex 2, Application 1:
	elif dac == 1 and fi == 11:
		# Latitude in decimal degrees (DD)
		retdict['latitude'] = calclatitude(data[0:24])
		# Longitude in decimal degrees (DD)
		retdict['longitude'] = calclongitude(data[24:49])
		# Bits 49-65 contains current station time in UTC (ddhhmm)
		# We use computer time as a baseline for year and month
		try:
			station_time = datetime.datetime.utcnow()
			station_time = station_time.replace(day=int(data[49:54],2),
												hour=int(data[54:59],2),
												minute=int(data[59:65],2),
												second=0, microsecond=0)
			retdict['station_time'] = station_time
		except ValueError:
			retdict['station_time'] = None # N/A
		# Average of wind speed values for the last ten minutes, knots
		retdict['average_wind_speed'] = standard_int_field(data[65:72])
		# Wind gust (maximum wind speed value) during the last ten
		# minutes, knots
		retdict['wind_gust'] = standard_int_field(data[72:79])
		# Wind direction in whole degrees
		retdict['wind_direction'] = standard_int_field(data[79:88])
		# Wind gust direction in whole degrees
		retdict['wind_gust_direction'] = standard_int_field(data[88:97])
		# Air temperature in 0.1 degrees Celsius from -60.0 to +60.0
		retdict['air_temperature'] = standard_decimal_tenth_signed_field(data[97:108])
		# Relative humidity in percent
		retdict['relative_humidity'] = standard_int_field(data[108:115])
		# Dew point in 0.1 degrees Celsius from -20.0 to +50.0
		retdict['dew_point'] = standard_decimal_tenth_signed_field(data[115:125])
		# Air pressure in whole hPa
		retdict['air_pressure'] = standard_int_field(data[125:134])
		# Air pressure tendency where 0=steady, 1=decreasing, 2=increasing
		retdict['air_pressure_tendency'] = standard_int_field(data[134:136])
		# Horizontal visibility in 0.1 NM steps
		retdict['horizontal_visibility'] = standard_decimal_tenth_field(data[136:144])
		# Water level including tide, deviation from local chart datum,
		# in 0.1 m from -10.0 to 30.0 m
		retdict['water_level_incl_tide'] = standard_decimal_tenth_signed_field(data[144:153])
		# Water level trend where 0=steady, 1=decreasing, 2=increasing
		retdict['water_level_trend'] = standard_int_field(data[153:155])
		# Surface current speed including tide in 0.1 kt steps
		retdict['surface_current_speed_incl_tide'] = standard_decimal_tenth_field(data[155:163])
		# Surface current direction in whole degrees
		retdict['surface_current_direction'] = standard_int_field(data[163:172])
		# Current speed #2, chosen below sea surface, in 0.1 kt steps
		retdict['current_speed_2'] = standard_decimal_tenth_field(data[172:180])
		# Current direction #2, chosen below sea surface in whole degrees
		retdict['current_direction_2'] = standard_int_field(data[180:189])
		# Current measuring level #2, whole meters below sea surface
		retdict['current_measuring_level_2'] = standard_int_field(data[189:194])
		# Current speed #3, chosen below sea surface, in 0.1 kt steps
		retdict['current_speed_3'] = standard_decimal_tenth_field(data[194:202])
		# Current direction #3, chosen below sea surface in whole degrees
		retdict['current_direction_3'] = standard_int_field(data[202:211])
		# Current measuring level #3, whole meters below sea surface
		retdict['current_measuring_level_3'] = standard_int_field(data[211:216])
		# Significant wave height in 0.1 m steps
		retdict['significant_wave_height'] = standard_decimal_tenth_field(data[216:224])
		# Wave period in whole seconds
		retdict['wave_period'] = standard_int_field(data[224:230])
		# Wave direction in whole degrees
		retdict['wave_direction'] = standard_int_field(data[230:239])
		# Swell height in 0.1 m steps
		retdict['swell_height'] = standard_decimal_tenth_field(data[239:247])
		# Swell period in whole seconds
		retdict['swell_period'] = standard_int_field(data[247:253])
		# Swell direction in whole degrees
		retdict['swell_direction'] = standard_int_field(data[253:262])
		# Sea state according to Beaufort scale (0-12)
		retdict['sea_state'] = standard_int_field(data[262:266])
		# Water temperature in 0.1 degrees Celsius from -10.0 to +50.0
		retdict['water_temperature'] = standard_decimal_tenth_signed_field(data[266:276])
		# Precipitation type according to WMO
		retdict['precipitation_type'] = standard_int_field(data[276:279])
		# Salinity in parts per thousand from 0.0 to 50.0
		retdict['salinity'] = standard_decimal_tenth_field(data[279:288])
		# Ice, Yes/No
		retdict['ice'] = standard_int_field(data[288:290])
		# Return a dictionary with descriptive keys
		return retdict

	# If we cannot decode the message, return None
	else:
		return None

def standard_int_field(data):
	# This function simplifies in checking for N/A-values
	# Check if just ones, then return N/A (Nonetype)
	if data.count('1') == len(data):
		return None
	else:
		return int(data,2)

def standard_int_signed_field(data):
	# This function simplifies in checking for N/A-values and signs
	# Check if just ones, then return N/A (Nonetype)
	if data.count('1') == len(data):
		return None
	else:
		# Return the signed integer
		if data[0]:
			# Positive
			return int(data[1:],2)
		else:
			# Negative
			return -int(data[1:],2)

def standard_decimal_tenth_field(data):
	# This function simplifies in checking for N/A-values
	# and returns a decimal.Decimal devided by 10
	# Check if just ones, then return N/A (Nonetype)
	if data.count('1') == len(data):
		return None
	else:
		return decimal.Decimal(int(data,2)) / 10

def standard_decimal_tenth_signed_field(data):
	# This function simplifies in checking for N/A-values and signs
	# and returns a decimal.Decimal devided by 10
	integer = standard_int_signed_field(data)
	if integer is None:
		return None
	else:
		return decimal.Decimal(integer) / 10

def tobin(x, count=8):
	# Convert the integer x to a binary representation where count is
	# the number of bits
	return "".join(map(lambda y:str((x>>y)&1), range(count-1, -1, -1)))

def makechecksum(s):
	# Calculate a checksum from sentence
	csum = 0
	i = 0
	s = s[1:s.rfind('*')] # Remove ! or $ and *xx in the sentence

	while (i < len(s)):
		inpt = binascii.b2a_hex(s[i])
		inpt = int(inpt,16)
		csum = csum ^ inpt #xor
		i += 1

	return csum

def checksum(s):
	# Create a checksum and compare it with the supplied checksum
	# If they are identical return 1, if not return 0
	try:
		# Create an integer of the two characters after the *, to the right
		supplied_csum = int(s[s.rfind('*')+1:s.rfind('*')+3], 16)
	except: return ''

	# Create the checksum
	csum = makechecksum(s)

	# Compare and return
	if csum == supplied_csum:
		return True
	else:
		return False

def sixtobin(encstring):
	# Converts encstring from coded 6-bit symbols to a binary string
	totalbin = ''
	for x in encstring[:]:
		# Loop over each symbol (x)
		# Convert x to the corresponding ASCII integer
		symbol = ord(x)
		# If the symbol does not exist in the character table, break loop
		if symbol < 48: break
		# If symbol match a certain table, subtract 48
		elif symbol < 88: symbol = symbol - 48
		# If the symbol does not exist in the character table, break loop
		elif symbol > 119: break
		# If symbol match a certain table, subtract 56
		else: symbol = symbol - 56
		# Add the bits from the integer symbol
		totalbin = totalbin + tobin(symbol, count=6)
	return totalbin

def bintoascii(binstring):
	# Converts binstring from binary integers to an ASCII string
	totalascii = ''
	inc = ''
	for x in binstring[:]:
		# Loop over each bit and add the bits until there are six of them
		inc = inc + x
		if len(inc) == 6:
			# Convert the six bits in inc to an integers
			symbol = int(inc,2)
			# If symbol is smaller than 32 add 64
			if symbol < 32: symbol = symbol + 64
			# Add the ASCII character to the string totalascii
			totalascii = totalascii + chr(symbol)
			inc = ''
	return totalascii

def calclatitude(binary_latitude):
	# Calculates latitude
	# First look at the signed bit
	sign = int(binary_latitude[0])
	latitude = int(binary_latitude[1:],2)
	# See how many bits we're looking at
	nr_bits = len(binary_latitude)
	if nr_bits == 24:
		factor = 60000 # 1000 * 60
		power = 23
	elif nr_bits == 27:
		factor = 600000 # 10000 * 60
		power = 26
	else:
		# Better to return None than a wrong value
		return None
	# See if the latitude are undefined (lat=91)
	if latitude == 91*factor:
		return None # N/A
	# Else, calculate the latitude
	if sign: # Negative == South
		latitude = pow(2,power) - latitude
		degree = -decimal.Decimal(latitude) / factor
	else: # Positive == North
		degree = decimal.Decimal(latitude) / factor
	# Return a value quantized to six decimal digits
	return degree.quantize(decimal.Decimal('1E-6'))

def calclongitude(binary_longitude):
	# Calculates longitude
	# First look at the signed bit
	sign = int(binary_longitude[0])
	longitude = int(binary_longitude[1:],2)
	# See how many bits we're looking at
	nr_bits = len(binary_longitude)
	if nr_bits == 25:
		factor = 60000 # 1000 * 60
		power = 24
	elif nr_bits == 28:
		factor = 600000 # 10000 * 60
		power = 27
	else:
		# Better to return None than a wrong value
		return None
	# See if the longitude are undefined (long=181)
	if longitude == 181*factor:
		return None # N/A
	# Else, calculate the longitude
	if sign: # Negative == West
		longitude = pow(2,power) - longitude
		degree = -decimal.Decimal(longitude) / factor
	else: # Positive == East
		degree = decimal.Decimal(longitude) / factor
	# Return a value quantized to six decimal digits
	return degree.quantize(decimal.Decimal('1E-6'))




'''
s = ["!AIVDO,1,1,,,B3P;s:@007vPcA7@dEaD?wP5wP06,0*3A",
"!AIVDM,1,1,,A,33P7jRP000wqsvTM5bhdibB>00wP,0*08",
"!AIVDM,1,1,,B,13P7ee@000wqsc:M5aeVrb0@0`5E,0*76",
"!AIVDM,1,1,,B,33QbwT1001Os;=PM0vp=360@0lkr,0*29",
"!AIVDO,1,1,,,B3P;s:@00GvPcA7@dEUEOwP5wP06,0*0F",
"!AIVDM,1,1,,A,33M@V`U000Ors:6M49rbos8B0000,0*0C",
"!AIVDM,1,1,,B,14hEVJ0001OsED>M0wIJ968D2@61,0*1C",
"!AIVDM,1,1,,A,13P;Qe@03RwriAPM2aKiVQFD1l1k,0*29",
"!AIVDM,1,1,,A,13P;i=P001wrteJM4g71f8rB086?,0*53",
"$GPGBS,225025.00,3.7,2.6,5.4,,,,*42",
"!AIVDO,1,1,,,B3P;s:@00GvPcA7@dEUFSwP5wP06,0*10",
"!AIVDM,1,1,,A,13M@F30001wqWDDM7I7uDBrD0`6J,0*61",
"!AIVDM,1,1,,A,16tL1v003=wvpa8Loa@as80B0<<P,0*42",
"!AIVDM,1,1,,A,13M@ENh000OrtThM4U>ueP>@0D1j,0*0C",
"$GPRMC,225026.00,A,5045.41035,N,00118.08954,W,0.16 4,140.39,280510,,,A*70",
"!AIVDO,1,1,,,B3P;s:@00GvPc@W@dEMGgwP5wP06,0*5C",
"!AIVDM,1,1,,B,13P7JTPu@;wrL`@M1ui8c6vB0D2j,0*7C",
"!AIVDM,1,1,,B,181:KU@001wqr4fM5mgKw4FH086u,0*51",
"!AIVDM,1,1,,B,33P88o@sR6wr5khM4i>eL:RF00wh,0*48",
"!AIVDM,2,1,3,A,53P;i=P2AG7c8<i3T010u9B0tJ1=04Tr000 0000S40s7740Hti@H54R@C4,0*5D",
"!AIVDM,2,2,3,A,h0000000001,2*7E",
"!AIVDM,1,1,,A,13cV5A002bOrIeTM324kqS:H0@7?,0*4B",
"!AIVDM,2,1,4,A,53OTJB000000mMICJ21HDi<PD@622222222 2220T28F155L<0<TkmE20CD53,0*1F",
"!AIVDM,2,2,4,A,k`5Bh000002,2*06",
"!AIVDO,1,1,,,B3P;s:@00GvPc@W@dEIHswP5wP06,0*43",
"!AIVDM,1,1,,A,19NWu15P1COrrtpM3t@66wvH0d2A,0*0B",
"!AIVDM,1,1,,B,33P7jRP000wqsvTM5bhdibBJ00lA,0*75",
"!AIVDM,1,1,,A,10FGp`?P?w<tSF0l4Q@>4?wv0`7t,0*12",
"!AIVDM,1,1,,A,13M@D8g001wqVGPM7gFn0V2F06k8,0*36",
"!AIVDM,1,1,,B,13P7bn0000wqWfTM7bAeQ5`J00SB,0*4C",
"!AIVDM,1,1,,A,13P9fuh000OqW10M7a89:THF2@87,0*69",
"!AIVDO,1,1,,,B3P;s:@00WvPc@7@dE=K;wP5wP06,0*0C",
"!AIVDM,1,1,,B,402=aTiuaNFj=OrrkDM4E`Q0288;,0*6D",
"!AIVDM,1,1,,B,13Q;0d001mOr4KPM4IN1cQHH00Rp,0*08",
"!AIVDM,1,1,,B,13M@F<O000OqWU@M7I5VVBtH0H8I,0*22",
"!AIVDM,1,1,,B,15R<5l0000wqqITM5qf<dTJJ0<2N,0*6F",
"$GPGBS,225029.00,3.9,2.7,5.5,,,,*40",
"!AIVDM,1,1,,B,13P9:j@000Oqsm8M5dvu37<N0D1a,0*3B",
"!AIVDO,1,1,,,B3P;s:@00WvPc?7@dE5M?wP5wP06,0*79",
"!AIVDM,1,1,,A,13M@D7@3j0Oqm1<M6EjTn3rL0<29,0*49",
"$GPRMC,225030.00,A,5045.40958,N,00118.08996,W,0.27 1,152.37,280510,,,A*70",
"!AIVDM,1,1,,A,13P88o@rj6wr5i>M4iieIbPN088t,0*7F",
"!AIVDM,1,1,,B,13P:RVh000OqtBvM5ahq@4HP0@8v,0*3D",
"!AIVDM,1,1,,A,33P7jRP000wqsvTM5bhdibBN0000,0*5F",
"!AIVDO,1,1,,,B3P;s:@00WvPc>W@dDuO?wP5wP06,0*5B",
"!AIVDM,1,1,,B,13P9?Dg000Or6DFM2HphKbhN00S0,0*28",
"!AIVDM,1,1,,B,13M@H25P?wwqK`pM806>4?vL0H9g,0*7A",
"!AIVDM,1,1,,B,16tL1v003=wvpE8Lo`m9s80N0@9h,0*5C",
"!AIVDO,1,1,,,B3P;s:@017vPc:7@dD1Q3wP5sP06,0*0C",
"!AIVDO,1,1,,,B3P;s:@017vPc77@dCIRWwP5sP06,0*19",
"!AIVDM,1,1,,A,13P7ee@000wqscDM5aeLF:0R0d1h,0*42",
"$GPGBS,225033.00,2.6,1.7,3.4,,,,*41",
"!AIVDM,1,1,,B,33P88o@sR6wr5hTM4irMDbNT01t@,0*67",
"!AIVDM,1,1,,B,13cV5A002bOrIubM31o3qC:V00S8,0*73",
"!AIVDM,2,1,5,A,53cV5A02<k`PT9@J220M84p@F0U@4hT6222 222163JF@?5N`0D1S5Dj2CQp8,0*70",
"!AIVDM,2,2,5,A,88888888881,2*20",
"!AIVDO,1,1,,,B3P;s:@017vPc57@dC1SwwP5sP06,0*42",
"!AIVDM,1,1,,B,33P7jRP000wqsvTM5bhdibBR011@,0*30",
"$GPRMC,225034.00,A,5045.40607,N,00118.09222,W,0.37 5,161.96,280510,,,A*7A",
"!AIVDM,1,1,,B,13P;i=P001wrteJM4g74p`rV06k8,0*5B",
"!AIVDO,1,1,,,B3P;s:@00ovPc37@dBiU?wP5sP06,0*0A",
"!AIVDM,1,1,,A,14hEVJ0001OsED:M0wHb968`2D2b,0*45",
"!AIVDM,1,1,,B,13IbAP0uAmOs0CdM3EMUt4fT08<4,0*0E",
"!AIVDO,1,1,,,B3P;s:@00ovPc27@dBaVOwP5sP06,0*70",
"!AIVDM,1,1,,A,13P7JTPsP8wrL`@M1ui80VtT0H<H,0*6D",
"!AIVDM,1,1,,A,33P88o@sR6wr5e<M4jUuG:Nb010h,0*1C",
"!AIVDM,1,1,,B,13M@ENh001OrtTlM4U>0FP>V0@<q,0*68",
"!AIVDO,1,1,,,B3P;s:@00ovPc1W@dBUWSwP5sP06,0*3A",
"!AIVDM,1,1,,B,19NWu15P1COrs0tM3sPV2wvb0Vk8,0*02",
"!AIVDM,1,1,,B,10FGp`?P?w<tSF0l4Q@>4?wv0h=5,0*52",
"!AIVDM,1,1,,A,13M@F<O000OqWTNM7IJFVBt`0@=<,0*11",
"!AIVDM,1,1,,A,181:KU@000wqr4bM5mgsw4Ff0<2H,0*7C",
"$GPGBS,225037.00,2.5,1.7,3.4,,,,*46",
"!AIVDM,1,1,,B,13M@D8g001wqVGPM7gG=F62`06k8,0*57",
"!AIVDM,1,1,,A,13P9:j@000Oqsm>M5dwM87<h0<1a,0*52",
"!AIVDM,1,1,,A,15R<5l0000wqqITM5qf<dTJb06k8,0*61",
"!AIVDO,1,1,,,B3P;s:@00GvPc17@dBUWcwP5sP06,0*42",
"$GPRMC,225038.00,A,5045.40572,N,00118.09318,W,0.25 1,167.63,280510,,,A*74",
"!AIVDM,1,1,,A,13P7bn0000wqWfVM7bAeQ5`f08=`,0*25",
"!AIVDM,1,1,,A,13P7jRP000wqsvTM5bhdibBf0L<O,0*7A",
"!AIVDM,1,1,,A,402=aTiuaNFjGOrrkDM4E`Q028>8,0*11",
"!AIVDO,1,1,,,B3P;s:@00WvPbvW@dBU`kwP5sP06,0*4B",
"!AIVDM,1,1,,B,13P9fuh000OqW10M7a89:THd20Rw,0*12",
"!AIVDM,1,1,,B,13M@D7@3j0Oqm?LM6Dw4pSth0<2:,0*17",
"!AIVDM,1,1,,A,13cV5A002aOrJ;PM31d3pS8j00S<,0*2C",
"!AIVDM,1,1,,B,13P88o@sR6wr5dNM4jfM?bLj00Rb,0*26",
"!AIVDO,1,1,,,B3P;s:@00WvPbu7@dBUakwP5sP06,0*29",
"!AIVDM,1,1,,A,13Q;0d001mOr4UlM4JE1cQJf0@>i,0*08",
"!AIVDM,1,1,,A,13P:RVh001OqtBvM5ak9@4Hl0H>u,0*45",
"!AIVDM,2,1,6,A,53M@H201prSTlMLsT00@tp4hB18D@Hu8@00 0000Q00m0;4t<06C@DPj5kki8,0*6A",
"!AIVDM,1,1,,B,33P7jRP000wqsvTM5bhdibBj0000,0*78",
"!AIVDO,1,1,,,B3P;s:@00WvPbtW@dBUbcwP5sP06,0*43",
"$GPGBS,225041.00,2.5,1.6,3.4,,,,*46",
"!AIVDM,1,1,,A,13P9?Dg000Or6DHM2HnhKbhl00SC,0*6A",
"!AIVDM,1,1,,A,13M@H25P?wwqK`pM806>4?vh06k8,0*2E",
"$GPRMC,225042.00,A,5045.40595,N,00118.09365,W,0.14 7,171.88,280510,,,A*7C",
"!AIVDO,1,1,,,B3P;s:@00GvPbt7@dBecKwP5sP06,0*2A",
"!AIVDM,1,1,,A,13P7EpPP00Orq3`M4:gWHgvp0H@7,0*3C",
"!AIVDM,2,1,7,B,53P7JTP2<tME`pq;D01=B0<h58D00000000 0000t01A0B5Dci6D3lU4p1RDj,0*4D",
"!AIVDM,2,2,7,B,0SmDSQ@0003,2*1B",
"!AIVDM,1,1,,B,13P7ee@000wqsc>M5aek?b0n0PS=,0*02",
"!AIVDO,1,1,,,B3P;s:@00GvPbt7@dBmckwP5sP06,0*02",
"!AIVDM,1,1,,A,33M@E;E000wrtPTM4TwPUP:n0000,0*0E",
"!AIVDM,1,1,,A,33P88o@sR6wr5`4M4kQu=:Jp01oh,0*27",
"!AIVDO,1,1,,,B3P;s:@00GvPbtW@dBqdCwP5sP06,0*51",
"!AIVDM,1,1,,B,16tL1v003=wvonPLo`:as80n06k8,0*5B",
"!AIVDM,1,1,,A,13P;i=P001wrteJM4g7;3`rr0D1H,0*68",
"!AIVDO,1,1,,,B3P;s:@007vPbu7@dC1dOwP5sP06,0*0D",
"!AIVDM,1,1,,B,13cV5A002aOrJFdM31RCok8t08Am,0*52",
"$GPGBS,225045.00,2.4,1.5,3.4,,,,*40",
"!AIVDM,2,1,8,B,50FGp`020<VDL90j220Pm>0QE9Lu9@R2222 2221J2Po8840Ht7d<<<<<8<<8,0*16",
"!AIVDM,2,2,8,B,88888888889,2*26",
"!AIVDM,1,1,,A,13M@ENh000OrtTLM4U:PFP>p0HB6,0*39",
"!AIVDM,1,1,,B,D02=aTh00000,0*33",
"$GPRMC,225046.00,A,5045.40658,N,00118.09329,W,0.05 3,173.80,280510,,,A*7C",
"!AIVDO,1,1,,,B3P;s:@007vPbv7@dC5dcwP5sP06,0*26",
"!AIVDM,1,1,,B,181:KU@000wqr4`M5mgKw4G006k8,0*31",
"!AIVDM,1,1,,B,33P7jRP000wqsvTM5bhdibBv015i,0*39",
"!AIVDM,1,1,,B,33P88o@sR6wr5VRM4kju:bHv0000,0*12",
"!AIVDO,1,1,,,B3P;s:@007vPbvW@dC=dwwP5sP06,0*5A",
"!AIVDM,1,1,,A,10FGp`?P?w<tSF0l4Q@>4?wv0`C9,0*2B",
"!AIVDM,1,1,,B,13P7JTPuP5wrL`@M1ui8c6rt06k8,0*29",
"!AIVDM,1,1,,B,13P7bn0000wqWf`M7bAeQ5a000SH,0*09",
"!AIVDM,1,1,,A,13M@D8g000wqVGPM7gG=5n0t0HCG,0*41",
"!AIVDM,1,1,,B,13M@F<O000OqWUlM7I4VVBtt08CI,0*38",
"!AIVDM,1,1,,A,33M@Dw?001wqHojM8@@AsK2v09l0,0*40",
"!AIVDO,1,1,,,B3P;s:@007vPbw7@dCEdowP5sP06,0*5B",
"!AIVDM,1,1,,A,13P9<@hrQpwrl4@M3B99W7Tv00Rm,0*56",
"!AIVDM,1,1,,B,402=aTiuaNFjQOrrkDM4E`Q028Cl,0*2D",
"!AIVDM,1,1,,B,15R<5l0000wqqITM5qf<dTK20@Cw,0*22"]
x=0
for p in s:
	x=x+1
	print x
	print telegramparser(p)
	print ''
	print ''
'''
