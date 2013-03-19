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
	radius = 6378.137
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