import pygame as pg
from pygame import gfxdraw
from PIL import Image
import random
import datetime as dt
from datetime import timedelta
import json
import os
from os import listdir
from os.path import isfile, join
import sys

# initialise pygame
pg.init()
clock = pg.time.Clock()
running = True

# scaling factor
# 1 = 640, 360
# 2 = 1280, 720
# 3 = 1920, 1080
SF = 2
WIDTH, HEIGHT = 640 * SF, 360 * SF
screen = pg.display.set_mode((WIDTH, HEIGHT), pg.DOUBLEBUF | pg.HWSURFACE, vsync=1)
FPS = 60

musicVolume = 0.0
sfxVolume = 0.5
masterVolume = 1.0

try:
	backgroundMusic = pg.mixer.Sound("assets/sounds/background.wav")
	backgroundMusic.set_volume(musicVolume * masterVolume)
	backgroundMusic.play(loops=-1)
except:
	backgroundMusic = None

texturePath = "assets/textures/"
tempTexturePath = "temp/assets/textures/"


# colours
colBlack = (0, 0, 0)
colWhite = (255, 255, 255)
colLightGray = (205, 205, 205)
colDarkGray = (55, 55, 55)
colRed = (200, 0, 0)
colGreen = (0, 200, 0)
colBlue = (0, 0, 200)
colOrange = (255, 145, 0)
colLightRed = (255, 48, 0)
colLightGreen = (0, 255, 48)
colLightBlue = (48, 0, 255)
colYellow = (200, 200, 0)

# create font object
FONT = pg.font.SysFont("arial", 8 * SF)

# contains all objects
allButtons = []
allSliders = []
allLabels = []
allSliders = []
allBullets = []
allEnemies = []
allPowerUps = [] 

buttonWidth, buttonHeight = 30, 30

savePath = "saveData.json"

gameState = "start menu"

powerUpSpawnChance = 40 # as percentage
numOfEnemies = 10

gameData = {
	"level": 1,
	"totalScore": 0
}

bulletData = {
	"speed": 4.5
}

playerData = {
	"speed": 3,
	"health": 100,
	"scoreAmount": 10,
	"hurtAmount": 10,
	"numberOfshots": 1,
	"bullets": {
		"numOfbullets": int(numOfEnemies * 1.5),
		"maxAmount": int(numOfEnemies * 1.5),
		"refillRate": 5,
	}
}

enemyData = {
	"speed": {
		"x": 1.5,
		"y": 0.1
	},
	"drawData": {
		"width": 15,
		"height": 15
	}
}

powerUpData = {
	"speed": 4,
	"abilityNames": ["Add health", "Refill bullets", "Increase speed", "IncreaseShots"],
	"Add health": {
		"color": colGreen,
		"attribute": "health",
		"value": 10,
		"duration": 0,
	},
	"Refill bullets": {
		"color": colBlue,
		"attribute": "numOfbullets",
		"value": playerData["bullets"]["maxAmount"],
		"duration": 0,
	},
	"Increase speed": {
		"color": colOrange,
		"attribute": "speed",
		"value": 1.5 * SF,
		"duration": 5,
	},
	"IncreaseShots": {
		"color": colYellow,
		"attribute": "numberOfshots",
		"value": 2,
		"duration": 15,	
	}
}

collideingRect = pg.Rect(0 + (enemyData["drawData"]["width"] * SF), 0, WIDTH - (enemyData["drawData"]["width"] * 2) * SF, HEIGHT)


def DrawRectOutline(surface, color, rect, width=1):
	x, y, w, h = rect
	width = max(width, 1)  # Draw at least one rect.
	width = min(min(width, w//2), h//2)  # Don't overdraw.

	# This draws several smaller outlines inside the first outline
	# Invert the direction if it should grow outwards.
	for i in range(int(width)):
		pg.gfxdraw.rectangle(surface, (x+i, y+i, w-i*2, h-i*2), color)


def DrawObround(surface, color, rect, filled=False, additive=True):
	x, y, w, h = rect
	radius = h // 2	
	# check if semicircles are added to the side or replace the side
	if not additive:
		x += radius
		w -= radius * 2
	# checks if it should be filled
	if not filled:
		pg.draw.aaline(surface, color, (x, y), (x + w, y), 3 * SF)
		pg.draw.aaline(surface, color, (x, y + h), (x + w, y + h), 3 * SF)
		pg.gfxdraw.arc(surface, x, y + radius, radius, 90, -90, color)
		pg.gfxdraw.arc(surface, x + w, y + radius, radius, -90, 90, color)
	else:
		pg.gfxdraw.filled_circle(surface, x, y + radius, radius, color)	
		pg.gfxdraw.filled_circle(surface, x + w, y + radius, radius, color)	
		pg.draw.rect(surface, color, (x, y, w, h))	


def GetCenterOfRect(rect):
	x, y, w, h = rect
	midX, midY = (x + w) // 2, (y + h) // 2
	return midX, midY


def ScaleImage(imagePath, imageScale, newImagePath):
	image = Image.open(imagePath)
	image = image.resize((imageScale[0], imageScale[1]))
	image.save(newImagePath)


class HoldButton:
	def __init__(self, surface, rect, buttonType, colorData, textData, actionData=[], lists=[allButtons], extraText=[], extraData=[], imageData=[None]):
		"""
		Parameters: 
			buttonType: tuple of gameState type and button action
			colorData: tuple of active color and inactive color
			textData: tuple of text and text color
			actionData: list of any additional button action data
			lists: list of lists to add self too
			extraText: list of tuples containing the text and the rect
			imageData: list of image path and scaled image path
		"""
		self.surface = surface
		self.originalRect = rect
		self.rect = pg.Rect(rect[0] * SF, rect[1] * SF, rect[2] * SF, rect[3] * SF)
		self.type = buttonType[0] 
		self.action = buttonType[1]
		self.active = False
		self.activeColor = colorData[0]
		self.inactiveColor = colorData[1]
		self.currentColor = self.inactiveColor
		self.text = textData[0]
		self.textColor = textData[1]
		self.textSurface = FONT.render(self.text, True, self.textColor)
		self.extraText = extraText
		self.extraData = extraData
		self.actionData = actionData
		for listToAppend in lists:
			listToAppend.append(self)
		
		self.imageData = imageData
		if self.imageData[0] != None:
			self.hasImage = True
		else:
			self.hasImage = False

		self.Rescale()

	# rescale all elements
	def Rescale(self):
		self.rect = pg.Rect(self.originalRect[0] * SF, self.originalRect[1] * SF, self.originalRect[2] * SF, self.originalRect[3] * SF)
		self.extraTextSurfaces = [] 
		for textData in self.extraText:
			textSurface = FONT.render(str(textData[0]), True, self.textColor)
			self.extraTextSurfaces.append((textSurface, ((textData[1][0] * SF) - textSurface.get_width() // 2, (textData[1][1] * SF) - textSurface.get_height() // 2)))
		try:
			if self.hasImage:
				ScaleImage(self.imageData[0], (self.rect.w, self.rect.h), self.imageData[1])
				self.image = pg.image.load(self.imageData[1])
				self.image.convert()
		except:
			print("{} has no image".format(self.action))
			self.hasImage = False

	def Draw(self):
		if not self.hasImage:
			pg.draw.rect(self.surface, self.currentColor, self.rect)
			self.surface.blit(self.textSurface, self.rect)
		else:
			self.surface.blit(self.image, self.rect)

		for textSurfaceData in self.extraTextSurfaces:
			self.surface.blit(textSurfaceData[0], textSurfaceData[1])


	def HandleEvent(self, event):
		# check for left mouse down
		if event.type == pg.MOUSEBUTTONDOWN:
			if event.button == 1:
				if self.rect.collidepoint(pg.mouse.get_pos()):
					self.active = True

		# check for left mouse up
		if event.type == pg.MOUSEBUTTONUP:
			if event.button == 1:
				self.active = False

		# change color
		if self.active:
			self.currentColor = self.activeColor
		else:
			self.currentColor = self.inactiveColor

	def ChangeRect(self, newRect):
		self.rect = pg.Rect(newRect)
		self.extraTextSurfaces = [] 
		for textData in self.extraText:
			textSurface = FONT.render(str(textData[0]), True, self.textColor)
			self.extraTextSurfaces.append((textSurface, ((self.rect.x + self.rect.w // 2) - textSurface.get_width() // 2, (self.rect.y + self.rect.h // 2) - textSurface.get_height() // 2)))

	def UpdateText(self, text):
		self.textSurface = FONT.render(str(text), True, self.textColor)

	def UpdateExtraText(self, extraText):
		self.extraTextSurfaces = []
		for textData in extraText:
			textSurface = FONT.render(str(textData[0]), True, self.textColor)
			self.extraTextSurfaces.append((textSurface, ((textData[1][0] * SF) - textSurface.get_width() // 2, (textData[1][1] * SF) - textSurface.get_height() // 2)))


class Slider:
	def __init__(self, surface, rect, sliderType, colors, textData, bounds, lists=[allSliders], drawData=[True]):
		"""
		Parameters:
			sliderType: tuple of gameState type and slider action
			colors: tuple of border, active color and inactive color
			textData: tuple of text and text color and antialliasing
			bounds: tuple of lower bound and upper bound
			lists: list of lists to add self too
			drawData: list of rounded edges
		"""
		self.surface = surface
		self.originalRect = rect
		self.type = sliderType[0]
		self.action = sliderType[1]
		self.borderColor = colors[0]
		self.activeColor = colors[1]
		self.inactiveColor = colors[2]
		self.sliderColor = self.inactiveColor
		self.bounds = bounds
		self.text = textData[0]
		self.textColor = textData[1]
		self.aa = textData[2]
		self.value = round(self.bounds[0], 0)
		self.roundedEdges = drawData[0]
		self.active = False
		self.direction = "none"
		self.Rescale()
		for listToAppend in lists:
			listToAppend.append(self)

	# rescale all elements
	def Rescale(self):
		self.rect = pg.Rect(self.originalRect[0] * SF, self.originalRect[1] * SF, self.originalRect[2] * SF, self.originalRect[3] * SF)
		self.font = pg.font.SysFont("arial", self.aa * SF)
		self.textSurface = FONT.render(self.text, True, self.textColor)
		self.segmentLength = self.rect.w / self.bounds[1]
		self.sliderRect = pg.Rect(self.rect.x, self.rect.y, max(self.segmentLength, self.textSurface.get_width()), self.rect.h)
		self.collisionRect = pg.Rect(self.sliderRect.x - self.sliderRect.h // 2, self.sliderRect.y, self.sliderRect.w + self.sliderRect.h, self.sliderRect.h)
	
	def Draw(self, width=3):
		if self.roundedEdges:
			# draw outline
			DrawObround(self.surface, self.borderColor, self.rect)
			# draw slider
			DrawObround(self.surface, self.sliderColor, self.sliderRect, True)
			# draw text
		else:
			DrawRectOutline(self.surface, self.borderColor, self.rect)
			pg.draw.rect(self.surface, self.sliderColor, self.sliderRect)

		self.surface.blit(self.textSurface, ((self.sliderRect.x + self.sliderRect.w // 2) - self.textSurface.get_width() // 2, (self.sliderRect.y + self.sliderRect.h // 2) - self.textSurface.get_height() // 2))

	def HandleEvent(self, event):
		# check for left mouse button down
		if event.type == pg.MOUSEBUTTONDOWN:
			if event.button == 1:
				mousePos = pg.mouse.get_pos()
				if self.collisionRect.collidepoint(mousePos):
					self.active = True

		# check for left mouse button up
		if event.type == pg.MOUSEBUTTONUP:
			if event.button == 1:
				self.active = False

		# change color
		if self.active:
			self.sliderColor = self.activeColor
			self.MoveSlider()
		else:
			self.sliderColor = self.inactiveColor

	# change slider position
	def MoveSlider(self):
		# get slider direction
		motion = pg.mouse.get_rel()
		if motion[0] <= 0:
			self.direction = "left"
		elif motion[0] > 0:
			self.direction = "right"

		# set the slider x to mouse x
		mousePosX = pg.mouse.get_pos()[0]
		if mousePosX < self.rect.x + self.rect.w - self.sliderRect.w // 2:
			if mousePosX > self.rect.x + self.sliderRect.w // 2:
				self.sliderRect.x = mousePosX - self.sliderRect.w // 2
				self.ChangeValue()
		# update rect and text
		self.collisionRect = pg.Rect(self.sliderRect.x - self.sliderRect.h // 2, self.sliderRect.y, self.sliderRect.w + self.sliderRect.h, self.sliderRect.h)
		self.textSurface = FONT.render(self.text, True, self.textColor)

	def ChangeValue(self):
		self.value = max(round(((self.sliderRect.x - self.rect.x) / self.rect.w) * (self.bounds[1] + 1), 0), self.bounds[0])

	def ChangeRect(self):
		self.sliderRect.x = self.value * self.segmentLength


class Label:
	def __init__(self, surface, rect, gameStateType, colors, textData, drawData=[False, False, True], lists=[allLabels], extraText=[], extraData=[]):
		"""
		Parameters:
			gameStateType: Which gameState to be drawn in
			colors: tuple of border color, background color
			textData: tuple of text, text color, font size, how to align text
			drawData: tuple of rounded edges, addititve, filled
			extraText: any additional text
			extraData: any additional data
		"""
		self.surface = surface
		self.originalRect = rect
		self.gameStateType = gameStateType
		self.borderColor = colors[0]
		self.backgroundColor = colors[1]
		self.text = str(textData[0])
		self.textColor = textData[1]
		self.fontSize = textData[2]
		self.alignText = textData[3]

		self.roundedEdges = drawData[0]
		self.additive = drawData[1]
		self.filled = drawData[2]

		self.extraText = extraText
		self.extraData = extraData

		self.Rescale()

		for listToAppend in lists:
			listToAppend.append(self)

	# rescale all elements
	def Rescale(self):
		self.rect = pg.Rect(self.originalRect[0] * SF, self.originalRect[1] * SF, self.originalRect[2] * SF, self.originalRect[3] * SF)
		self.font = pg.font.SysFont("arial", self.fontSize * SF)
		self.textSurface = self.font.render(self.text, True, self.textColor)
		if self.alignText == "center-center":
			self.textRect = pg.Rect((self.rect[0] + self.rect[2] // 2) - self.textSurface.get_width() // 2, (self.rect[1] + self.rect[3] // 2) - self.textSurface.get_height() // 2, self.rect[2], self.rect[3])
		elif self.alignText == "top-center":
			self.textRect = pg.Rect((self.rect[0] + self.rect[2] // 2) - self.textSurface.get_width() // 2, self.rect[1] + 3 * SF, self.rect[2], self.rect[3])
		elif self.alignText == "top-left":
			self.textRect = (self.rect.x + 3 * SF, self.rect.y + 3 * SF)
		else:
			self.textRect = (self.rect.x + 5 * SF, self.rect.y + 5 * SF)

		self.extraTextSurfaces = []
		for textData in self.extraText:
			textSurface = FONT.render(str(textData[0]), True, self.textColor)
			x, y = textData[1][0] * SF, textData[1][1] * SF
			alignText = textData[2]
			textSurface = FONT.render(str(textData[0]), True, self.textColor)
			if alignText == "center-center":
				textRect = (x + self.rect.w // 2) - self.textSurface.get_width() // 2, (y + self.rect.h // 2) - self.textSurface.get_height() // 2, self.rect.w, self.rect.h
			elif alignText == "top-center":
				textRect = (x + self.rect.w // 2) - self.textSurface.get_width() // 2, y + 3 * self.rect.w
			elif alignText == "top-left":
				textRect = (x + 5 * SF, y + 5 * SF)

			self.extraTextSurfaces.append((textSurface, textRect))

	def Draw(self):
		if self.roundedEdges:
			DrawObround(screen, self.backgroundColor, self.rect, self.filled, self.additive)
			DrawObround(screen, colDarkGray, (self.rect.x + 3, self.rect.y + 3, self.rect.w - 6, self.rect.h - 6), self.filled, self.additive)
		else:
			pg.draw.rect(screen, self.backgroundColor, self.rect)
			if self.borderColor != False:
				DrawRectOutline(screen, self.borderColor, self.rect, 1.5 * SF)
		self.surface.blit(self.textSurface, self.textRect)

		for textSurface in self.extraTextSurfaces:
			self.surface.blit(textSurface[0], textSurface[1])

	def UpdateText(self, text):
		self.textSurface = self.font.render(text, True, self.textColor)
		if self.alignText == "center-center":
			self.textRect = pg.Rect((self.rect[0] + self.rect[2] // 2) - self.textSurface.get_width() // 2, (self.rect[1] + self.rect[3] // 2) - self.textSurface.get_height() // 2, self.rect[2], self.rect[3])
		elif self.alignText == "top-center":
			self.textRect = pg.Rect((self.rect[0] + self.rect[2] // 2) - self.textSurface.get_width() // 2, self.rect[1] + 3 * SF, self.rect[2], self.rect[3])
		elif self.alignText == "top-left":
			self.textRect = (self.rect.x + 3 * SF, self.rect.y + 3 * SF)
		else:
			self.textRect = (self.rect.x + 5 * SF, self.rect.y + 5 * SF)

	def UpdateExtraText(self, text):
		self.extraText = text
		self.extraTextSurfaces = []
		for textData in self.extraText:
			textSurface = FONT.render(str(textData[0]), True, self.textColor)
			x, y = textData[1][0] * SF, textData[1][1] * SF
			alignText = textData[2]
			textSurface = FONT.render(str(textData[0]), True, self.textColor)
			if alignText == "center-center":
				textRect = (self.rect.x + self.rect.w // 2) - textSurface.get_width() // 2, (y + self.rect.h // 2) - self.textSurface.get_height() // 2, self.rect.w, self.rect.h
			elif alignText == "top-center":
				textRect = (self.rect.x + self.rect.w // 2) - textSurface.get_width() // 2, y
			elif alignText == "top-left":
				textRect = (x + 5 * SF, y + 5 * SF)
			else:
				textRect = (x + 5 * SF, y + 5 * SF)

			self.extraTextSurfaces.append((textSurface, textRect))


class Bullet:
	def __init__(self, surface, rect, color, lists=[allBullets], data=bulletData):
		self.surface = surface
		self.originalRect = rect
		self.color = color
		self.data = data
		self.lists = lists

		self.direction = [0, -1]
		self.speed = data["speed"]

		self.Rescale()

		for listToAppend in self.lists:
			listToAppend.append(self)

	def Rescale(self):
		self.rect = pg.Rect(self.originalRect[0] * SF, self.originalRect[1] * SF, self.originalRect[2] * SF, self.originalRect[3] * SF)
		self.pos = [self.rect.x, self.rect.y]

	def Draw(self):
		pg.draw.rect(self.surface, self.color, self.rect)

	def Move(self):
		if not self.rect.colliderect(0, 0, WIDTH, 100000000):
			for listToAppend in self.lists:
				listToAppend.remove(self)
		
		self.pos[1] += self.direction[1] * (self.speed * SF)
		self.rect.y = self.pos[1]

		if self.rect.y >= player.rect.y:
			self.rect.x = player.rect.x + random.randint(-5, 10)

	def Destroy(self):
		for listToAppend in self.lists:
			listToAppend.remove(self)


class Player:
	def __init__(self, surface, rect, color, data=playerData, imageData=[None]):
		self.surface = surface
		self.originalRect = rect
		self.color = color
		# never changed
		self.originalData = data
		# changes in runtime
		self.data = data

		self.direction = [0, 0]
		self.speed = data["speed"]

		self.numOfbullets = data["bullets"]["numOfbullets"]
		self.bulletRefillRate = data["bullets"]["refillRate"]
		self.maxAmountBullets = data["bullets"]["maxAmount"]
		self.numberOfshots = data["numberOfshots"]

		self.score = 0
		self.scoreAmount = data["scoreAmount"]
		self.health = 100
		self.hurtAmount = data["hurtAmount"]

		self.refilling = False
		self.activePowerUps = []

		self.imageData = imageData
		if self.imageData[0] != None:
			self.hasImage = True
		else:
			self.hasImage = False

		self.Rescale()

	def Rescale(self):
		self.rect = pg.Rect(self.originalRect[0] * SF, self.originalRect[1] * SF, self.originalRect[2] * SF, self.originalRect[3] * SF)
		try:
			if self.hasImage:
				ScaleImage(self.imageData[0], (self.rect.w, self.rect.h), self.imageData[1])
				self.image = pg.image.load(self.imageData[1])
		except:
			print("No image found")
			self.hasImage = False

	def Draw(self):
		if not self.hasImage:
			pg.draw.rect(self.surface, self.color, self.rect)
		else:
			self.surface.blit(self.image, self.rect)


	def Move(self):
		if self.rect.x + self.rect.w + self.direction[0] * (self.speed * SF) <= WIDTH and self.rect.x + self.direction[0] * (self.speed * SF) >= 0:
			self.rect.x += self.direction[0] * (self.speed * SF)
		self.rect.y += self.direction[1] * (self.speed * SF)

	def Shoot(self):
		if self.numOfbullets - 1 >= 0:
			self.numOfbullets -= 1
			for i in range(self.numberOfshots):
				bullet = Bullet(screen, (((player.rect.x + player.rect.w // 2) - 5) // SF, (player.rect.y // SF) + (i * 10), 5, 5), colBlack, lists=[allBullets])
			
			if self.numOfbullets < self.maxAmountBullets:
				self.StartRefillTimer()	
				self.refilling = True
		numOfbulletsLabel.UpdateText("Bullets: {}".format(self.numOfbullets))

	def StartRefillTimer(self):
		self.currentTime = int(dt.datetime.utcnow().strftime("%S"))
		self.startRefillTime = dt.datetime.utcnow().strftime("%S")
		self.endFillTime = timedelta(minutes=0, seconds=int(self.startRefillTime) + self.bulletRefillRate)

	def UpdateTimers(self):
		self.currentTime = int(dt.datetime.utcnow().strftime("%S"))
		if self.refilling:
			endTime = self.endFillTime.seconds

			if self.currentTime == 0:
				difference = self.bulletRefillRate
			else:
				difference = endTime - self.currentTime
			bulletTimerLabel.UpdateText(str(difference))
			if difference <= 0:
				self.Refill()
				self.refilling = False

		for powerUpData in self.activePowerUps:
			endTime = powerUpData[1].seconds
			if endTime >= 60:
				endTime -= 60

			difference = endTime - self.currentTime
			if difference <= 0:
				self.RestoreDeafualtValues(powerUpData)

	def RestoreDeafualtValues(self, powerUpData):
		try:
			self.activePowerUps.remove(powerUpData)
			originalValue = self.originalData[powerUpData[0]]
			self.__dict__[powerUpData[0]] = originalValue
		except:
			pass

	def Refill(self):
		if self.numOfbullets <= self.data["bullets"]["maxAmount"]:
			self.numOfbullets = self.data["bullets"]["maxAmount"]
		numOfbulletsLabel.UpdateText("Bullets: {}".format(self.numOfbullets))

	def PowerUp(self, name, ability, value, duration):
		if ability in self.__dict__:
			self.__dict__[ability] += value
			if duration > 0:
				startPowerUpTime = dt.datetime.utcnow().strftime("%S")
				endPowerUpTime = timedelta(minutes=0, seconds=int(startPowerUpTime) + duration)
				self.activePowerUps.append((ability, endPowerUpTime))

		numOfbulletsLabel.UpdateText("Bullets: {}".format(self.numOfbullets))
		healthLabel.UpdateText("Health: {}".format(self.health))
		scoreLabel.UpdateText("Score: {}".format(self.score))
		currentPowerUp.UpdateText("Power up: {}".format(name))

	def LevelUp(self):
		self.score = 0
		if self.health < 100:
			self.health = 100
		self.maxAmountBullets *= gameData["level"]
		self.numOfbullets = self.maxAmountBullets

		healthLabel.UpdateText("Health: 100".format(self.health))
		scoreLabel.UpdateText("Score: 0".format(self.score))
		numOfbulletsLabel.UpdateText("Bullets: {}".format(self.numOfbullets))
		bulletTimerLabel.UpdateText(str(self.data["bullets"]["refillRate"]))


class Enemy:
	def __init__(self, surface, rect, color, lists=[allEnemies], data=enemyData):
		self.surface = surface
		self.originalRect = rect
		self.color = color
		self.data = data
		self.lists = lists

		xDir = random.randint(-1, 1)
		while xDir == 0:
			xDir = random.randint(-1, 1)

		self.direction = [xDir, 1]
		self.speed = [self.data["speed"]["x"] * SF, self.data["speed"]["y"] * SF]

		self.Rescale()

		for listToAppend in self.lists:
			listToAppend.append(self)

	def Rescale(self):
		self.rect = pg.Rect(self.originalRect[0] * SF, self.originalRect[1] * SF, self.originalRect[2] * SF, self.originalRect[3] * SF)
		self.pos = [self.rect.x, self.rect.y]

	def Draw(self):
		pg.draw.rect(self.surface, self.color, self.rect)

	def Move(self):
		self.pos[0] += self.direction[0] * self.speed[0]
		self.pos[1] += self.direction[1] * self.speed[1]
		self.rect.x = self.pos[0]
		self.rect.y = self.pos[1]
		if not self.rect.colliderect(collideingRect):
			self.direction[0] = -self.direction[0]

		if self.rect.y + self.rect.h >= 325 * SF:
			self.Destroy(False)

	def Update(self):
		for bullet in allBullets:
			if self.rect.colliderect(bullet.rect):
				bullet.Destroy()
				self.Destroy(True)

	def Destroy(self, positive):
		try:
			for listToAppend in self.lists:
				listToAppend.remove(self)
		except:
			pass

		if positive:
			player.score += player.scoreAmount
			powerUpChance = random.randint(0, max(0, 100-powerUpSpawnChance))
			if powerUpChance == 0:
				powerUp = PowerUp(screen, (self.rect.x // SF, self.rect.y // SF, self.rect.w // SF, self.rect.h // SF))
		else:
			player.health -= player.hurtAmount

		healthLabel.UpdateText("Health: {}".format(player.health))
		scoreLabel.UpdateText("Score: {}".format(player.score))
		numOfEnemiesLeftLabel.UpdateText("Enemies left: {}".format(len(allEnemies)))


class PowerUp:
	def __init__(self, surface, rect, lists=[allPowerUps], data=powerUpData):
		self.surface = surface
		self.originalRect = rect
		self.data = data
		self.lists = lists

		self.direction = [0, 1]
		self.speed = [0, self.data["speed"]]

		self.abilityName = self.data["abilityNames"][random.randint(0, len(self.data["abilityNames"]) - 1)]
		self.attribute = self.data[self.abilityName]["attribute"]
		self.color = self.data[self.abilityName]["color"]
		self.value = self.data[self.abilityName]["value"]
		self.duration = self.data[self.abilityName]["duration"]

		self.Rescale()

		for listToAppend in self.lists:
			listToAppend.append(self)

	def Rescale(self):
		self.rect = pg.Rect(self.originalRect[0] * SF, self.originalRect[1] * SF, self.originalRect[2] * SF, self.originalRect[3] * SF)
		self.pos = [self.rect.x, self.rect.y]

	def Draw(self):
		pg.draw.rect(self.surface, self.color, self.rect)

	def Move(self):
		if self.rect.y >= HEIGHT:
			self.Destroy()

		self.pos[0] += self.direction[0] * self.speed[0]
		self.pos[1] += self.direction[1] * self.speed[1]
		self.rect.x = self.pos[0]
		self.rect.y = self.pos[1]

	def Destroy(self):
		for listToAppend in self.lists:
			listToAppend.remove(self)

	def Update(self):
		if self.rect.colliderect(player.rect):
			player.PowerUp(self.abilityName, self.attribute, self.value, self.duration)
			self.Destroy()


def DrawLoop():
	global gameState
	screen.fill(colDarkGray)

	for label in allLabels:
		if label.gameStateType == gameState:
			label.Draw()

	for slider in allSliders:
		if slider.type == gameState:
			slider.Draw()

	for button in allButtons:
		if button.type == gameState:
			button.Draw()

	if gameState == "game":
		for bullet in allBullets:
			if bullet.rect.y < player.rect.y:
				bullet.Draw()

		player.Draw()

		for enemy in allEnemies:
			enemy.Draw()

		for powerUp in allPowerUps:
			powerUp.Draw()

		pg.draw.line(screen, colLightGray, (0, player.rect.y), (WIDTH, player.rect.y))

	pg.display.update()


def HandleKeyboard(event):
	global gameState
	if gameState != "start menu":
		if event.type == pg.QUIT:
			QuitMenu()
		if event.type == pg.KEYDOWN:
			if event.key == pg.K_ESCAPE:
				QuitMenu()
	
		if gameState == "game":
			if event.type == pg.KEYDOWN:
				if event.key == pg.K_s:
					gameState = "settings"

				if event.key == pg.K_a:
					player.direction[0] = -1

				if event.key == pg.K_d:
					player.direction[0] = 1

	else:
		if event.type == pg.QUIT:
			Quit(False)
		if event.type == pg.KEYDOWN:
			if event.key == pg.K_ESCAPE:
				Quit(False)



	if event.type == pg.KEYUP:
		if event.key == pg.K_a:
			player.direction[0] = 0

		if event.key == pg.K_d:
			player.direction[0] = 0

	if event.type == pg.MOUSEBUTTONDOWN:
		if event.button == 1:
			player.Shoot()


def QuitMenu():
	global gameState
	gameState = "quit menu"
	for button in allButtons:
		if button.type == gameState:
			allButtons.remove(button)

	x, y, w, h = 0, -100, WIDTH // SF, (HEIGHT // SF) + 100

	Label(screen, (x, y, w, h), "quit menu", (colDarkGray, colDarkGray), ("Are you sure you want to quit?", colLightGray, 32, "center-center"), extraText=[("All data will be saved on exit.", (160, -60), "center-center")])

	confirm = HoldButton(screen, ((x + w // 2) - 100 , 240, 200, 50), ("quit menu", "yes"), (colLightGray, colLightGray), ("YES", colDarkGray))
	deny = HoldButton(screen, ((x + w // 2) - 100 , 300, 200, 50), ("quit menu", "no"), (colLightGray, colLightGray), ("NO", colDarkGray))


def Quit(save=True):
	global running
	running = False
	if save:
		Save()


def Save():
	with open(savePath, "w") as file:
		json.dump(gameData, indent=2, fp=file)
		file.close()


def Load(): 
	global gameData, numOfEnemies, gameState
	with open(savePath, "r") as file:
		gameData = json.load(file)
		file.close()

	numOfEnemies = 10 * gameData["level"]
	playerData["bullets"]["numOfbullets"] = int(numOfEnemies * 1.5)
	playerData["bullets"]["maxAmount"] = int(numOfEnemies * 1.5)
	gameState = "game"


def ButtonClick():
	global gameState
	for button in allButtons:
		if button.type == gameState:
			if button.active:
				# quit menu buttons
				if button.action == "yes":
					Quit(False)
				elif button.action == "no":
					gameState = "game"

				# start menu buttons
				if button.action == "new save":
					NewSave()
				if button.action == "load save":
					Load()
				if button.action == "quit":
					Quit()

				# settings buttons
				if button.action == "musicUp":
					ChangeVolume("music", "up")
				if button.action == "musicDown":
					ChangeVolume("music", "down")

				if button.action == "SFXup":
					ChangeVolume("SFX", "up")
				if button.action == "SFXDown":
					ChangeVolume("SFX", "down")

				if button.action == "masterUp":
					ChangeVolume("master", "up")
				if button.action == "masterDown":
					ChangeVolume("master", "down")

				if button.action == "back":
					gameState = "game"


def SliderClick(slider):
	global musicVolume, SFXVolume, masterVolume
	if slider.action == "music":
		print(musicVolume, slider.value / 100)
		if slider.direction == "left":
			musicVolume = slider.value / 100
		if slider.direction == "right":
			musicVolume = slider.value / 100

	if slider.action == "SFX":
		if slider.direction == "left":
			SFXVolume = slider.value / 100
		if slider.direction == "right":
			SFXVolume = slider.value / 100

	if slider.action == "master":
		if slider.direction == "left":
			masterVolume = slider.value / 100
		if slider.direction == "right":
			masterVolume = slider.value / 100


	backgroundMusic.set_volume(musicVolume * masterVolume)


def SettingsMenu():
	title = Label(screen, (40, 20, 560, 60), "settings", (colLightGray, colLightGray), ["Settings", colLightGray, 16, "center-center"], [True, True, False])
	
	musicUp = HoldButton(screen, (300, 100, 20, 20), ("settings", "musicUp"), (colLightGray, colLightGray), ("M Up.", colDarkGray))
	musicSlider = Slider(screen, (65, 100, 235, 20), ("settings", "music"), (colLightGray, colWhite, colLightGray), (" ||| ", colDarkGray, True), (0, 100), drawData=[False])
	musicDown = HoldButton(screen, (45, 100, 20, 20), ("settings", "musicDown"), (colLightGray, colLightGray), ("M Down.", colDarkGray))
	
	SFXup = HoldButton(screen, (580, 100, 20, 20), ("settings", "SFXup"), (colLightGray, colLightGray), ("SFX Up.", colDarkGray))
	SFXSlider = Slider(screen, (345, 100, 235, 20), ("settings", "SFX"), (colLightGray, colWhite, colLightGray), (" ||| ", colDarkGray, True), (0, 100), drawData=[False])
	SFXDown = HoldButton(screen, (325, 100, 20, 20), ("settings", "SFXDown"), (colLightGray, colLightGray), ("SFX Down.", colDarkGray))
	
	masterUp = HoldButton(screen, (580, 140, 20, 20), ("settings", "masterUp"), (colLightGray, colLightGray), ("Master Down.", colDarkGray))
	masterSlider = Slider(screen, (65, 140, 515, 20), ("settings", "master"), (colLightGray, colWhite, colLightGray), (" ||| ", colDarkGray, True), (0, 100), drawData=[False])
	masterDown = HoldButton(screen, (45, 140, 20, 20), ("settings", "masterDown"), (colLightGray, colLightGray), ("Master Down.", colDarkGray))
	
	back = HoldButton(screen, (230, 270, 200, 50), ("settings", "back"), (colLightGray, colLightGray), ("Back.", colDarkGray))
	# add resolution buttons


def StartMenu():
	title = Label(screen, (40, 20, 560, 60), "start menu", (colLightGray, colLightGray), ["Shooter", colLightGray, 16, "center-center"], [True, True, False])
	startNewSave = HoldButton(screen, (230, 110, 200, 50), ("start menu", "new save"), (colLightGray, colLightGray), ("Start new save game.", colDarkGray))
	loadSave = HoldButton(screen, (230, 190, 200, 50), ("start menu", "load save"), (colLightGray, colLightGray), ("Load save game.", colDarkGray))
	exit = HoldButton(screen, (230, 270, 200, 50), ("start menu", "quit"), (colLightGray, colLightGray), ("Quit.", colDarkGray))
	

def ChangeVolume(soundtype, direction, value=0.1):
	global musicVolume, sfxVolume, masterVolume
	if backgroundMusic != None:
		if soundtype == "music":
			if direction == "up":
				if musicVolume + value <= 1.0:
					musicVolume += value
			if direction == "down":
				if musicVolume - value >= 0.0:
					musicVolume -= value

		if soundtype == "SFX":
			if direction == "up":
				if sfxVolume + value <= 1.0:
					sfxVolume += value
			if direction == "down":
				if sfxVolume - value >= 0.0:
					sfxVolume -= value

		if soundtype == "master":
			if direction == "up":
				if masterVolume + value <= 1.0:
					masterVolume += value
			if direction == "down":
				if masterVolume - value >= 0.0:
					masterVolume -= value

		backgroundMusic.set_volume(musicVolume * masterVolume)


def NewSave():
	global gameState
	gameData = {
		"level": 1,
		"totalScore": 0
	}

	bulletData = {
		"speed": 4.5
	}

	playerData = {
		"speed": 3,
		"health": 100,
		"scoreAmount": 10,
		"hurtAmount": 10,
		"bullets": {
			"numOfbullets": int(numOfEnemies * 1.5),
			"maxAmount": int(numOfEnemies * 1.5),
			"refillRate": 5,
			"numberOfshots": 5
		}
	}

	enemyData = {
		"speed": {
			"x": 1.5,
			"y": 0.1
		},
		"drawData": {
			"width": 15,
			"height": 15
		}
	}

	powerUpData = {
		"speed": 4,
		"abilityNames": ["Add health", "Refill bullets", "Increase speed"],
		"Add health": {
			"color": colGreen,
			"attribute": "health",
			"value": 10,
			"duration": 0,
		},
		"Refill bullets": {
			"color": colBlue,
			"attribute": "numOfbullets",
			"value": playerData["bullets"]["maxAmount"],
			"duration": 0,
		},
		"Increase speed": {
			"color": colOrange,
			"attribute": "speed",
			"value": 3 * SF,
			"duration": 5,
		}
	}

	Save()
	gameState = "game"


def CreateGameObjects():
	global healthLabel, scoreLabel, numOfbulletsLabel, bulletTimerLabel, player, currentPowerUp, numOfEnemiesLeftLabel, totalScoreLabel, levelLabel
	
	player = Player(screen, ((WIDTH // 2) // SF, 325, 10, 10), colWhite)
	CreateEnemies()

	healthLabel = Label(screen, (0, (HEIGHT // SF) - 15, 50, 15), "game", (colLightGray, colDarkGray), ("Health: 100", colLightGray, 8, "center-center"), (False, False, False))
	scoreLabel = Label(screen, (55, (HEIGHT // SF) - 15, 50, 15), "game", (colLightGray, colDarkGray), ("Score: {}".format(player.score), colLightGray, 8, "center-center"), (False, False, False))
	numOfbulletsLabel = Label(screen, (110, (HEIGHT // SF) - 15, 50, 15), "game", (colLightGray, colDarkGray), ("Bullets: {}".format(playerData["bullets"]["numOfbullets"]), colLightGray, 8, "center-center"), (False, False, False))
	bulletTimerLabel = Label(screen, (165, (HEIGHT // SF) - 15, 15, 15), "game", (colLightGray, colDarkGray), (str(playerData["bullets"]["refillRate"]), colLightGray, 8, "center-center"), (False, False, False))
	currentPowerUp = Label(screen, (530, (HEIGHT // SF) - 15, 110, 15), "game", (colLightGray, colDarkGray), ("Power up: None", colLightGray, 8, "top-left"), (False, False, False))
	numOfEnemiesLeftLabel = Label(screen, (185, (HEIGHT // SF) - 15, 70, 15), "game", (colLightGray, colDarkGray), ("Enemies left: {}".format(len(allEnemies)), colLightGray, 8, "top-left"), (False, False, False))
	totalScoreLabel = Label(screen, (285, (HEIGHT // SF) - 15, 75, 15), "game", (colLightGray, colDarkGray), ("Total score: {}".format(gameData["totalScore"]), colLightGray, 8, "center-center"), (False, False, False))
	levelLabel = Label(screen, (365, (HEIGHT // SF) - 15, 40, 15), "game", (colLightGray, colDarkGray), ("Level: {}".format(gameData["level"]), colLightGray, 8, "center-center"), (False, False, False))


def CreateEnemies():
	global allBullets
	allBullets = []
	for i in range(numOfEnemies):
		x = random.randint(enemyData["drawData"]["width"] * 2, (WIDTH // SF) - enemyData["drawData"]["width"] * 4)
		y = random.randint(-20, 100)
		for enemy in allEnemies:
			while pg.Rect((x * SF, y * SF, enemyData["drawData"]["width"] * SF, enemyData["drawData"]["height"] * SF)).colliderect(enemy.rect):
				x = random.randint(enemyData["drawData"]["width"] * 2, (WIDTH // SF) - enemyData["drawData"]["width"] * 4)
				y = random.randint(-20, 100)
		enemy = Enemy(screen, (x, y, enemyData["drawData"]["width"], enemyData["drawData"]["height"]), colRed)


def CheckForSaveGame():
	rootDirectory = os.getcwd()
	filesInDirectory = [file for file in listdir(rootDirectory)]
	saveFileName = "saveData.json"
	saveExists = False
	newDirectorys = []

	for file in filesInDirectory:
		if file == saveFileName:
			saveExists = True
		else:
			with open(savePath, "w") as file:
				json.dump(gameData, indent=2, fp=file)
				file.close()

		os.chdir(rootDirectory)


CheckForSaveGame()
StartMenu()
SettingsMenu()
CreateGameObjects()
while running:
	clock.tick(FPS)

	for event in pg.event.get():
		HandleKeyboard(event)

		for button in allButtons:
			button.HandleEvent(event)

		for slider in allSliders:
			slider.HandleEvent(event)

			if slider.active:
				SliderClick(slider)

		if event.type == pg.MOUSEBUTTONDOWN:
			if event.button == 1:
				ButtonClick()

	if gameState == "game":
		for bullet in allBullets:
			bullet.Move()

		player.Move()
		player.UpdateTimers()

		for enemy in allEnemies:
			enemy.Update()
			enemy.Move()

		for powerUp in allPowerUps:
			powerUp.Update()
			powerUp.Move()

		if player.health <= 0:
			Quit()
			print("YOU LOSE")
		

		if len(allEnemies) == 0:
			gameData["level"] += 1
			numOfEnemies = 10 * gameData["level"]
			gameData["totalScore"] += player.score
			player.LevelUp()
			CreateEnemies()
			numOfEnemiesLeftLabel.UpdateText("Enemies left: {}".format(len(allEnemies)))
			totalScoreLabel.UpdateText("Total score: {}".format(gameData["totalScore"]))
			levelLabel.UpdateText("Level: {}".format(gameData["level"]))
			Save()


	DrawLoop()

pg.quit()
