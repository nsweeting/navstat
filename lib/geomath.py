import math

def haversine(lat_1,lon_1,lat_2,lon_2):
	'''Calculates the distance between two coordinates.
	
	Keyword arguments:
	lat_1 -- the base coordinate latitude
	lon_1 -- the base coordinate longitude
	lat_2 -- the alternate coordinate latitude
	lon_2 -- the alternate coordinate longitude
	
	'''
	#Earth radius
	try:
		radius = 3443.92
		lon_1, lat_1, lon_2, lat_2 = map(math.radians, [lon_1, lat_1, lon_2, lat_2])
		dst_lon = lon_2 - lon_1
		dst_lat = lat_2 - lat_1
		a = math.sin(dst_lat/2)**2 + math.cos(lat_1) * math.cos(lat_2) * math.sin(dst_lon/2)**2
		c = 2 * math.asin(math.sqrt(a))
		dis_out = radius * c
		y = math.sin(dst_lon) * math.cos(lat_2)
		x = math.cos(lat_1) * math.sin(lat_2) - math.sin(lat_1) * math.cos(lat_2) * math.cos(dst_lon)
		brg_out = math.degrees(math.atan2(y, x))
		brg_out = (brg_out + 360) % 360
		return [round(dis_out,2),round(brg_out)]
	except:
		pass

def calc_line(degree,radius,x,y):
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

def unit_convert(unit,type,num):
	'''Converts unit output units to the units of choice.
	
	Keyword arguments:
	type -- The type of unit to convert, distance = 0, speed = 1.
	num -- The number that needs to be converted.
	
	'''
	#This converts distance to choice of unit. Starts in km.
	try:
		if type == 0:
			#Kilometers
			if unit[0] == 0:
				return round(num*1.852,2)
			#Miles
			elif unit[0] == 1:
				return round(num*0.621371,2)
			#Nautical Miles
			elif unit[0] == 2:
				return round(num,2)
		#This converts speed to choice of unit. Starts in knots.
		elif type == 1:
			#Kilometers / Hour
			if unit[1] == 0:
				return round(num*1.852,2)
			#Miles / Hour
			elif unit[1] == 1:
				return round(num*1.15078,2)
			#Nautical Miles / Hour
			elif unit[1] == 2:
				return round(num,2)
	except:
		return num

def calc_size(num):
	'''Calculates the additional x pixels required to centre a number based on number size .
	
	Keyword arguments:
	num -- the number to size up
	
	'''
	if num >= 0 and num < 10:
		ext = 40
	elif num >= 10 and num < 100:
		ext = 34
	elif num >= 100 and num < 1000:
		ext = 24
	elif num >= 1000 and num < 10000:
		ext = 14
	elif num >= 10000 and num < 100000:
		ext = 0
	else:
		return 40
	#Returns the additional number of pixels required
	return ext