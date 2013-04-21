import gpx
import time
import thread


class TRACK():

	def __init__(self, cache):
		self.mode                = False
		#Holds track point info for future file output
		self.route               = []
		#Number of seconds between each track point. Number of points between each track file output
		self.save_info           = [10,6]
		#The max size of a track file
		self.maxsize             = None
		self.gpx_track           = None
		self.cache               = cache

	def switch(self, gpx_location):
		'''Checks whether Track Mode is enabled, and starts a tracking thread if so.'''
		if self.mode == False:
			self.mode = True
			self.gpx_track = gpx.GPX(gpx_location)
			self.gpx_track.track_start()
			thread.start_new_thread(self.start, ())
		else:
			self.mode = False
			self.off()

	def start(self):
		'''Used as a thread to save tracking info for future file output.'''
		x = 0
		#Loop that keeps track of time, and saves track info based on this time
		while self.mode == True:
			self.route.append([self.cache.lat_lon,self.cache.utc])
			x = x + 1
			if x > self.save_info[1]:
				self.make()
				#If the file hits the maximum size, start a new one
				if self.gpx_track.track_size > self.maxsize and self.track == True:
					self.gpx_track.track_close()
					self.gpx_track.track_size = 0
					self.gpx_track.track_start()
				self.route = []
				x = 0
			time.sleep(self.save_info[0])

	def off(self):
		'''Cleans up and closes the current track file open.'''
		if self.gpx_track:
			if self.route:
				self.make()
			#Cleans and closes track variables and files
			self.gpx_track.track_close()
			self.gpx_track = None
			self.route = []

	def make(self):
		'''Outputs the track info to the current track file.'''
		#Runs through each track point for output
		for point in self.route:
			self.gpx_track.track_point(point[0][0], point[0][1], 0, point[1])