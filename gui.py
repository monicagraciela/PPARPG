#!/usr/bin/python
# -*- coding: utf8 -*-

from pandac.PandaModules import *
import direct.directbase.DirectStart
from direct.gui.DirectGui import *
from direct.gui.OnscreenText import OnscreenText
from direct.gui.OnscreenImage import OnscreenImage
from direct.interval.IntervalGlobal import *

import sys, math, random, os.path, os, re

RATIO = base.getAspectRatio()

textColors = {}
textColors["white"] = ((1,1,1,1), (0,0,0,0.8))
textColors["white_transp"] = ((1,1,1,1), (0,0,0,0.0))

#FONT = loader.loadFont("fonts/oldtypewriter.ttf")
FONT = loader.loadFont("fonts/oldtypewriter.ttf")
FONT_SCALE = 0.035

FONT2 = loader.loadFont("fonts/oldtypewriter.egg")
FONT_SCALE2 = 0.035

#-------------------------------------------------------------------------------
# makeImg
#-------------------------------------------------------------------------------
def makeImg(x,y, path, scale = 1):
	a = OnscreenImage(image=path, pos=(float(x),0,float(y)), hpr=None, scale=scale, color=None, parent=None, sort=0)
	a.setTransparency(True)
	return a

#-------------------------------------------------------------------------------
# makeMsg
#-------------------------------------------------------------------------------
def makeMsg(x,y, txt = "msg", color = "white"):
	fg = textColors[color][0]
	bg = textColors[color][1]
	M = OnscreenText(style=1, fg=fg, bg=bg, pos=(x, y), align=TextNode.ALeft, scale = FONT_SCALE, mayChange = 1, font = FONT)
	M.setText(txt)
	return M

def makeMsgRight(x,y, txt = "msg", color = "white"):
	m = makeMsg(x, y, txt, color)
	m["align"]=TextNode.ARight
	return m

#-------------------------------------------------------------------------------
# MainButton
#-------------------------------------------------------------------------------
class MainButton(DirectButton):
	def __init__(self, x, y, name):
		DirectButton.__init__(self,
			frameSize = (-0.35,0.35,-0.07,0.07),
			pos = (x, 1, y),
			pad = (0,0),
			borderWidth=(0.008,0.008),
			frameColor=(0.2,0.2,0.2,0.6),
			#pressEffect = None,
			#scale = (0.4, 1, 0.1),
			#relief = None,
			relief = DGG.GROOVE,
			#relief = DGG.RIDGE,
			rolloverSound = None,#soundDic["rollover"],
			clickSound = None,#soundDic["select_confirm"],
			text_font = FONT,
			#text_scale = (0.01,0.0125,1),
			text_scale = (0.06,0.06,1.0),
			text_fg = (0.8,0.8,0.8,1),
			#text_shadow = (0.25,0.25,0.25,1),
			text_bg = (0,0,0,0.0),
			text = name,
			text_align = TextNode.ACenter,
			text_pos = (0, -0.025),
			#geom = None
			text_mayChange = True,
		)
		self.initialiseoptions(MainButton)
		
		self.bind(DGG.ENTER, command=self.onHover, extraArgs=[self])
		self.bind(DGG.EXIT, command=self.onOut, extraArgs=[self])
		
	def onHover(self, extraArgs, sentArgs):
		self["text_fg"] = (1,1,1,1)
		#self["text_shadow"] = (0.0,0.5,0.95,1)
		
	def onOut(self, extraArgs, sentArgs):
		self["text_fg"] = (0.8,0.8,0.8,1)
		#self["text_shadow"] = (0.0,0.5,0.95,1)


#-------------------------------------------------------------------------------
# Menu
#-------------------------------------------------------------------------------

class MenuButton(DirectButton):
	def __init__(self, x, y, w=0.1, h=0.04, name = "dialogButton"):
		self.x = x
		self.y = y
		self.w = w
		self.h = h
		self.name = name
		#print "created dialog button %s" % (name)
		#print "Type w : %s" % (type(self.w))
		#print "Type h : %s" % (type(self.h))
		#print "Type x : %s" % (type(self.x))
		#print "Type y : %s" % (type(self.y))
		
		DirectButton.__init__(self,
			frameSize = (-self.w*RATIO,self.w*RATIO,-h,h),
			pos = (x, 1, y),
			pad = (0,0),
			borderWidth=(0.008,0.008),
			frameColor=(0.1,0.1,0.1,0.8),
			relief = DGG.RIDGE,
			rolloverSound = None,#soundDic["rollover"],
			clickSound = None,#soundDic["select_confirm"],
			text_font = FONT,
			text_scale = FONT_SCALE,
			text_fg = (0.8,0.8,0.8,1),
			text = name,
			text_align = TextNode.ALeft,
			text_pos = (-self.w*RATIO, -0.02),
			text_mayChange = True,
			sortOrder=1
		)
		self.initialiseoptions(MenuButton)
		self.bind(DGG.ENTER, command=self.onHover, extraArgs=[self])
		self.bind(DGG.EXIT, command=self.onOut, extraArgs=[self])
		
	def onHover(self, extraArgs=[], sentArgs=[]):
		self["text_fg"] = (1,1,1,1)
		self["frameColor"]=(0.2,0.2,0.2,0.8)
		#self["text_shadow"] = (0.0,0.5,0.95,1)
		
	def onOut(self, extraArgs=[], sentArgs=[]):
		self["text_fg"] = (0.8,0.8,0.8,1)
		self["frameColor"]=(0.1,0.1,0.1,0.8)	

class TopMenu:
	def __init__(self, x, y, w=0.1, h=0.04, cmdList=[]):
		padding = 0.05
		
		self.x = x
		self.y = y
		self.w = w
		self.h = h
		
		# the first string of the cmdList is used for the top button
		self.topCmd = cmdList.pop(0)
		
		bottom = len(cmdList)*self.h*2+self.h+padding
		
		self.frame = DirectFrame(
			frameSize = ((-self.w-padding)*RATIO,(self.w+padding)*RATIO,-bottom,self.h+padding),
			frameColor=(0.9, 0.7, 0.9, 0.0),
			pos = (self.x,1,self.y),
			pad = (0,0),
			borderWidth=(0.0,0.0),
			relief = DGG.GROOVE,
			sortOrder=-1,
			state = DGG.NORMAL
		)
		
		self.topButton = MenuButton(0, 0, self.w, self.h, self.topCmd)
		self.topButton.reparentTo(self.frame)
		
		self.menu = ActionSubMenu(self.topButton, cmdList, "down")
		self.menu.frame.reparentTo(self.frame)
		
		self.topButton.bind(DGG.ENTER, self.expand)
		self.frame.bind(DGG.EXIT, self.retract)
		
		self.visible = True
		
	def setPos(self, pos):
		self.frame.setPos(pos)
		
	def expand(self, extraArgs=[]):
		print "top menu : expand"
		self.topButton.onHover()
		self.menu.expand()
			
	def retract(self, extraArgs=[]):
		print "top menu : retract"
		self.topButton.onOut()
		self.menu.retract()
	
	def hide(self):
		self.frame.hide()
		self.visible = False
		
	def show(self):
		self.frame.show()
		self.visible = True
		
	def toggleVisible(self):
		if self.visible:
			self.hide()
		else:
			self.show()


class ActionMenu:
	"""ActionMenu : this menu doesn't have an always visible top button, all buttons in are the same."""
	
	def __init__(self, x, y, w=0.1,h=0.04,cmdList=[]):
		self.padding = 0.05
		self.x = x
		self.y = y
		self.w = w
		self.h = h
		
		self.cmdList = cmdList
		bottom = len(self.cmdList)*self.h*2
		
		self.frame = DirectFrame(
			frameSize = ((-self.w-self.padding)*RATIO,(self.w+self.padding)*RATIO,-bottom,self.h+self.padding),
			#frameSize = (0,0,0,0),
			frameColor=(0.7, 0.7, 0.9, 0.0),
			pos = (self.x,1,self.y),
			pad = (0,0),
			borderWidth=(0.0,0.0),
			relief = DGG.GROOVE,
			state = DGG.NORMAL
		)
		
		self.buttons = []
		for i, m in enumerate(cmdList):
			button = MenuButton(0, -i*2*h, self.w, self.h, m)
			button.reparentTo(self.frame)
			button.bind(DGG.ENTER, self.onMainButtonHover, [i])
			self.buttons.append(button)
			
		
		self.subMenus = []
		
		#self.frame.bind(DGG.ENTER, self.expand)
		self.frame.bind(DGG.EXIT, self.retract)
		
		self.retract()
		
	def hide(self):
		self.frame.hide()
		self.visible = False
		
	def show(self):
		self.frame.show()
		self.visible = True
		
	def toggleVisible(self):
		if self.visible:
			self.hide()
		else:
			self.show()
		
	def setPos(self, pos):
		self.frame.setPos(pos[0]*RATIO, 1,pos[1])
		
	def onMainButtonHover(self, n, extraArgs=[]):
		if n >= len(self.cmdList):
			return False
		self.buttons[n].onHover()
		for submenu in self.subMenus:
			if self.buttons[n] is submenu.baseButton:
				#print "Expanding menu %s" % (n)
				submenu.expand()
			else:
				#print "Hovering %s" % (self.buttons[n].name)
				#print "-> doesn't match menu with button named %s\n" % (submenu.baseButton.name)
				submenu.retract()
		
		 
		
	def addSubMenu(self, n, cmdList=[]):
		if n >= len(self.cmdList):
			return False
		self.subMenus.append(ActionSubMenu(self.buttons[n], cmdList))
		
	def expand(self, extraArgs=[]):
		#print "Expand!"
		if base.mouseWatcherNode.hasMouse():
			mpos = base.mouseWatcherNode.getMouse()
		self.frame.setPos(mpos[0]*RATIO+self.w, 1, mpos[1])
		
		self.frame.show()
			
	def retract(self, extraArgs=[]):
		for submenu in self.subMenus:
			submenu.retract()
		self.frame.hide()
		
	def clear(self):
		for b in self.buttons:
			b.destroy()
		self.buttons = []
		for menu in self.subMenus:
			menu.destroy()
		self.subMenus = []
		
	def rebuild(self, cmdList=[]):
		self.clear()
		bottom = len(cmdList)*self.h*2
		self.frame["frameSize"] = ((-self.w-self.padding)*RATIO,(self.w+self.padding)*RATIO,-bottom,self.h+self.padding)
		
		for i, m in enumerate(cmdList):
			button = MenuButton(0, -i*2*self.h, self.w, self.h, m)
			button.reparentTo(self.frame)
			self.buttons.append(button)



class ActionSubMenu:
	def __init__(self, baseButton, cmdList=[], direction="right"):
		self.baseButton = baseButton # MenuButton
		self.padding = 0.05
		self.w = self.baseButton.w
		self.h = self.baseButton.h
		bottom = len(cmdList)*self.h*2
		self.cmdList = cmdList
		
		if direction == "right":
			self.x = self.baseButton.w * 2 * RATIO
			self.y = 0
			self.frameSize = ((-self.w)*RATIO,(self.w+self.padding)*RATIO,-bottom,self.h+self.padding)
		elif direction == "down":
			self.x = 0
			self.y = -self.h*2.0
			self.frameSize = ((-self.w)*RATIO,(self.w)*RATIO,-bottom+self.padding,self.h)
		
		self.frame = DirectFrame(
			#frameSize = ((-self.w)*RATIO,(self.w+self.padding)*RATIO,-bottom,self.h+self.padding),
			frameSize = self.frameSize,
			#frameSize = (0,0,0,0),
			frameColor=(0.7, 0.7, 0.9, 0.0),
			pos = (self.x,1,self.y),
			pad = (0,0),
			borderWidth=(0.0,0.0),
			relief = DGG.GROOVE,
			state = DGG.NORMAL,
			sortOrder=-1
		)
		self.frame.reparentTo(self.baseButton)
		
		
		self.buttons = []
		for i, m in enumerate(cmdList):
			button = MenuButton(0, -i*2*self.h, self.w, self.h, m)
			button.reparentTo(self.frame)
			self.buttons.append(button)
			button.bind(DGG.ENTER, self.onMainButtonHover, [i])
			
		self.subMenus = []
		
		self.retract()
		self.frame.bind(DGG.EXIT, self.retract)
		
	def expand(self, extraArgs=[]):
		for menu in self.subMenus:
			menu.retract()
		self.baseButton.onHover()
		self.frame.show()
			
	def retract(self, extraArgs=[]):
		self.frame.hide()
		for menu in self.subMenus:
			menu.retract()
		
	def clear(self):
		for b in self.buttons:
			b.destroy()
		self.buttons = []
		for menu in self.subMenus:
			menu.destroy()
		self.subMenus = []
		
	def onMainButtonHover(self, n, extraArgs=[]):
		if n >= len(self.cmdList):
			return False
		self.buttons[n].onHover()
		for submenu in self.subMenus:
			if self.buttons[n] is submenu.baseButton:
				submenu.expand()
			else:
				submenu.retract()
		
		 
		
	def addSubMenu(self, n, cmdList=[]):
		if n >= len(self.cmdList):
			return False
		self.subMenus.append(ActionSubMenu(self.buttons[n], cmdList))
		
	def rebuild(self, cmdList=[]):
		self.clear()
		bottom = len(cmdList)*self.h*2
		self.frame["frameSize"] = ((-self.padding)*RATIO,(self.w+self.padding)*RATIO,-bottom,self.h+self.padding)
		
		for i, m in enumerate(cmdList):
			button = MenuButton(0, -i*2*self.h, self.w, self.h, m)
			button.reparentTo(self.frame)
			self.buttons.append(button)

	def destroy(self):
		for b in self.buttons:
			b.destroy()


class EditorGui:
	def __init__(self, editor):
		self.editor = editor
		
		self.topMenu = TopMenu(-0.7*RATIO, 0.9, 0.2,0.04, ["File", "New", "Open...", "Save", "Save as..."])
		mapList = os.listdir("maps")
		self.topMenu.menu.addSubMenu(1, mapList)
		for i, map in enumerate(mapList):
			path = "maps/" + map
			self.topMenu.menu.subMenus[0].buttons[i].bind(DGG.B1PRESS, self.editor.load, [path])
		
		self.objectMenu = ActionMenu(-0.7*RATIO, 0.9, 0.16,0.035, ["Object", "Grab", "Rotate", "MoveZ", "Duplicate", "Destroy"])
		
			
		self.infoLabel = makeMsgRight(0.95*RATIO,-0.95,"")
		self.objectLabel = makeMsg(-0.95*RATIO,-0.85,"")
		
		self.hide()
		
	def hide(self):
		self.topMenu.hide()
		self.objectMenu.hide()
		self.infoLabel.hide()
		self.objectLabel.hide()
		self.visible = False
		
	def show(self):
		self.topMenu.show()
		#self.objectMenu.show()
		self.infoLabel.show()
		self.objectLabel.show()
		self.visible = True
		
	def openObjectMenu(self, obj, mpos):
		"""obj is a MapObject"""
		self.objectMenu.show()
		pos = (mpos[0] + self.objectMenu.w, mpos[1])
		self.objectMenu.setPos(pos)
		
	def toggleVisible(self):
		if self.visible:
			self.hide()
		else:
			self.show()
	
	def setInfo(self, info):
		self.infoLabel.setText(str(info))
		
	def setObjInfo(self, mpos, info):
		self.objectLabel.setPos(mpos.getX()*1.33+0.1, mpos.getY()+0.02)
		self.objectLabel.setText(str(info))
		
	def clearObjInfo(self):
		self.objectLabel.setText("")
