import gpx
import thread
import time
import datetime
import geomath
import math

class ROUTE():

	def __init__(self, cache):
		self.gpx_route           = None
		self.mode                = False
		#Lat, lon, name, distance, and bearing of current route waypoint
		self.waypoint_info       = {'lat': 0, 'lon': 0, 'name': '', 'distance': 0, 'bearing': 0}
		#Calculated distance and bearing to current waypoint
		self.waypoint_calc       = {'distance': 0, 'bearing': 0}
		#Hour and minutes to current waypoint
		self.waypoint_eta        = {'hour': '', 'min': ''}
		#The total distance of current route
		self.total_distance      = None
		#The estimated date of arrival for total route
		self.total_eta           = None
		
		self.xte_alarm           = 10
		self.xte_status          = False
		self.xte_angle           = [0,[0,0],0,[0,0]]
		#Current crosstrack error for waypoint
		self.waypoint_xte        = [0,'']
		self.cache				 = cache
		self.haversine           = geomath.haversine
		self.calc_line           = geomath.calc_line

	def switch(self, gpx_location):
		'''Checks whether Route Mode is enabled, and starts a routing, eta and crosstrack thread if so.'''
		if self.mode == False:
			self.mode = True
			self.gpx_route = gpx.GPX(gpx_location)
			self.gpx_route.route_start('Example.gpx')
			thread.start_new_thread(self.position, ())
			thread.start_new_thread(self.arrival, ())
			thread.start_new_thread(self.crosstrack, ())
		else:
			self.mode = False

	def position(self):
		'''Used to keep track of current position in relation to current route - run as thread.'''
		#Gets the next route position
		self.get(0)
		#Run while routing is enabled
		while self.mode == True:
			#Calculates distance between current position, and destination point
			waypoint_info = self.haversine(self.cache.lat_lon[0],self.cache.lat_lon[1],self.waypoint_info['lat'],self.waypoint_info['lon'])
			self.waypoint_calc = {'distance': waypoint_info[0], 'bearing': waypoint_info[1]}
			#Calculates total route distance
			self.total_distance = self.waypoint_calc['distance'] + self.gpx_route.route_distance
			#We're close to the destination - get the next point
			if self.waypoint_calc['distance'] < 0.02:
				self.get(0)
			time.sleep(1)

	def arrival(self):
		'''Calculates the estimated arrival time based on current speed - run as thread.'''
		#Loops until routing is turned off
		while self.mode == True:
			speed = round(self.cache.speed,2)
			#Make sure we do not divide by zero
			if speed > 0:
				time_current = datetime.datetime.now()
				#Determine time required for whole route
				time_total = self.total_distance / speed
				time_total_min, time_total_hour = math.modf(time_total)
				time_total_min = round(time_total_min*60)
				#Create a date/time object for ETA
				time_total = time_current + datetime.timedelta(hours=time_total_hour, minutes=time_total_min)
				self.total_eta = time_total.strftime("%Y-%m-%d %H:%M")
				#Determine time required for next point in route
				time_point = self.waypoint_calc['distance'] / speed
				time_point_min, time_point_hour = math.modf(time_point)
				time_point_min = round(time_point_min*60)
				#If time is too large to display properly
				if time_point_hour > 1000:
					self.waypoint_eta['hour'] = '1000'
				else:
					#Add a 0 if minutes are less then 10
					if time_point_min < 10:
						time_point_min = '0' + str(time_point_min)
					#Remove decimal points
					self.waypoint_eta['hour'] = int(str(time_point_hour).replace('.0',''))
					self.waypoint_eta['min'] = str(time_point_min).replace('.0','')
				time.sleep(4)
			#Do not estimate times if speed is 0
			else:
				self.total_eta = '           --'
				self.waypoint_eta['hour'] = '--'
				self.waypoint_eta['min'] = '--'

	def crosstrack(self):
		'''Calculates the crosstrack error for the current destination - run as thread.'''
		#Loops until routing is turned off
		while self.mode == True:
			#Make sure this is not the first point in the route (no standard bearing)
			if self.gpx_route.route_points[0][0] != self.waypoint_info['lat']:
				#Gets haversine info of last route point
				hav_start = self.haversine(self.gpx_route.route_points[self.gpx_route.route_position - 1][0], self.gpx_route.route_points[self.gpx_route.route_position - 1][1], self.cache.lat_lon[0], self.cache.lat_lon[1])
				#Crosstrack calculation
				self.waypoint_xte[0] = math.asin(math.sin(hav_start[0]/3443.92)*math.sin(hav_start[1]-self.gpx_route.route_points[self.gpx_route.route_position - 1][4]))*3443.92
				#Negative is left of course - making positive again
				if self.waypoint_xte[0] < 0:
					self.waypoint_xte[0] = self.waypoint_xte[0]*(-1)
					self.waypoint_xte[1] = 'L'
				#Right of course
				elif self.waypoint_xte[0] > 0:
					self.waypoint_xte[1] ='R'
				#Creates a crosstrack angle
				self.angle()
				#Checks for XTE alarm status
				if self.waypoint_xte[0] >= self.xte_alarm:
					self.xte_status == True
				elif self.waypoint_xte[0] < self.xte_alarm:
					self.xte_status == False
			#No current standard bearing
			else:
				self.waypoint_xte[0] = '    --'
				self.waypoint_xte[1] =''
			time.sleep(1)

	def angle(self):
		'''Calculates the crosstrack angle numbers for the interface.'''
		#Determines the positioning of the xte angle, based on xte distance
		if self.waypoint_xte[0] < 5:
			xte_lineadd = int(round(self.waypoint_xte[0]*10))
		else:
			xte_lineadd = 50
		#Adds/subs the above to the base position
		if self.waypoint_xte[1] == 'L':
			self.xte_angle[0] = 675 + xte_lineadd
		elif self.waypoint_xte[1] == 'R':
			self.xte_angle[0] = 675 - xte_lineadd
		#Determines how far away, in degrees, the current track is from the waypoint track
		self.xte_angle[2] = self.gpx_route.route_points[self.gpx_route.route_position - 1][4] - self.cache.track
		self.xte_angle[2] = round((self.xte_angle[2] + 180) % 360 - 180)
		#Negative is left, positive is right
		if self.xte_angle[2] < 0:
			xte_calc = 360 + self.xte_angle[2]
		elif self.xte_angle[2] > 0:
			xte_calc = 0 + self.xte_angle[2]
		else:
			xte_calc = 0
		xte_calc_opposite = (xte_calc + 180) % 360
		self.xte_angle[1] = self.calc_line(xte_calc,40,self.xte_angle[0],170)
		self.xte_angle[3] = self.calc_line(xte_calc_opposite,15,self.xte_angle[0],170)

	def get(self,pos):
		data = self.gpx_route.route_get(pos)
		self.waypoint_info = {'lat': data[0], 'lon': data[1], 'name': data[2], 'distance': data[3], 'bearing': data[4]}