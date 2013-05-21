import pygame
import time
import datetime

class GUI():

	def __init__(self):
		#Initialize pygame
		pygame.init()
		#Current version of NAVSTAT
		self.version             = None
		#Pixel size of the interface
		self.size                = [0,0]
		#Frame rate of the program
		self.frame_rate          = 29
		self.screen              = None
		self.clock               = pygame.time.Clock()
		#Switches for night and mini mode
		self.night               = False
		self.mini                = False
		#Colours avilable to use
		self.black               = (   0,   0,   0)
		self.white               = ( 255, 255, 255)
		self.red                 = ( 255,   0,   0)
		self.colour_1            = self.black
		self.colour_2            = self.white
		self.colour_1_2          = self.colour_1
		self.colour_2_2          = self.colour_2
		#4 font sizes that are available
		self.font_1              = pygame.font.Font(None, 18)
		self.font_2              = pygame.font.Font(None, 30)
		self.font_3              = pygame.font.Font(None, 25)
		self.font_4              = pygame.font.Font(None, 50)
		pygame.display.set_caption("NAVSTAT")

	def night_mode(self):
		'''Checks whether Night Mode is enabled, and changes colour scheme to match.'''
		if self.night == False:
			self.colour_1 = self.black
			self.colour_2 = self.red
			self.night = True
		elif self.night == True:
			self.colour_1 = self.colour_1_2
			self.colour_2 = self.colour_2_2
			self.night = False

	def mini_mode(self):
		'''Checks whether Mini Mode is enabled, and alters screen size if so.'''
		if self.mini == False: 
			self.screen = pygame.display.set_mode(self.size,pygame.RESIZABLE)
			self.mini = True
		else: 
			self.screen = pygame.display.set_mode(self.size,pygame.FULLSCREEN)
			self.mini = False

	def splash(self):
		'''Creates a splash screen while first booting.'''
		#Clears with background color
		self.screen.fill(self.colour_1)
		splash_font = pygame.font.Font(None, 60)
		#Draws the splash screen
		self.txt_out((splash_font.render('NAVSTAT', True, self.colour_2)),300,210)
		self.txt_out((self.font_3.render('Bluewater Mechanics', True, self.colour_2)),310,260)
		self.txt_out((self.font_1.render('version ' + self.version, True, self.colour_2)),740,480)
		pygame.display.update()
		time.sleep(2)

	def menu(self):
		'''Draws the menu interface common between all functions.'''
		#Clears with background color
		self.screen.fill(self.colour_1)
		#Display current time
		self.txt_out((self.font_2.render(datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), True, self.colour_2)),323,472)
		pygame.draw.rect(self.screen, self.colour_2, (0,500,800,30))
		pygame.draw.lines(self.screen, self.colour_2, False, [(0,465),(800,465)], 2)
		#Draw the various screen display options
		self.txt_out(self.font_3.render('GPS', True, self.colour_1),100,510)
		self.txt_out(self.font_3.render('MAP', True, self.colour_1),200,510)
		self.txt_out(self.font_3.render('AIS', True, self.colour_1),300,510)
		self.txt_out(self.font_3.render('ENG', True, self.colour_1),400,510)
		self.txt_out(self.font_3.render('OFF', True, self.colour_1),500,510)
		pygame.draw.rect(self.screen, self.colour_1, (68,500,100,10))
		#Monitors GPS status and displays problems
		#if self.cache.gps['status'] == 'A':
			#pygame.draw.circle(self.ui_screen, self.colour_1, (30,515), 10)
		#else:
			#pygame.draw.circle(self.ui_screen, self.colour_1, (30,515), 10,1)
		#if self.alarm.status == True:
			#self.txt_out(self.font_3.render('!!!!', True, self.colour_1),770,510)

	def txt_out(self,text, x, y):
		'''Gets pygame text ready to be outputted on screen.
		
		Keyword arguments:
		text -- the text that will be outputted
		x -- the horizontal position of the text
		y -- the vertical position of the text
		
		'''
		self.screen.blit(text, [x,y])