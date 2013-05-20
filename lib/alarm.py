class ALARM():

	def __init__(self):
		self.xte        = False
		self.status     = False

	def check(self):
		self.status = False
		if self.xte == True:
			self.status = True