#!/usr/bin/python
# -*- coding: utf8 -*-

from config import *
if CONFIG_FULLSCREEN:
	fullscreen = "#t"
else:
	fullscreen = "#f"
	
from pandac.PandaModules import *

loadPrcFileData("setup", """sync-video 0
show-frame-rate-meter #t
#win-size 800 600
#win-size 1024 768
#win-size 1280 960
#win-size 1280 1024
win-size %s %s
win-fixed-size 1
#yield-timeslice 0 
#client-sleep 0 
#multi-sleep 0
basic-shaders-only #f
fullscreen %s
#audio-library-name null
""" % (CONFIG_W, CONFIG_H, fullscreen))


import direct.directbase.DirectStart
from direct.showbase.DirectObject import DirectObject
from direct.task import Task
from direct.interval.IntervalGlobal import *
from direct.gui.OnscreenText import OnscreenText
from direct.filter.CommonFilters import CommonFilters
from direct.fsm.FSM import FSM

import sys, random
import cPickle as pickle

from camHandler import CamHandler
from pathFind import *

from skyBox import SkyBox
from lightManager import LightManager

from mouseCursor import *

from gui import *
from mapObject import *
from dialog import *


class Clicker:
	def __init__(self):
		"""
		This class is used to handle clicks on the collision / pathfinding grid
		"""
		self.plane = Plane(Vec3(0, 0, 1), Point3(0, 0, 0))
		self.picker = CollisionTraverser()
		self.pq     = CollisionHandlerQueue()
		self.pickerNode = CollisionNode('mouseRay')
		self.pickerNP = camera.attachNewNode(self.pickerNode)
		self.pickerNode.setFromCollideMask(BitMask32.bit(1))
		self.pickerRay = CollisionRay()
		self.pickerNode.addSolid(self.pickerRay)
		self.picker.addCollider(self.pickerNP, self.pq)
		self.picker.showCollisions(render)
		
	def getMouseObject(self, np=render):
		if base.mouseWatcherNode.hasMouse():
			mpos = base.mouseWatcherNode.getMouse()
			
			self.pickerRay.setFromLens(base.camNode, mpos.getX(), mpos.getY())
			self.picker.traverse(np)
			if self.pq.getNumEntries() > 0:
				self.pq.sortEntries()
				#print "y'a eu %s collisions!!!" % (self.pq.getNumEntries())
				res = self.pq.getEntry(0)
				#print "Entry = %s" % (res)
				#print dir(res)
				return res
			#else:
			#	print "y'a rien eu..."
		return None
		
	def getMouseTilePos(self, mpos=None):
		if mpos is None:
			if base.mouseWatcherNode.hasMouse():
				mpos = base.mouseWatcherNode.getMouse()
			else:
				return None
			
		pos3d = Point3()
		nearPoint = Point3()
		farPoint = Point3()
		base.camLens.extrude(mpos, nearPoint, farPoint)
		if self.plane.intersectsLine(pos3d,
				render.getRelativePoint(camera, nearPoint),
				render.getRelativePoint(camera, farPoint)):
			
			x = pos3d.getX()
			y = pos3d.getY()
			return int(x), int(y)
		return None

	def getMousePos(self, mpos=None):
		if mpos is None:
			if base.mouseWatcherNode.hasMouse():
				mpos = base.mouseWatcherNode.getMouse()
			else:
				return None
			
		pos3d = Point3()
		nearPoint = Point3()
		farPoint = Point3()
		base.camLens.extrude(mpos, nearPoint, farPoint)
		if self.plane.intersectsLine(pos3d,
				render.getRelativePoint(camera, nearPoint),
				render.getRelativePoint(camera, farPoint)):
			
			x = pos3d.getX()
			y = pos3d.getY()
			return x, y
		return None

		
		
def makeFloor(nbCases, scalex, scaley, texpath):
	cm = CardMaker('card')
	cm.setUvRange(Point2(scalex/nbCases,scaley/nbCases), Point2(0,0))
	cm.setHasNormals(True)
	#card = render.attachNewNode(cm2.generate())
	card = NodePath(cm.generate())
	img = loader.loadTexture(texpath)
	img.setWrapU(Texture.WMRepeat)
	img.setWrapV(Texture.WMRepeat)
	
	card.setTexture(img)
	card.setScale(scalex,1,scaley)
	card.setPos(0,0,0.0)
	card.setHpr(0,-90,0)
	#card.setTwoSided(True)
	#card.setTransparency(TransparencyAttrib.MAlpha)
	return card
	
def makeWall(scalex, scaley, scaleTex):
	cm = CardMaker('card')
	cm.setUvRange((scalex/scaleTex,0), (0,scaley/scaleTex))
	cm.setHasNormals(True)
	card = NodePath(cm.generate())
	img = loader.loadTexture("img/textures/oldstone4.jpg")
	card.setTexture(img)
	card.setScale(scalex,1,scaley)
	#card.setHpr(0,0,0)
	card.setTwoSided(True)
	card.setTransparency(TransparencyAttrib.MAlpha)
	return card

class MapWall:
	def __init__(self, x, y,z=0):
		self.walls = []
		
		height = 6.0
		texScale = 5.0
		
		wall1 = makeWall(x, height, texScale)
		wall1.reparentTo(render)
		wall1.setPos(0,y,z)
		self.walls.append(wall1)
		
		wall1 = makeWall(x, height, texScale)
		wall1.reparentTo(render)
		wall1.setPos(x,0,z)
		wall1.setHpr(180,0,0)
		self.walls.append(wall1)
		
		wall1 = makeWall(y, height, texScale)
		wall1.reparentTo(render)
		wall1.setPos(0,0,z)
		wall1.setHpr(90,0,0)
		self.walls.append(wall1)
		
		wall1 = makeWall(y, height, texScale)
		wall1.reparentTo(render)
		wall1.setPos(x,y,z)
		wall1.setHpr(-90,0,0)
		self.walls.append(wall1)
		
	def destroy(self):
		for wall in self.walls:
			wall.remove()
	
		
#-----------------------------------------------------------------------
# CollisionGrid
#-----------------------------------------------------------------------
class CollisionGrid:
	def __init__(self, x=50, y=30, name=None, texPath="img/textures/ice01.jpg", geoMipPath = None):
		self.name = name
		
		self.x = x
		self.y = y
		self.texPath = texPath
		self.geoMipPath = geoMipPath
		
		self.data = [] # [[1,1,1,1,0,1,0,0,...], [1,0,0,...]... ]
		for y in range(self.y):
			tmp = []
			for x in range(self.x):
				tmp.append(0)
			self.data.append(tmp)
				
		
		self.node = GeomNode("tiledMesh")
		self.gvd = GeomVertexData('name', GeomVertexFormat.getV3n3c4t2(), Geom.UHStatic)
		self.geom = Geom(self.gvd)
		self.prim = GeomTriangles(Geom.UHStatic)
		
		self.update()
		
		i = 0
		for x in range(self.x * self.y):
			self.prim.addVertices(i, i + 3, i + 2)
			self.prim.addVertices(i, i + 2, i + 1)
			i += 4
		
		self.prim.closePrimitive()
		self.geom.addPrimitive(self.prim)
		self.node.addGeom(self.geom)
		
		self.np = NodePath(self.node)
		self.np.reparentTo(render)
		#self.np.setTwoSided(True)
		#self.np.setTransparency(True)
		if self.texPath is not None:
			self.tex = loader.loadTexture(self.texPath)
		self.colTex = loader.loadTexture("img/textures/collision.png")
		self.np.setTexture(self.colTex)
		#self.np.setColor(0,0,1.0,0.1)
		self.np.setTransparency(True)
		
		self.hasGeoMip = False
		self.terrain = None
		self.terrainNP = None
		self.terrainScale = 0
		
		if self.geoMipPath is not None:
			self.ground = None
			self.initGeoMip()
			
		else:
			
			self.ground = makeFloor(8, self.x, self.y, self.texPath)
			self.ground.reparentTo(render)
			
	def initGeoMip(self):
		if self.ground:
			self.ground.remove()
			
		if self.terrainNP:
			self.terrainNP.remove()
			
		self.hasGeoMip = True
		self.terrain = GeoMipTerrain("ground")
		self.terrain.setHeightfield(self.geoMipPath)
		#self.terrain.setMinLevel(2)
		#self.terrain.setBruteforce(True)
		self.terrainScale = 5.0
		self.terrainImgSize = 65.0
		self.terrainNP = self.terrain.getRoot()
		self.terrainNP.reparentTo(render)
		self.terrainNP.setScale(self.x/self.terrainImgSize,self.y/self.terrainImgSize,self.terrainScale)
		#self.terrainNP.setPos(0,0,-self.terrainScale)
		self.terrain.generate()
		self.terrainNP.setTexture(loader.loadTexture(self.texPath))
		self.terrainNP.setTexScale(TextureStage.getDefault(),self.terrainImgSize/10,self.terrainImgSize/10)
		self.terrainNP.flattenStrong()
		#self.terrainNP.setCollideMask(BitMask32(1))
		
	def removeGeoMip(self):
		if self.terrainNP:
			self.terrainNP.remove()
			self.hasGeoMip = False
			self.terrain = None
			self.terrainNP = None
			self.terrainScale = 0
			self.ground = makeFloor(8, self.x, self.y, self.texPath)
			self.ground.reparentTo(render)
			self.update()
		
	def addGeoMip(self, geomipPath, texPath="img/textures/ice01.jpg", imgSize = 65.0, scale = 5.0):
		if self.terrainNP:
			self.terrainNP.remove()
		if self.ground:
			self.ground.remove()
		
		self.geoMipPath = geomipPath
		self.texPath = texPath
		
		self.hasGeoMip = True
		self.terrain = GeoMipTerrain("ground")
		self.terrain.setHeightfield(self.geoMipPath)
		#self.terrain.setMinLevel(2)
		#self.terrain.setBruteforce(True)
		self.terrainScale = scale
		self.terrainImgSize = imgSize
		self.terrainNP = self.terrain.getRoot()
		self.terrainNP.reparentTo(render)
		self.terrainNP.setScale(self.x/self.terrainImgSize,self.y/self.terrainImgSize,self.terrainScale)
		#self.terrainNP.setPos(0,0,-self.terrainScale)
		self.terrain.generate()
		self.terrainNP.setTexture(loader.loadTexture(self.texPath))
		self.terrainNP.setTexScale(TextureStage.getDefault(),self.terrainImgSize/10,self.terrainImgSize/10)
		self.terrainNP.flattenStrong()
		
	def collisionHide(self):
		self.np.hide()
		
	def collisionShow(self):
		self.np.show()
		
	def getTileHeight(self, x, y):
		if not self.hasGeoMip:
			return 0
		if not (0<=x<self.x): return 0 #- self.terrainScale
		if not (0<=y<self.y): return 0 #- self.terrainScale
		
		xPx = int(float(x)/self.x*self.terrainImgSize)
		yPx = int(float(y)/self.y*self.terrainImgSize)
		height = self.terrain.getElevation(xPx, yPx) * self.terrainScale# - self.terrainScale
		#print "Terrain height in %s / %s : %s" % (x, y, height)
		return height
		
	def update(self):
		self.vertex = GeomVertexWriter(self.gvd, 'vertex')
		self.texcoord = GeomVertexWriter(self.gvd, 'texcoord')
		self.color = GeomVertexWriter(self.gvd, 'color')
		self.normal = GeomVertexWriter(self.gvd, 'normal')
		
		i = 0
		for y in range(self.y):
			for x in range(self.x):
				if self.data[y][x] == 1:
					self.addWallTile(x, y)
				else:
					self.addEmptyTile(x, y)
				i += 4
			
	def rebuild(self):
		# Needed to update the map after it has been resized
		if self.np:
			self.np.remove()
		if self.terrainNP:
			self.terrainNP.remove()
		self.y = len(self.data)
		self.x = len(self.data[0])
		
		self.node = GeomNode("tiledMesh")
		self.gvd = GeomVertexData('name', GeomVertexFormat.getV3n3c4t2(), Geom.UHStatic)
		self.geom = Geom(self.gvd)
		self.prim = GeomTriangles(Geom.UHStatic)
		
		self.update()
		
		i = 0
		for x in range(self.x * self.y):
			#self.prim.addVertices(i, i + 3, i + 2)
			#self.prim.addVertices(i, i + 2, i + 1)
			self.prim.addVertices(i, i + 2, i + 1)
			self.prim.addVertices(i, i + 3, i + 2)
			i += 4
		
		self.prim.closePrimitive()
		self.geom.addPrimitive(self.prim)
		self.node.addGeom(self.geom)
		
		self.np = NodePath(self.node)
		self.np.reparentTo(render)
		#self.np.setTwoSided(True)
		self.np.setTexture(self.colTex)
		#self.np.setColor(0,0,1.0,0.1)
		self.np.setTransparency(True)
		
		if self.hasGeoMip:
			self.initGeoMip()
		
		
	def addWallTile(self, x, y):
		
		norm, norm2 = random.random()/2.0, random.random()/2.0
		#z = 0
		z1 = self.getTileHeight(x, y) + 0.01
		z2 = self.getTileHeight(x, y+1) + 0.01
		z3 = self.getTileHeight(x+1, y+1) + 0.01
		z4 = self.getTileHeight(x+1, y) + 0.01
		
		self.vertex.addData3f(x, y, z1)
		self.texcoord.addData2f(0, 0)
		self.color.addData4f(1, 1, 1, 1)
		self.normal.addData3f(norm,norm2,1)
		
		self.vertex.addData3f(x, y+1, z2)
		self.texcoord.addData2f(0, 1)
		self.color.addData4f(1, 1, 1, 1)
		self.normal.addData3f(norm,norm2,1)
		
		self.vertex.addData3f(x+1, y+1, z3)
		self.texcoord.addData2f(1, 1)
		self.color.addData4f(1, 1, 1, 1)
		self.normal.addData3f(norm,norm2,1)
		
		self.vertex.addData3f(x+1, y, z4)
		self.texcoord.addData2f(1, 0)
		self.color.addData4f(1, 1, 1, 1)
		self.normal.addData3f(norm,norm2,1)

	def addEmptyTile(self, x, y):
		#z = random()/100.0
		z = 0
		self.vertex.addData3f(x, y, z)
		self.texcoord.addData2f(0, 0)
		self.color.addData4f(1, 1, 1, 1)
		self.normal.addData3f(0,0,1)
		
		self.vertex.addData3f(x, y, z)
		self.texcoord.addData2f(0, 1)
		self.color.addData4f(1, 1, 1, 1)
		self.normal.addData3f(0,0,1)
		
		self.vertex.addData3f(x, y, z)
		self.texcoord.addData2f(1, 1)
		self.color.addData4f(1, 1, 1, 1)
		self.normal.addData3f(0,0,1)
		
		self.vertex.addData3f(x, y, z)
		self.texcoord.addData2f(1, 0)
		self.color.addData4f(1, 1, 1, 1)
		self.normal.addData3f(0,0,1)
		
	def hideTile(self, x, y):
		if (0<=x<self.x) and (0<=y<self.y):
			if self.data[y][x]!=0:
				self.data[y][x] = 0
				row = (self.x*y + x)*4
				
				self.vertex = GeomVertexWriter(self.gvd, 'vertex')
				self.texcoord = GeomVertexWriter(self.gvd, 'texcoord')
				self.color = GeomVertexWriter(self.gvd, 'color')
				self.normal = GeomVertexWriter(self.gvd, 'normal')
				
				self.vertex.setRow(row)
				self.texcoord.setRow(row)
				self.color.setRow(row)
				self.normal.setRow(row)
				
				self.addEmptyTile(x, y)
				#self.update()
	
	def showTile(self, x, y):
		if (0<=x<self.x) and (0<=y<self.y):
			if self.data[y][x]!=1:
				self.data[y][x] = 1
				row = (self.x*y + x)*4
				
				self.vertex = GeomVertexWriter(self.gvd, 'vertex')
				self.texcoord = GeomVertexWriter(self.gvd, 'texcoord')
				self.color = GeomVertexWriter(self.gvd, 'color')
				self.normal = GeomVertexWriter(self.gvd, 'normal')
				
				self.vertex.setRow(row)
				self.texcoord.setRow(row)
				self.color.setRow(row)
				self.normal.setRow(row)
				
				self.addWallTile(x, y)
				
				#self.update()
		
		
	def fill(self):
		for y in range(self.y):
			for x in range(self.x):
				self.data[y][x] = 1
		self.update()
		
	def clear(self):
		self.data = [] # [[1,1,1,1,0,1,0,0,...], [1,0,0,...]... ]
		for y in range(self.y):
			tmp = []
			for x in range(self.x):
				tmp.append(0)
			self.data.append(tmp)
		#for y in range(self.y):
		#	for x in range(self.x):
		#		self.data[y][x] = 0
		self.update()
	
	def fillBorder(self):
		for y in range(self.y):
			for x in range(self.x):
				if self.data[y][x] == 0:
					if (x==0) or (y==0):
						self.data[y][x] = 1
					if (x==self.x-1) or (y==self.y-1):
						self.data[y][x] = 1
					
		self.update()
		
	def getRandomTile(self):
		#while True:
		for i in range(10):# if no success after ten tries, give up and wait
			x = random.randint(1,self.x-1)
			y = random.randint(1,self.y-1)
			if self.data[y][x]==0:
				#print "returning random free tile : %s %s" % (x, y)
				return x, y
		return None
	
	def destroy(self):
		if self.np:
			self.np.remove()
		if self.terrainNP:
			self.terrainNP.remove()
			
class GameMap(DirectObject):
	def __init__(self, filename = None):
		self.name = None
		self.filename = filename
		
		self.x = 0
		self.y = 0
		
		#self.floor = makeFloor(20, self.x, self.y)
		#self.floor.reparentTo(render)
		
		self.NPCroot = NodePath("root")
		self.NPCroot.reparentTo(render)
		
		self.mapObjectRoot = NodePath("mapObjectRoot")
		self.mapObjectRoot.reparentTo(render)
		#self.mapObjectRoot.setTransparency(True)
		self.mapObjectRoot.setTransparency(TransparencyAttrib.MAlpha)
		
		self.mapObjects = {} # map objects
		
		self.mapWall = None
		self.collisionGrid = None
		
		if self.filename is not None:
			self.load()
			#self.collisionGrid.addGeoMip("models/grounds/ground01.jpg")
			
		self.clicker = Clicker()
		
		# NPCs
		self.NPC = {}
		for name in ["ula2", "Kimmo", "Drunkard", "Camilla"]:
			x, y = self.collisionGrid.getRandomTile()
			self.addNPC(name, "male", "humanTex2.png", x,y)
		
		self.player = NPC("arikel", "male", "humanTex2.png")
		self.player.setTilePos(5, 3)
		self.player.reparentTo(render)
		
		
		
		
		# light
		if CONFIG_LIGHT:
			self.light = LightManager()
			self.light.lightCenter.setPos(0,0,0)
			self.light.lightCenter.reparentTo(base.camera)
		
		
		self.keyDic = {}
		for key in [
			"mouse1", "mouse3",
			FORWARD, BACKWARD,
			STRAFE_LEFT, STRAFE_RIGHT,
			TURN_LEFT, TURN_RIGHT,
			UP, DOWN,"h", "b", "t", "g"
			]:
			self.keyDic[key] = 0
			self.accept(key, self.setKey, [key, 1])
			keyUp = key + "-up"
			self.accept(keyUp, self.setKey, [key, 0])
		
		
		self.camHandler = CamHandler()
		self.setMode("playing")
		
		self.accept(OPEN_EDITOR, self.toggle)
		self.accept("quit", self.quit, [["this one is from GameMap", "this one too"]])
		self.accept(SAVE_MAP, self.save, [self.filename])
		self.accept(LOAD_MAP, self.load, [self.filename])
		
		self.accept(CLEAR_COLLISION, self.clearCollision, [])
		self.accept(FILL_COLLISION, self.fillCollision, [])
		
		
		
		
		self.msg = makeMsg(-1.3,0.95,"...")
		
		self.msgTilePos = makeMsg(-1.2,0.95,"...")
		self.cursor = MouseCursor()
		
		self.dialog = None # current dialog
		
		#self.addMapObject("crate1", "crate 1", 12.5, 32.5)
		#self.addMapObject("aldea", "aldea 1", 28.5, 35.5)
		
		self.draggingObject = False
		self.draggedObject = None
		
		taskMgr.add(self.update, "gameMapTask")
	
	def startDrag(self, mapObj):
		self.draggingObject = True
		self.draggedObject = mapObj
		
	def stopDrag(self):
		self.draggingObject = False
		self.draggedObject = None
		
	def openDialog(self, name):
		if self.dialog:
			#print "There was dialog garbage left, %s got his/her dialog shut unpolitely." % (self.dialog.name)
			#self.dialog.destroy()
			#print "a dialog is already open"
			return False
		if name in self.NPC:
			self.NPC[name].stop()
			if name in dialogDic:
				self.dialog = dialogDic[name](self, name)
		
		
	def quit(self, args=[], extraArgs=[]):
		print "Quit has really been fired from an event, baby! args were : \n- %s\nExtra args were:\n%s" % (str(args), str(extraArgs))
		
		
		
	def save(self, filename):
		mapData = {}
		mapData["name"] = self.name
		mapData["X"] = self.x
		mapData["Y"] = self.y
		mapData["collision"] = self.collisionGrid.data
		if self.collisionGrid.hasGeoMip:
			mapData["geomip"] = [self.collisionGrid.texPath, self.collisionGrid.geoMipPath]
			
		mapData["mapObjects"] = []
		for elem in self.mapObjects.values():
			model = elem.model
			mapObjectData = []
			mapObjectData.append(elem.name)
			mapObjectData.append(elem.genre)
			mapObjectData.append(model.getPos())
			mapObjectData.append(model.getHpr())
			mapObjectData.append(model.getScale())
			mapData["mapObjects"].append(mapObjectData)
		
		
		f = open(filename, 'w')
		pickle.dump(mapData, f)
		f.close()
		print "map data saved as %s" % (filename)
		
	def destroy(self):
		if self.mapWall:
			self.mapWall.destroy()
		if self.collisionGrid:
			self.collisionGrid.destroy()
		for mapObj in self.mapObjects.values():
			self.removeMapObject(mapObj.name)
			#mapObj.destroy()
		#self.mapObjects = {}
		
	def load(self, filename=None):
		if filename is None:
			filename = self.filename
		if filename is None:
			return False
		self.destroy()
		
		
		
		mapData = pickle.load(open(filename, 'r'))
		if "name" in mapData:
			self.name = mapData["name"]
			print "Loading map named %s" % (self.name)
		if "X" in mapData:
			self.x = mapData["X"]	
		if "Y" in mapData:
			self.y = mapData["Y"]
		
		if "geomip" in mapData:
			tex = mapData["geomip"][0]
			geomipTex = mapData["geomip"][1]
			self.collisionGrid = CollisionGrid(self.x, self.y, self.name, tex, geomipTex)
		else:
			self.collisionGrid = CollisionGrid(self.x, self.y, self.name)
			
		self.mapWall = MapWall(self.x, self.y, 0)
		
		self.collisionGrid.data = mapData["collision"]
		self.collisionGrid.rebuild()
		#self.collisionGrid.fillBorder()
		
		print "models in use : %s" % (mapData["mapObjects"])
		for data in mapData["mapObjects"]:
			name = data[0]
			genre = data[1]
			pos = data[2]
			hpr = data[3]
			scale = data[4]
			self.addMapObject(
				genre,
				name,
				(pos.getX(), pos.getY(), pos.getZ()),
				(hpr.getX(), hpr.getY(), hpr.getZ()),
				(scale.getX(), scale.getY(), scale.getZ())
				)
			
		
	
	def addMapObject(self, genre, name, pos=(0,0,0), hpr=(0,0,0), scale=(1,1,1)):
		if name not in self.mapObjects:
			mapObject = MapObject(self, genre, name)
			mapObject.setPos(pos) #-self.collisionGrid.terrainScale/3.0)
			mapObject.setHpr(hpr)
			mapObject.setScale(scale)
			mapObject.reparentTo(self.mapObjectRoot)
			self.mapObjects[name] = mapObject
		
	def removeMapObject(self, name):
		if name in self.mapObjects:
			self.mapObjects[name].destroy()
			del self.mapObjects[name]
		
	def setMapObjectPos(self, name, x, y, z=0):
		if name in self.mapObjects:
			self.mapObjects[name].setPos(x, y, z)
			
			
	def clearCollision(self, args=[]):
		if self.mode == "edit":
			self.collisionGrid.clear()
		
	def fillCollision(self, args=[]):
		if self.mode == "edit":
			self.collisionGrid.fill()
		
	def setKey(self, key, value):
		self.keyDic[key] = value
		
	def setMode(self, mode):
		self.mode = mode
		self.camHandler.setMode(mode)
		if mode == "edit":
			for obj in self.mapObjects.values():
				obj.model.clearColor()
				obj.model.setColorScale(1,1,1,1)
				obj.model.setTransparency(TransparencyAttrib.MAlpha)
				
			#if CONFIG_LIGHT: self.light.lightCenter.detachNode()
			#render.setShaderOff()
			#render.setLightOff()
			
		elif mode == "playing":
			for obj in self.mapObjects.values():
				obj.model.clearColor()
				obj.model.setColorScale(1,1,1,1.0)
				obj.model.setTransparency(TransparencyAttrib.MAlpha)
				
			#if CONFIG_LIGHT: self.light.lightCenter.reparentTo(base.camera)
			#render.setShaderAuto()
			
	def toggle(self):
		if self.mode == "edit":
			self.mode = "playing"
			#self.collisionGrid.collisionHide()
			self.camHandler.setMode("playing")
			#base.enableMouse()
			
		else:
			self.mode = "edit"
			self.camHandler.setMode("edit")
			#self.collisionGrid.collisionShow()
			#base.disableMouse()
		
	
		
		
	def addNPC(self, name, modelName, tex, x, y):
		npc = NPC(name, modelName, tex)
		npc.setTilePos(x, y)
		self.NPC[name] = npc
		npc.reparentTo(self.NPCroot)
		
	def removeNPC(self, name):
		if name in self.NPC:
			self.NPC[name].destroy()
			del self.NPC[name]
		
	def playerGoto(self, x, y):
		start = (self.player.getTilePos())
		end = (x, y)
		data = self.collisionGrid.data
		path = astar(start, end, data)
		if path is []:
			#print "... but no good path found"
			return False
		newPath = []
		for tile in path:
			newPath.append((tile[0], tile[1], self.collisionGrid.getTileHeight(tile[0], tile[1])))
		self.player.setPath(newPath)
		return True
	
	def NPCGoto(self, name, x, y):
		#print "NPCGoto called!"
		if name not in self.NPC:
			#print "%s is not a known NPC" % (name)	
			return False
		start = (self.NPC[name].getTilePos())
		end = (x, y)
		data = self.collisionGrid.data
		path = astar(start, end, data)
		if path is []:
			#print "... but no good path found"
			return False
		#else:
		#	print "NPCGoto : path found : %s" % (path)
		newPath = []
		for tile in path:
			newPath.append((tile[0], tile[1], self.collisionGrid.getTileHeight(tile[0], tile[1])))
		self.NPC[name].setPath(newPath)
		
		
	def update(self, task):
		dt = globalClock.getDt()
		if base.mouseWatcherNode.hasMouse():
			mpos = base.mouseWatcherNode.getMouse()
		else:
			return task.cont
		
		
			
		# click on NPC :
		res = self.clicker.getMouseObject(self.NPCroot)
		#res = self.clicker.getMouseObject(render)
		if res is not None:
			#print "Found a name : %s " % (res.getIntoNodePath().getName())
			name = res.getIntoNodePath().getName()
			msg = "Talk to " + name
			self.msg.setText(msg)
			self.msg.setPos(mpos.getX()*1.33+0.1, mpos.getY()+0.02)
			if self.keyDic["mouse1"]:# and name != self.player.name:
				self.openDialog(name)
			elif self.keyDic["mouse3"]:# and name != self.player.name:
				pass
				#self.removeNPC(name)
				
		else:
			self.msg.setText("")
		
		# click on MapObject :
		res = self.clicker.getMouseObject(self.mapObjectRoot)
		
		if res is not None:
			#print "Found a name : %s " % (res.getIntoNodePath().getName())
			name = res.getIntoNodePath().getName()
			msg = "mapObject : " + name
			self.msg.setText(msg)
			self.msg.setPos(mpos.getX()*1.33+0.1, mpos.getY()+0.02)
			if self.keyDic["mouse1"]:# and name != self.player.name:
				#self.openDialog(name)
				if not self.draggingObject:
					self.startDrag(self.mapObjects[name])
				print "map object left click"
			
				
			if self.keyDic["mouse3"]:# and name != self.player.name:
				#self.NPC[name].destroy()
				#self.removeMapObject(name)
				print "map object right click"
		
			if self.keyDic["h"]:
				#self.mapObjectMoveZ(self.mapObjects[name], dt)
				self.mapObjects[name].moveZ(dt)
				
			elif self.keyDic["b"]:
				#self.mapObjectMoveZ(self.mapObjects[name], -dt)
				self.mapObjects[name].moveZ(-dt)
				
			if self.keyDic["t"]:
				#self.mapObjectMoveScale(self.mapObjects[name], dt)
				#self.mapObjects[name].scale(dt)
				self.mapObjects[name].rotate(dt)
				
			elif self.keyDic["g"]:
				#self.mapObjectMoveScale(self.mapObjects[name], -dt)
				#self.mapObjects[name].scale(-dt)
				self.mapObjects[name].rotate(-dt)
				
		if self.draggingObject and not self.keyDic["mouse1"]:
			self.stopDrag()
		
		pos = self.clicker.getMouseTilePos(mpos)
		if pos is None:
			return task.cont
		else:
			msg = "coord : " + str(pos[0]) + "/" + str(pos[1])
			self.msgTilePos.setText(msg)
			if self.draggingObject:		
				self.draggedObject.setTilePos(pos[0], pos[1])
			
		if self.mode == "edit":
			if self.keyDic["mouse1"]:
				self.collisionGrid.showTile(pos[0], pos[1])
			elif self.keyDic["mouse3"]:
				self.collisionGrid.hideTile(pos[0], pos[1])
		elif self.mode == "playing":
			if self.keyDic["mouse1"] and not self.draggingObject:
				self.playerGoto(pos[0], pos[1])
				
				#for name in self.NPC:
				#	self.NPCGoto(name, pos[0], pos[1])
		
		if self.keyDic[FORWARD]:
			self.camHandler.forward(dt)
		if self.keyDic[BACKWARD]:
			self.camHandler.backward(dt)
		
		if self.keyDic[STRAFE_LEFT]:
			self.camHandler.strafeLeft(dt)
			
		if self.keyDic[STRAFE_RIGHT]:
			self.camHandler.strafeRight(dt)
			
		if self.keyDic[TURN_LEFT]:
			self.camHandler.turnLeft(dt)
		if self.keyDic[TURN_RIGHT]:
			self.camHandler.turnRight(dt)
			
		if self.keyDic[UP]:
			self.camHandler.lookUp(dt)
		if self.keyDic[DOWN]:
			self.camHandler.lookDown(dt)
		
		#-------------------------------------------------
		# NPC random movement
		for name in self.NPC:
			npc = self.NPC[name]
			if npc.timer <= 0:
				if npc.mode == "idle":
					if self.dialog:
						if self.dialog.name != name:
							#print "Sending NPC to random pos"
							tile = self.collisionGrid.getRandomTile()
							if tile is not None:
								self.NPCGoto(name, tile[0], tile[1])
							else:
								npc.resetTimer()
					else:
						tile = self.collisionGrid.getRandomTile()
						if tile is not None:
							self.NPCGoto(name, tile[0], tile[1])
		
		return task.cont
		

class GameManager(FSM):
	def __init__(self):
		FSM.__init__(self, 'Game')
		self.clicker = Clicker()
		
		# light
		if CONFIG_LIGHT:
			self.light = LightManager()
			self.light.lightCenter.setPos(0,0,0)
			self.light.lightCenter.reparentTo(base.camera)
		
	def loadGameMap(self, filename):
		self.map = GameMap(filename)
		
#gamemap = GameMap(40,25)
gamemap = GameMap("maps/mapCode.txt")

sky = SkyBox()
#sky.load("hipshot1")
sky.load("teal1")
#sky.set("teal1")

#button = MainButton(-0.5,0.8, u"PPARPG coming...")
#dg = DialogGui(0,-0.5,"Kimmo")


base.accept("escape", sys.exit)

base.disableMouse()

base.setFrameRateMeter(True)

props = WindowProperties()
props.setCursorHidden(True) 
base.win.requestProperties(props)

bgMusic = loader.loadSfx("music/preciouswasteland.ogg")
bgMusic.setLoop(True)
bgMusic.play()

#messenger.send("quit", [["and", "a", "shit", "load", "of", "other", "things"]])

render.setShaderAuto()
render.setTransparency(TransparencyAttrib.MAlpha)
#render.setAntialias(AntialiasAttrib.MMultisample)
#render.setAntialias(AntialiasAttrib.MAuto)

run()
