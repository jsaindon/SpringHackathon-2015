import random
import time
import os
import numpy
import moviepy.editor as mpy
from PIL import Image
try:
	import cPickle as pickle
except:
	import pickle

DEBUG = True
IMG_MAPPINGS_FILE_NAME = "mappings"

class Mosaic:
	MOSAIC_IMG_DIR = "/composite_images/"
	MOSAIC_FILE_NAME = "/dynamic_images/mosaic"
	MOSAIC_FILE_EXTENSION = ".bmp"
	
	TIME_STEP = 0.2
	FOREVER_MODE = False
	NUM_STEPS = 5
	REPLACE_INTERVAL = 2

	SEC_PER_LAYER = 1
	#SWITCH_INTERVAL = Mosaic.NUM_STEPS / 5

	def __init__(self, fname=IMG_MAPPINGS_FILE_NAME, imgName=None): #  mappings, imgName, width, length, tile_size):
		with open(fname, 'rb') as f:
			data = pickle.load(f)

		self.mappings = data["mappings"] # key: composite image name, value: 2D array mapping image names

		if imgName:
			self.imgName = imgName
		else:
			# pick random composite image
			while(True):
				try:
					self.imgName = os.getcwd() + Mosaic.MOSAIC_IMG_DIR + random.choice(os.listdir(os.getcwd() + Mosaic.MOSAIC_IMG_DIR))
					self.image = Image.open(self.imgName)
					break
				except:
					print("Not an image, trying another choice.")
		self.imgName = os.path.basename(self.imgName) # strip directory from imgName
		self.width = data["width"]
		self.length = data["length"]
		self.tile_width = data["tile_width"]
		self.tile_length = data["tile_length"]
		self.layers = [] # History of mosaic layers in the form (imgName, tilePicked)

	def pickRandomTile(self):
		rand_tile_x = random.randint(0,self.width) / self.tile_width
		rand_tile_y = random.randint(0,self.length) / self.tile_length

		return (rand_tile_x, rand_tile_y)

	def animateForward(self, chosen_tile):
		# do animation stuff

		# get tile
		if not chosen_tile:
			tile = self.pickRandomTile()
		else:
			tile = chosen_tile

		# save current mosaic key in self.layers
		self.layers.append((self.imgName, tile))

		# get next image info
		self.imgName = self.mappings[self.imgName][tile[0]][tile[1]]
		tile_img_name = os.getcwd() + Mosaic.MOSAIC_IMG_DIR + self.imgName

		# get distances from img to tile
		distances = self.getDistances(tile)

		# replace chosen tile with corresponding mosaics
		tile_image = Image.open(tile_img_name).transform((self.tile_width, self.tile_length), Image.EXTENT, (0, 0, self.width, self.length))
		tile_image = tile_image.convert("RGBA")
		self.image = self.image.convert("RGBA")
		self.image.paste(tile_image, (tile[0] * self.tile_width, tile[1] * self.tile_length))

		if DEBUG:
			self.image.show()	

		curr_tile_width = self.tile_width
		curr_tile_length = self.tile_length
		curr_tile_tl_corner = [tile[0] * curr_tile_width, tile[1] * curr_tile_length]

		# animation
		for i in xrange(1, Mosaic.NUM_STEPS + 1):

			# render image
			self.render(self.image)

			# get proportional distances
			cutDistances = map(lambda dim: dim * i * 1.0 / Mosaic.NUM_STEPS, distances)
			newRectangle = (cutDistances[0], cutDistances[1], 
							self.width - cutDistances[2], self.length - cutDistances[3])

			# adjust distances to account for scaling during transform
			tile_dist_changes = (
				Mosaic.NUM_STEPS*self.width / (1.0 * self.width * (Mosaic.NUM_STEPS - i) + curr_tile_width*i),
				Mosaic.NUM_STEPS*self.length / (1.0 * self.length * (Mosaic.NUM_STEPS - i) + curr_tile_length*i),
				Mosaic.NUM_STEPS*self.width / (1.0 * self.width * (Mosaic.NUM_STEPS - i) + curr_tile_width*i),
				Mosaic.NUM_STEPS*self.length / (1.0 * self.length * (Mosaic.NUM_STEPS - i) + curr_tile_length*i)
			)
			curr_tile_tl_corner = [curr_tile_tl_corner[0] + tile_dist_changes[0],
								   curr_tile_tl_corner[1] + tile_dist_changes[1]]
			distances = (
				distances[0] - ((curr_tile_width/(1.0*self.width))*(self.width-distances[0]-(curr_tile_width/2)) * (tile_dist_changes[0] - 1)),
				distances[1] - ((curr_tile_length/(1.0*self.length))*(self.length-distances[1]-(curr_tile_length/2)) * (tile_dist_changes[1] - 1)),
				distances[2] - ((curr_tile_width/(1.0*self.width))*(self.width-distances[2]-(curr_tile_width/2)) * (tile_dist_changes[2] - 1)),
				distances[3] - ((curr_tile_length/(1.0*self.length))*(self.length-distances[3]-(curr_tile_length/2)) * (tile_dist_changes[3] - 1))
			)

			# crop image
			self.image = self.image.transform((self.width, self.length), Image.EXTENT, newRectangle)

			#time
			#time.sleep(Mosaic.TIME_STEP)

			if DEBUG:
				self.image.show()

			# every NUM_TIMES timesteps, replace visible tiles with corresponding mosaics
			# if (i % Mosaic.REPLACE_INTERVAL == 0):
			# 	newImage = Image.open(tile_img_name)
			# 	newImage.transform((curr_tile_width, curr_tile_length), Image.EXTENT, newImage.getbbox())
			# 	self.image.paste(newImage, (int(curr_tile_tl_corner[0]), int(curr_tile_tl_corner[1])))

		# load overall new mosaic
		self.image = Image.open(os.getcwd() + Mosaic.MOSAIC_IMG_DIR + self.imgName)

		if DEBUG:
			self.image.show()
		self.render(self.image)

	def animateBackward(self):
		# get parent layer info
		(parent_image_name,tile_position)=self.layers.pop()

		# load parent image
		parent_image = Image.open(os.getcwd() + Mosaic.MOSAIC_IMG_DIR + parent_image_name)

		for i in xrange(1, Mosaic.NUM_STEPS + 1):

			# Adjust tile size
			self.image = self.image.transform( (self.width - i * ((self.width - self.tile_width) / Mosaic.NUM_STEPS), 
								   self.length - i * ((self.length - self.tile_length) / Mosaic.NUM_STEPS) ), 
								  Image.EXTENT, self.image.getbbox())

			# paste tile onto foreground
			newImage = parent_image.copy()
			newImage.paste(self.image, (i * tile_position[0] * self.tile_width / Mosaic.NUM_STEPS,
										i * tile_position[1] * self.tile_length / Mosaic.NUM_STEPS))
			
			if DEBUG:
				newImage.show()

			# sleep for a bit
			time.sleep(Mosaic.TIME_STEP)

			# render intermediate image
			self.render(newImage)

		# save and render file image
		self.image = parent_image
		self.imgName = parent_image_name
		self.render(self.image)

	def getDistances(self, tile):
		leftX = tile[0] * self.tile_width
		rightX = self.width - (leftX + self.tile_width)
		upY = tile[1] * self.tile_length
		downY = self.length - (upY + self.tile_length)

		return (leftX, upY, rightX, downY)

	def render(self,img):
		# save img, front end will update img source on source chance
		img.save(os.getcwd() + Mosaic.MOSAIC_FILE_NAME + Mosaic.MOSAIC_FILE_EXTENSION)

	@staticmethod
	def test_animation():
		image_fname = "/composite_images/outdoor_free_3d_scene_by_djeric_composite.JPEG"
		mosaic = Mosaic(IMG_MAPPINGS_FILE_NAME, image_fname)
		mosaic.animateForward(mosaic.pickRandomTile())

		print("Layers:", mosaic.layers)

	@staticmethod
	def main():
		mosaic = Mosaic()
		mosaic.animateForward(mosaic.pickRandomTile())
		#mosaic.animateBackward()

def createVideo(time):
	if (time % Mosaic.SEC_PER_LAYER != 0):
		adjustment = (1-(time % Mosaic.SEC_PER_LAYER)*0.5/Mosaic.SEC_PER_LAYER)
		horizMax = mosaic.width * adjustment
		horizMin = mosaic.width - horizMax
		vertMax = mosaic.length * adjustment
		vertMin = mosaic.length - vertMax
		newRectangle = ( horizMin, vertMin, horizMax, vertMax )
		img = mosaic.image.copy().transform((mosaic.width, mosaic.length), Image.EXTENT, newRectangle)
		return numpy.array(img.getdata()).reshape(img.size[0], img.size[1], 3)
	else:
		# add center tile
		tile = ((mosaic.width / 2) / mosaic.tile_width, (mosaic.length / 2) / mosaic.tile_length)
		mosaic.layers.append(tile)

		while(True):
			try:
				mosaic.imgName = random.choice(os.listdir(os.getcwd() + Mosaic.MOSAIC_IMG_DIR)) #mosaic.mappings[mosaic.imgName][tile[0]][tile[1]]
				img_name = os.getcwd() + Mosaic.MOSAIC_IMG_DIR + mosaic.imgName
				mosaic.image = Image.open(img_name)
				break
			except:
					print("Not an image, trying another choice.")
		img = mosaic.image.copy()
		return numpy.array(img.getdata()).reshape(img.size[0], img.size[1], 3)

mosaic = Mosaic()

if __name__ == "__main__":
	duration = 8
	clip = mpy.VideoClip( createVideo, duration=duration)
	clip.write_gif("recursive_img_variable.gif", fps = 30)