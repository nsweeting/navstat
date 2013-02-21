from datetime import datetime


class GPX():


	def __init__(self,location):
		self.gpx_doc = ''
		self.gpx_loc = location
		self.gpx_rte = []
		self.rte_pos = -1

	def trk_start(self):
		gpx_fle = str(datetime.now().strftime('%Y-%m-%d %H:%M')) + '.gpx'
		gpx_out = '<?xml version="1.0" encoding="UTF-8" standalone="no" ?>\n<gpx>\n\t<trk>\n\t\t<name>NAVSTAT TRACK</name>\n\t\t<trkseg>\n'
		self.gpx_doc = open(self.gpx_loc + gpx_fle, 'a')
		self.gpx_doc.write(gpx_out)


	def trkpt(self,lat,lon,ele,tme):
		gpx_out = '\t\t\t<trkpt lat="' + str(lat) + '" lon="' + str(lon) + '">\n' + '\t\t\t\t<ele>' + str(ele) + '</ele>\n' + '\t\t\t\t<time>' + str(tme) + '</time>\n\t\t\t</trkpt>\n'
		self.gpx_doc.write(gpx_out)


	def trk_close(self):
		gpx_out = '\t\t</trkseg>\n\t</trk>\n</gpx>'
		self.gpx_doc.write(gpx_out)
		self.gpx_doc.close()


	def rte_start(self,gpx_fle):
		lat_lon = [0,0,'']
		self.gpx_doc = open(self.gpx_loc + gpx_fle, 'r')
		con = 0
		for line in self.gpx_doc:
			if line.find('<rtept') != -1:
				start = line.find('lat=')
				end = line.find('lon=')
				lat_lon[0] = line[start + 5:end - 2]
				start = line.find('lon=')
				end = line.find('">')
				lat_lon[1] = line[start + 5:end]
				con = 1
			if line.find('<name>') != -1 and con == 1:
				start = line.find('<name>')
				end = line.find('</name>')
				lat_lon[2] = line[start + 6:end]
				self.gpx_rte.append(lat_lon)
				lat_lon = [0,0,'']
				con = 0


	def rte_get(self):
		self.rte_pos = self.rte_pos + 1
		return self.gpx_rte[self.rte_pos]
