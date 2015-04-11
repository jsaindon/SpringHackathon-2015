import random
import time
import os
import Image from PIL

DEBUG = True

class Mosaic:
	MOSAIC_FILE_NAME = "images/mosaic"
	MOSAIC_FILE_EXTENSION = "bmp"
	
	TIME_STEP = 0.2
	FOREVER_MODE = False
	NUM_STEPS = 5
	#SWITCH_INTERVAL = Mosaic.NUM_STEPS / 5

	def __init__(self, mappings, imgName, width, length, tile_size):
		self.mappings = mappings # key: composite image name, value: 2D array mapping image names
		self.imgName = imgName
		self.image = Image.open(imgName)
		self.width = width
		self.length = length
		self.tile_width = tile_size[0]
		self.tile_length = tile_size[1]
		self.scale = 1.0
		self.layers = [] # History of mosaic layers in the form (imgName, tilePicked)

	def pickRandomTile(self):
		rand_tile_x = random.randint(self.x) / self.tile_width
		rand_tile_x = random.randint(self.y) / self.tile_length

		return (rand_tile_x, rand_tile_y)

	def animateForward(self, chosen_tile):
		# do animation stuff

		# get tile
		if not chosen_tile:
			tile = self.pickRandomTile()
		else:
			tile = chosen_tile

		tile_img_name = self.mappings[this.imgName][tile[0]][tile[1]]

		# save current mosaic key in self.layers
		self.layers.append((self.imgName, tile))

		# get distances from img to tile
		distances = self.getDistances(tile)

		# replace chosen tile with corresponding mosaics
		tile_image = Image.open(tile_img_name).transform((self.tile_width, self.tile_length), Image.EXTENT, (0, 0, self.width, self.length))
		tile_image = tile_image.convert("RGBA")
		self.image = self.image.convert("RGBA")
		self.image.paste(tile_image, (tile[0] * self.tile_width, tile[1] * self.tile_length))

		if DEBUG:
			self.image.show()	

		# animation
		for i in xrange(Mosaic.NUM_STEPS):

			# render image
			self.render(self.image)

			# get proportional distances
			cutDistances = map(lambda dim: dim * 1.0 / Mosaic.NUM_STEPS, distances)
			newRectangle = (cutDistances[0], cutDistances[1], 
							self.width - cutDistances[2], self.length - cutDistances[3])

			# adjust distances to account for scaling during transform
			distances = map(lambda x: distances[x]*distances[x]/(distances[x]-cutDistances[x]), range(len(distances)))

			# crop image
			self.image = self.image.transform((self.width, self.length), Image.EXTENT, newRectangle)

			#time
			time.sleep(Mosaic.TIME_STEP)

			if DEBUG:
				self.image.show()

			# every NUM_TIMES timesteps, replace visible tiles with corresponding mosaics
			# if (i % Mosaic.SWITCH_INTERVAL == 0):
			# 	tile_size = stuff
			# 	newImage = Image.open(tile_img_name).transform(size=stuff)

		# load overall new mosaic
		self.render(self.image)

	def animateBackward(self):
		# get parent layer info
		(parent_image_name,tile_position)=self.layers.pop()

		# load parent image
		parent_image = Image.open(parent_image_name)

		for i in xrange(1, Mosaic.NUM_STEPS + 1):

			# Adjust tile size
			self.image.transform( (self.width - i * ((self.width - self.tile_width) / (1.0 * Mosaic.NUM_STEPS)), 
								   self.length - i * ((self.length - self.tile_length) / (1.0 * Mosaic.NUM_STEPS)) ), 
								  Image.EXTENT, self.image.getbbox())

			# paste tile onto foreground
			newImage = parent_image.copy()
			newImage.paste(self.image, (i * tile_position[0] * self.tile_width * 1.0 / Mosaic.NUM_STEPS,
										i * tile_position[1] * self.tile_length * 1.0 / Mosaic.NUM_STEPS))
			
			if DEBUG:
				newImage.show()

			# sleep for a bit
			time.sleep(Mosaic.TIME_STEP)

			# render intermediate image
			self.render(newImage)

		# save and render file image
		self.image = parent_image
		self.render(self.image)

	def getDistances(self, tile):
		leftX = tile[0] * self.tile_width
		rightX = self.width - (leftX + self.tile_width)
		upY = tile[1] * self.tile_length
		downY = self.length - (upY + self.tile_length)

		return (leftX, upperY, rightX, lowerY)

	def render(img):
		# save img, front end will update img source on source chance
		img.save(os.getcwd() + Mosaic.MOSAIC_FILE_NAME, Mosaic.MOSAIC_FILE_EXTENSION)
