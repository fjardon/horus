#!/usr/bin/python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------#
#                                                                       #
# This file is part of the Horus Project                                #
#                                                                       #
# Copyright (C) 2014 Mundo Reader S.L.                                  #
#                                                                       #
# Date: March 2014                                                      #
# Author: Jesús Arroyo Torrens <jesus.arroyo@bq.com>                    #
#                                                                       #
# This program is free software: you can redistribute it and/or modify  #
# it under the terms of the GNU General Public License as published by  #
# the Free Software Foundation, either version 3 of the License, or     #
# (at your option) any later version.                                   #
#                                                                       #
# This program is distributed in the hope that it will be useful,       #
# but WITHOUT ANY WARRANTY; without even the implied warranty of        #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the          #
# GNU General Public License for more details.                          #
#                                                                       #
# You should have received a copy of the GNU General Public License     #
# along with this program. If not, see <http://www.gnu.org/licenses/>.  #
#                                                                       #
#-----------------------------------------------------------------------#

__author__ = "Jesús Arroyo Torrens <jesus.arroyo@bq.com>"
__license__ = "GNU General Public License v3 http://www.gnu.org/licenses/gpl.html"

import cv2
import math
import numpy as np

class Core:
	""" """
	def __init__(self):
		""" """
		self.points = None
		self.colors = None
		
		self.imgRaw  = None
		self.imgLas  = None
		self.imgDiff = None
		self.imgBin  = None
		self.imgLine = None

		self.points = None
		self.colors = None

	def initialize(self, imgType='raw',
						 blurEnable=True,
						 blurValue=4,
						 openEnable=True,
						 openValue=4,
						 colorMin=np.array([0, 180, 30],np.uint8),
						 colorMax=np.array([180, 250, 140],np.uint8),
						 useCompact=True,
						 rhoMin=-100,
						 rhoMax=100,
						 hMin=0,
						 hMax=200,
						 zOffset=0,
						 degrees=0.45,
						 width=600,
						 height=800,
						 alpha=60.0,
						 calibrationMatrix=None,
						 translationVector=None,
						 useLeftLaser=True):

		#-- Image type parameters
		self.imgType = imgType

		#-- Image Processing Parameters
		self.blurEnable = blurEnable
		self.blurValue = blurValue

		self.openEnable = openEnable
		self.openValue = openValue

		self.colorMin = colorMin
		self.colorMax = colorMax

		#-- Point Cloud Parameters
		self.modeCW = True

		self.useCompact = useCompact

		self.rhoMin = rhoMin
		self.rhoMax = rhoMax
		self.hMin = hMin
		self.hMax = hMax

		self.zOffset = zOffset

		self.degrees = degrees

		self.setResolution(width, height)

		#-- Calibration parameters
		if calibrationMatrix is not None:
			self.fx = calibrationMatrix[0][0]
			self.fy = calibrationMatrix[1][1]
			self.cx = calibrationMatrix[0][2]
			self.cy = calibrationMatrix[1][2]

		if translationVector is not None:
			self.xo = translationVector[0]
			self.ho = translationVector[1]
			self.zs = translationVector[2]

		self.xp = self.fx * self.xo / self.zs

		if not useLeftLaser:
			self.xp *= -1

		#-- Constant Parameters initialization
		self.rad = math.pi / 180.0

		self.alpha = alpha
		
		alpha = self.alpha * self.rad
		
		A = self.zs / math.sin(alpha)
		B = self.fx / math.tan(alpha)
		
		self.theta = 0

		self.W = np.ones((self.height,self.width))*np.linspace(0,self.width-1,self.width)
		
		u = self.W-self.cx-self.xp
		self.M_rho = A*u/(u+B)
		
		v = self.cy-np.linspace(0,self.height-1,self.height)
		self.M_z = self.ho + (self.zs-self.M_rho*math.sin(alpha))*(np.ones((self.width,self.height))*v).T/self.fy

		if not useLeftLaser:
			self.M_rho = np.fliplr(self.M_rho)
			self.M_z = np.fliplr(self.M_z)

	def setResolution(self, width, height):
		self.width = width
		self.height = height

	def setBlur(self, enable, value):
		self.blurEnable = enable
		self.blurValue = value

	def setOpen(self, enable, value):
		self.openEnable = enable
		self.openValue = value

	def setHSVRange(self, minH, minS, minV, maxH, maxS, maxV):
		self.colorMin = np.array([minH,minS,minV],np.uint8)
		self.colorMax = np.array([maxH,maxS,maxV],np.uint8)

	def setUseCompactAlgorithm(self, useCompact):
		self.useCompact = useCompact

	def setRangeFilter(self, rhoMin, rhoMax, hMin, hMax):
		self.rhoMin = rhoMin
		self.rhoMax = rhoMax
		self.hMin = hMin
		self.hMax = hMax

	def setZOffset(self, zOffset):
		self.zOffset = zOffset

	def setDegrees(self, degrees):
		self.degrees = degrees

	def getImage(self):
		""" """
		return { 'raw' : self.imgRaw,
				 'las' : self.imgLas,
				 'diff' : self.imgDiff,
				 'bin' : self.imgBin,
				 'line' : self.imgLine
				}[self.imgType]

	def setImageType(self, imgType):
		""" """
		self.imgType = imgType

	def getDiffImage(self, img1, img2):
		""" """
		return cv2.absdiff(img1, img2)

	def imageProcessing(self, image):
		""" """
		#-- Image Processing
		if self.blurEnable:
			image = cv2.blur(image,(self.blurValue,self.blurValue))

		if self.openEnable:
			kernel = cv2.getStructuringElement(cv2.MORPH_RECT,(self.openValue,self.openValue))
			image = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)

		#image = cv2.bitwise_not(image) # TODO: remove

		imageHSV = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)

		return cv2.inRange(imageHSV, self.colorMin, self.colorMax)

	def pointCloudGeneration(self, imageDiff, imageRaw, src):
		""" """
		#-- Point Cloud Generation
		s = src.sum(1)
		v = np.nonzero(s)[0]
		if self.useCompact:
			i = src.argmax(1)
			l = ((i + (s/255-1) / 2)[v]).T.astype(int)
		else:
			w = (self.W * src).sum(1)
			l = (w[v] / s[v].T).astype(int)

		#-- Obtaining parameters
		rho = self.M_rho[v,l]
		thetaR = self.theta * self.rad
		x = rho * math.cos(thetaR)
		y = rho * math.sin(thetaR)
		z = self.M_z[v,l] + self.zOffset
		points = np.concatenate((x,y,z)).reshape(3,z.size).T
		colors = np.copy(imageRaw[v,l])

		return points, colors, rho, z

	def pointCloudFilter(self, points, colors, rho, z):
		""" """
		#-- Point Cloud Filter
		idx = np.where((z >= self.hMin) &
					   (z <= self.hMax) &
					   (rho >= self.rhoMin) &
					   (rho <= self.rhoMax))[0]

		return points[idx], colors[idx]

	def getPointCloud(self, imageRaw, imageLas):
		""" """
 		#-- Update Raw, Laser and Diff images
		self.imgRaw = imageRaw
		self.imgLas = imageLas
		self.imgDiff = self.getDiffImage(imageRaw, imageLas)

		src = self.imageProcessing(self.imgDiff)

		temp = np.zeros_like(self.imgDiff)
		temp[:,:,0] = src
		temp[:,:,1] = src
		temp[:,:,2] = src
		self.imgBin = temp

		points, colors, rho, z = self.pointCloudGeneration(self.imgDiff, imageRaw, src)

		if points != None and colors != None:
			points, colors = self.pointCloudFilter(points, colors, rho, z)

		if points != None and colors != None:
			if self.points == None and self.colors == None:
				self.points = points
				self.colors = colors
			else:
				self.points = np.concatenate((self.points, points))
				self.colors = np.concatenate((self.colors, colors))

 		self.theta += self.degrees

		return points, colors