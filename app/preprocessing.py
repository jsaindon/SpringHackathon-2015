from PIL import Image
import os
import random 
IMAGE_WIDTH = 60
IMAGE_HEIGHT = 60
TILE_WIDTH = 15
TILE_HEIGHT = 15


def findAvgPixels(startX, startY, endX, endY, image):
    sumRed = 0
    sumGreen = 0
    sumBlue = 0
    #print startX,startY, endX, endY
    totPixels = (endX - startX)*(endY - startY)
    for x in range(startX, endX):
        for y in range(startY, endY):
        	#print x,y
        	r, g, b = image.getpixel((x,y))
        	sumRed += r
        	sumGreen += g 
        	sumBlue += b
    avgRed = sumRed/totPixels
    avgGreen = sumGreen/totPixels
    avgBlue = sumBlue/totPixels
    return (avgRed,avgGreen,avgBlue)
    
def mosaicTileRGB(image):
    numWidthTiles = IMAGE_WIDTH/TILE_WIDTH
    numHeightTiles = IMAGE_HEIGHT/TILE_HEIGHT
    mosaicTiles = []
    for y in range(numHeightTiles):
        row = []
        for x in range(numWidthTiles):
            tile = findAvgPixels(x*TILE_WIDTH, y*TILE_HEIGHT, (x+1)*TILE_WIDTH, (y+1)*TILE_HEIGHT, image)
            row.append(tile)
        mosaicTiles.append(row)
    return mosaicTiles

def pixelDifference((r1, g1, b1), (r2, g2, b2)):
    difference = (pow(r1 - r2, 2) + pow(g1 - g2, 2) + pow(b1 - b2, 2))
    return difference

def loadImages():
	"""	returns a list of images
	"""
	imageList = []
	#imPath = os.path.join(scriptDir, "/img")
	imPath = os.getcwd() + "/img/" # get absolute path
	listing = os.listdir(imPath)     # get file names
	
	for imName in listing:
		image = Image.open(imPath + imName)	# open images
		image = image.convert("RGB")
		imageList.append((image,imName))
	
	return imageList

def findImage(name,imageList):
	for image,imName in imageList:
		if name == imName:
			return image

def getMosaicData():
	"""gets the iamge's images that make up its mosaic """
	imagePixelDict = {}	# dictionary mapping each image to its average pixel value
	mosaicDict = {}	# dictionary mapping each image to its mosaic
	compositeMosaicDict = {}	# dictionary mapping each composite image to its mosaic

	imageList = loadImages()
	
	for image, imName in imageList:
		image.thumbnail((IMAGE_WIDTH,IMAGE_HEIGHT))	
		#print image.getbbox()
		imagePixelDict[imName] = findAvgPixels(0, 0, IMAGE_WIDTH,IMAGE_HEIGHT,image) 	#fill in pixelDict
	
	for image, imName in imageList:
		tileArray = mosaicTileRGB(image)	# get the average pixel data for all tiles
		for y in range(len(tileArray)):		# number of rows
			for x in range(len(tileArray[0])):
				closestImageName = None				# go through all images to find the one with most similar pixels
				closestDifference = 1000000
				for imName2 in imagePixelDict.keys():
					#print tileArray[y][x]
					#print imagePixelDict[imName]
					if pixelDifference(tileArray[y][x],imagePixelDict[imName2]) < closestDifference:
						closestImageName = imName2
						closestDifference = pixelDifference(tileArray[y][x],imagePixelDict[imName2])
				tileArray[y][x] = closestImageName	#change tileArray to be made of images rather than pixels
		mosaicDict[imName] = tileArray

	for image,imName in imageList:
		tileArray = mosaicDict[imName]
		print imName + "first"
		compositeImage = Image.new('RGBA',(IMAGE_WIDTH,IMAGE_HEIGHT))
		numWidthTiles = IMAGE_WIDTH/TILE_WIDTH
		numHeightTiles = IMAGE_HEIGHT/TILE_HEIGHT
		for tileY in range(numHeightTiles):
			print imName + "second"
			for tileX in range(numWidthTiles):
				littleImage = findImage(tileArray[tileY][tileX],imageList)
				littleImage.thumbnail((TILE_WIDTH,TILE_HEIGHT))
				for littleY in range(TILE_HEIGHT):
					for littleX in range(TILE_WIDTH):
						pixelColor = littleImage.getpixel((littleX,littleY))
						compositeImage.putpixel((TILE_WIDTH* tileX+littleX,TILE_HEIGHT* tileY + littleY),pixelColor)
		image.convert("RGBA")
		blendedImage = Image.blend(compositeImage,image,.5)
		blendedImage.save(imName.split(".")[0]+"_composite.JPEG","JPEG")
		print imName


		# process image to become composite
		#save as imName + "composite"
	return mosaicDict


getMosaicData()