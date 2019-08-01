import math
import FreeCAD, FreeCADGui
import Part
from pivy import coin
import ScrewMaker
u = FreeCAD.Units.parseQuantity
v = FreeCAD.Base.Vector
screwMaker = ScrewMaker.Instance()

# 9 basic needs
# 1. sustenance
# 2. safety, protection
# 3. love
# 4. empathy, understanding
# 5. rest, recreation, play
# 6. community
# 7. creativity
# 8. autonomy
# 9. meaning

# to say 'no':
#  1. be sure to let the other know that you have received their request as a gift
#		a precious chance to contribute to their wellbeing
#  	this is best done nonverbally
#	SHOW that their REQUEST is a PRECIOUS GIFT to contribute to their wellbeing
#  2. be aware that 'no' is a poor expression of a need.  it backs a need.
#    SAY THE NEED that keeps one from saying 'yes'.
#  3. END ON A REQUEST that searches for a way to get everybody's needs met

# When not listening, interrupt with your need.  Other party wants actual communication to happen too.
#  can be helpful to ask what the person wants back when expressing (could be empathy they're unaware of)
#   marshall had the experience of 'i'm having some confusing following you; what is it you want back from me saying this?' 'oh nothing in particular' 'well is it all right if I ignore you then?' 'do and I'll kill you!' this seemed to help the person talk more clearly to others even, but it's notable marshall was probably already known to be very caring and that statement would have been out of character as a real insult
# when other party not speaking productively, interrupt to connect with their need:
#	"excuse me, excuse me for interrupting, but I really want to be sure I'm connecting to
#	what you want me to hear by telling me this.  Are you saying that you feel angry right now
#	about this thing in the past, and you'd really like some understanding about how painful it was?"
#		-> guess was wrong: she decided she felt hurt rather than angry; was very relevent to
#		   present moment
# practice:
#	- list messages people have said that make one afraid to express oneself
#		things one is most afraid of hearing
#		what are these replies we do not express?
#		how might the other respond?
#		how can we empathize with this response?
#		"oh, you're too sensitive" hmm... i'm saying my safety relies on what they say
#			but what's relevent is how to respond to that next, the feeling and need
#			maybe they're feeling frustrated because they need understanding for what they said or experienced
#		hey this PREPARES YOU for the hard things!
#		comparable: WRITE DOWN hard things you hear!

# to really listen to stories from the past, listen for what is alive in the person NOW

# X is positive right
# Y is positive away from viewer
# Z is positive up

# overlap lip
#	horizontal portion
#		evenly spaced screwholes
#		line up with outer edge
#		screw heads go on outside
#	corner
#		slotted to mate edges

# outer sides
#	outer dimensions are shrunk to provide for screw heads (if using screws)

			
class Tabbing:
	def __init__(self, tabDistance, thickness, screwDistance=0, screwEdgeDistance=0, screwDiameter=0, screwMinLength=0, screwMaxLength=0, nutDiameter=0, nutThickness=0):
		self.tabDistance = tabDistance.Value
		self.thickness = thickness.Value
		self.screwDistance = screwDistance.Value
		self.screwEdgeDistance = screwEdgeDistance.Value
		self.screwDiameter = screwDiameter.Value
		self.screwMinLength = screwMinLength.Value
		self.screwMaxLength = screwMaxLength.Value
		self.nutDiameter = nutDiameter.Value
		self.nutThickness = nutThickness.Value
		self.update()

	def update(self):
		self.tabWidth = self.tabDistance / 2
		self.slotCutOverlap = self.tabWidth / 2
		self.screwTabWidth = self.tabWidth
		if self.nutDiameter and self.screwDiameter:
			if self.screwTabWidth < self.nutDiameter:
				self.screwTabWidth = self.nutDiameter
			if self.screwDiameter / 2 < self.slotCutOverlap:
				self.slotCutOverlap = self.screwDiameter / 2

class TabbedCorner:
	corners = {}
	@staticmethod
	def reset():
		TabbedCorner.corners = {}
	def __init__(self, v):
		self.v = v
		if self in TabbedCorner.corners:
			self.filled = True
			self.filler = TabbedCorner.corners[self]
		else:
			self.filled = False
			self.filler = None

	def fill(self, filler):
		if self in TabbedCorner.corners:
			print 'already filled', self.v
			raise Exception("already filled")
		TabbedCorner.corners[self] = filler
		self.filler = TabbedCorner.corners[self]
		self.filled = True

	def __hash__(self):
		return (hash(self.v.x) << 1) ^ hash(self.v.y) ^ (hash(self.v.z) << 2)
	def __eq__(self, other):
		return self.__hash__() == other.__hash__()
	def __ne__(self, other):
		return not (self.__eq__(other))

# NEXT:
# The two floor approaches of sending beams down below don't really work because the pieces to affix them are so close to each other.
# Alternative solutions include multiple layers so no cross-connections are needed inside here,
#   or using the wide floor with a layer of floor flat against it below (easiest).

class TabbedEdge:
	trace = False
	@staticmethod
	def FromFaces(tabbing, face1, face2, screwFace1 = True, screwFace2 = True):
		v2v = lambda vv: v(vv.X, vv.Y, vv.Z)
		samev = lambda v1, v2: v1.x == v2.x and v1.y == v2.y and v1.z == v2.z
		coordlist = lambda v: [v.x, v.y, v.z]
		ret = []
		if TabbedEdge.trace:
			print 'comparing 2 faces'
		for edge1 in face1.Edges:
			for edge2 in face2.Edges:
				vs1 = [v2v(x) for x in edge1.Vertexes]
				vs2 = [v2v(x) for x in edge2.Vertexes]
				if (samev(vs1[0], vs2[0]) and samev(vs1[1], vs2[1])) or (samev(vs1[0], vs2[1]) and samev(vs1[1], vs2[0])):
					cutFlag = coordlist(vs1[0]) < coordlist(vs1[1])
					if TabbedEdge.trace:
						print 'found edge ', vs1[0], ' ', vs1[1]
					ret.append( (
						TabbedEdge(tabbing, vs1[0], vs1[1], face1, face2, cutFlag, screwFace1, screwFace2),
						TabbedEdge(tabbing, vs1[0], vs1[1], face2, face1, not cutFlag, screwFace2, screwFace1)
					) )
		return ret
				

	def __init__(self, tabbing, v1, v2, cutFace, otherFace, cutFlag, cutScrewFlag, otherScrewFlag, cutMidLeft= False, cutMid1 = False, cutMid2 = False, corner1Flag = True, corner2Flag = True):
		self.c1 = TabbedCorner(v1)
		self.c2 = TabbedCorner(v2)
		self.cutFace = cutFace
		self.otherFace = otherFace
		self.cutMidLeft = cutMidLeft
		self.cutMid1 = cutMid1
		self.cutMid2 = cutMid2
		self.corner1Flag = corner1Flag
		self.corner2Flag = corner2Flag
		self.dist = (v2 - v1).Length
		if self.dist == 0:
			raise Exception('endpoints are coincident')
		self.unitv = (v2 - v1) / self.dist
		self.tabbing = tabbing
		cutDirection = cutFace.CenterOfMass - (v1 + v2) / 2
		if TabbedEdge.trace:
			print 'edge dist = ', self.dist
			print 'face center of mass = ', cutFace.CenterOfMass
			print 'edge direction = ', self.unitv
			print 'edge to center of mass arrow = ', cutDirection
		cutDirection -= cutDirection.dot(self.unitv) * self.unitv
		if cutDirection.Length == 0:
			raise Exception('cut direction is zero')
		self.cutDirection = cutDirection / cutDirection.Length
		self.cutFlag = cutFlag
		self.cutNormal = self.unitv.cross(self.cutDirection)
		self.cutScrewFlag = cutScrewFlag and self.tabbing.screwDistance
		self.otherScrewFlag = otherScrewFlag and self.tabbing.screwDistance
		self.screwFlag = self.cutScrewFlag or self.otherScrewFlag
		if self.screwFlag:
			self.screwCount = int(math.ceil(self.dist / self.tabbing.screwDistance) + 1)
		else:
			self.screwCount = 0
		if not self.c1.filled and cutFlag:
			self.c1.fill(self.cutFace)
		elif not self.c2.filled and not cutFlag:
			self.c2.fill(self.cutFace)
		self.haveEnd1 = (self.c1.filler == self.cutFace or self.c1.filler == self.otherFace)
		self.haveEnd2 = (self.c2.filler == self.cutFace or self.c2.filler == self.otherFace)
		if self.tabbing.screwDistance:
			if self.screwCount % 2 != 0:
				++ self.screwCount
			screwOffset = self.tabbing.screwTabWidth / 2 + self.tabbing.screwEdgeDistance
			screwOffset2 = screwOffset
			if self.corner1Flag:
				screwOffset += self.tabbing.thickness
			if self.corner2Flag:
				screwOffset2 += self.tabbing.thickness
			if screwOffset > self.dist:
				if TabbedEdge.trace:
					print screwOffset, ' > ', self.dist, ' so only 1 screw'
				self.screwCount = 1
				self.screwPositions = [self.dist / 2]
			else:
				screwDelta = (self.dist - screwOffset - screwOffset2) / (self.screwCount - 1)
				self.screwPositions = [idx * screwDelta + screwOffset for idx in xrange(self.screwCount)]
				if TabbedEdge.trace:
					print 'normal calculation of ', self.screwCount, ' screws: ', self.screwPositions
		else:
			self.screwPositions = []
	
	def calculate(self):
		pos = 0
		self.cuts = None

		self.tabbing.update()

		screwIdx = 0
		tabnext = self.cutFlag
		if TabbedEdge.trace:
			print 'Calculating from ', self.c1.v, ' to ', self.c2.v
			print 'Cutting in direction ', self.cutDirection

		if self.corner1Flag:
			# fill for corner 1
			if self.c1.filler != self.cutFace:
				slotpos = 0
				slotlen = self.tabbing.thickness
				if not self.cutMid1:
					slotpos -= self.tabbing.slotCutOverlap
					slotlen += self.tabbing.slotCutOverlap
				if not tabnext:
					slotlen += self.tabbing.slotCutOverlap
				if TabbedEdge.trace:
					print "Slotting corner 1 from ", slotpos, " to ", slotpos + slotlen
				self.addslot(slotpos, slotlen)
			elif TabbedEdge.trace:
				print "Tabbing corner 1 from ", pos, " to ", pos + self.tabbing.thickness
			pos += self.tabbing.thickness
		if self.corner2Flag:
			stopTabbingAt = self.dist - self.tabbing.thickness
		else:
			stopTabbingAt = self.dist

		while pos < stopTabbingAt - self.tabbing.slotCutOverlap:
			# self.cutScrewFlag indicates we can make screw tabs here
			# self.otherScrewFlag indicates we can make screw slots here
			if tabnext:
				canscrewhere = self.cutScrewFlag
				canscrewnext = self.otherScrewFlag
			else:
				canscrewhere = self.otherScrewFlag
				canscrewnext = self.cutScrewFlag
			possibleScrewPos = pos + self.tabbing.screwTabWidth / 2
			if canscrewnext:
				nextScrewPos = pos + self.tabbing.tabWidth + self.tabbing.screwTabWidth / 2
			else:
				nextScrewPos = pos + self.tabbing.tabWidth * 2 + self.tabbing.screwTabWidth / 2
			if screwIdx < len(self.screwPositions):
				goalScrewPos = self.screwPositions[screwIdx]
			else:
				goalScrewPos = float('inf')
			if canscrewhere and abs(goalScrewPos - possibleScrewPos) < abs(goalScrewPos - nextScrewPos):
				# place a screw
				#slotlen = 2 * (goalScrewPos - pos)
				#slotlen = goalScrewPos + self.tabbing.screwTabWidth / 2 - pos
				slotlen = self.tabbing.screwTabWidth
				if pos + slotlen > stopTabbingAt:
					slotlen = stopTabbingAt - pos
				screwpos = pos + slotlen / 2
				if tabnext:
				 	self.addscrewtab(screwpos)
				else:
				 	self.addscrewslot(pos, screwpos, slotlen)
				if TabbedEdge.trace:
					print "Placing screw at ", screwpos, " from ", pos, " to ", pos + slotlen
				pos += slotlen
				screwIdx = screwIdx + 1
			else:
				if TabbedEdge.trace:
					if canscrewhere:
						print "Waiting at ", possibleScrewPos, " for ", nextScrewPos, " which is closer to screw goal pos of ", goalScrewPos
				# place a tab
				tabwidth = self.tabbing.tabWidth
				if pos + tabwidth > stopTabbingAt:
					tabwidth = stopTabbingAt - pos
				if not tabnext:
					if TabbedEdge.trace:
						print "Slotting from ", pos, " to ", pos + tabwidth
					self.addslot(pos, tabwidth)
				elif TabbedEdge.trace:
					print "Tabbing from ", pos, " to ", pos + tabwidth
				pos += tabwidth
			tabnext = not tabnext

		if self.corner2Flag:
			# fill for corner 2
			if self.c2.filler != self.cutFace:
				slotpos = self.dist - self.tabbing.thickness
				slotlen = self.tabbing.thickness
				if not self.cutMid2:
					slotlen += self.tabbing.slotCutOverlap
				if tabnext:
					slotlen += self.tabbing.slotCutOverlap
					slotpos -= self.tabbing.slotCutOverlap
				if TabbedEdge.trace:
					print "Slotting corner 2 from ", slotpos, " to ", slotpos + slotlen
				self.addslot(slotpos, slotlen)
			elif TabbedEdge.trace:
				print "Tabbing corner 1 from ", pos, " to ", pos + self.tabbing.thickness

		return self.cuts
		
	def addcut(self, startPos, length, left, right):
		if self.cutMidLeft and left < 0:
			left = 0
		if self.cutMid1 and startPos < 0:
			length += startPos
			startPos = 0
		if self.cutMid2 and startPos + length > self.dist:
			length = self.dist - startPos
		raw_coords = [v(left, 0, 0), v(right, 0, 0), v(right, length, 0), v(left, length, 0), v(left, 0, 0)]
		coords = [self.c1.v + coord.x * self.cutDirection + (coord.y + startPos) * self.unitv - self.tabbing.thickness * 2 * self.cutNormal for coord in raw_coords]
		front = Part.Face(Part.makePolygon(coords))
		cut = front.extrude(self.tabbing.thickness * 3 * self.cutNormal)
		if TabbedEdge.trace:
			print 'cut ', coords, ' through ', self.tabbing.thickness * 3 * self.cutNormal
		if self.cuts is None:
			self.cuts = cut
		else:
			self.cuts = self.cuts.fuse(cut)
		return cut

	def addslot(self, startPos, length):
		self.addcut(startPos, length, -self.tabbing.thickness, self.tabbing.thickness)

	def addscrewtab(self, screwPos):
		if self.tabbing.screwDiameter:
			margin = (self.tabbing.thickness - self.tabbing.screwDiameter) / 2
			#self.addcut(screwPos - self.tabbing.screwDiameter / 2, self.tabbing.screwDiameter, margin, margin + self.tabbing.screwDiameter)
			cut = Part.makeCylinder(self.tabbing.screwDiameter / 2, self.tabbing.thickness * 3, self.c1.v + self.tabbing.thickness / 2 * self.cutDirection + screwPos * self.unitv - self.tabbing.thickness * 2 * self.cutNormal, self.cutNormal)
			if self.cuts is None:
				self.cuts = cut
			else:
				self.cuts = self.cuts.fuse(cut)

	def addscrewslot(self, startPos, screwPos, length):
		# other side to tab into
		self.addcut(startPos, length, -self.tabbing.thickness, self.tabbing.thickness)
		if self.tabbing.screwDiameter:
			# screw body
			self.addcut(screwPos - self.tabbing.screwDiameter / 2, self.tabbing.screwDiameter, 0, self.tabbing.screwMaxLength)
			# nut body
			self.addcut(screwPos - self.tabbing.nutDiameter / 2, self.tabbing.nutDiameter, self.tabbing.screwMinLength - self.tabbing.nutThickness, self.tabbing.screwMinLength)

class FastenedFace:
	def __init__(self, tabbing, v1, v2, width1, width2, cutDirection, widthDirection):
		self.tabbing = tabbing
		self.v1 = v1
		self.v2 = v2
		self.dist = (v2 - v1).Length
		self.margin = self.tabbing.screwEdgeDistance
		self.cutDirection = cutDirection / cutDirection.Length
		widthDirection /= widthDirection.Length
		width1 -= self.margin
		width2 -= self.margin
		self.widthVector1 = width1 * -widthDirection
		self.widthVector2 = width2 * widthDirection
		projectedScrewDistanceSquared = self.tabbing.screwDistance ** 2 - (width1 + width2) ** 2
		if projectedScrewDistanceSquared < 0:
			raise Exception('fastening line is wider than screw distance')
		projectedScrewDistance = math.sqrt(projectedScrewDistanceSquared)
		self.lengthVector = (v2 - v1) / self.dist
		self.screwCount = int(math.ceil((self.dist - self.margin * 2) / projectedScrewDistance) + 1)

	def calculate(self):
		screwPosDelta = (self.dist - self.margin * 2) / (self.screwCount - 1)
		screwPoss = [idx * screwPosDelta + self.margin for idx in xrange(self.screwCount)]
		cuts = None
		side2 = False
		for pos in screwPoss:
			vec = self.v1 + self.lengthVector * pos
			if side2:
				vec += self.widthVector1
			else:
				vec += self.widthVector2
			cut = Part.makeCylinder(self.tabbing.screwDiameter / 2, self.tabbing.thickness * 5, vec - self.tabbing.thickness * 2.5 * self.cutDirection, self.cutDirection)
			if cuts is None:
				cuts = cut
			else:
				cuts = cuts.fuse(cut)
			side2 = not side2
		return cuts

class FrozenGroup:
	def __init__(self, obj, doc, subobjs):
		self.Object = obj
		self.Document = doc
		obj.Proxy = self
		self.SubObjects = subobjs
	def removeObjectsFromDocument(self):
		print 'removeObjectsFromDocument'
		for obj in self.SubObjects:
			self.Document.removeObject(obj)
		self.SubObjects = []
	def addObject(self, child):
		print 'removeObject'
		pass
	def removeObject(self, child):
		print 'addObject'
		pass

class VPFrozenGroup:
	def __init__(self, vobj):
		if FreeCAD.GuiUp:
			vobj.Proxy = self

	def attach(self, vobj):
		self.Object = vobj.Object

	def claimChildren(self):
		if hasattr(self,'Object'):
			if self.Object:
				return self.Object.Proxy.SubObjects

	def __getstate__(self):
		return None

	def __setstate__(self,state):
		return None

class CrateDrawer(FrozenGroup):
	def __init__(self, obj, doc):
		#obj.addExtension('App::OriginGroupExtensionPython', self)
		#obj.ExtensionProxy = self
		obj.addProperty('App::PropertyLength', 'crateOuterWidth', 'CrateDrawer', 'Outer width of a crate')
		obj.crateOuterWidth = u('13 in')
		obj.addProperty('App::PropertyLength', 'crateInnerWidth', 'CrateDrawer', 'Inner width of a crate')
		obj.crateInnerWidth = u('12 in')
		obj.addProperty('App::PropertyLength', 'crateHeight', 'CrateDrawer', 'Height of a crate minus overlap')
		obj.crateHeight = u('10 in')
		obj.addProperty('App::PropertyLength', 'thickness', 'CrateDrawer', 'Material thickness')
		obj.thickness = u('0.25 in')
		obj.addProperty('App::PropertyLength', 'tabSpacing', 'CrateDrawer', 'Tab spacing')
		obj.tabSpacing = u('1 in')
		obj.addProperty('App::PropertyLength', 'overlap', 'CrateDrawer', 'Stacking overlap')
		obj.overlap = u('0.5 in')
		obj.addProperty('App::PropertyLength', 'trimWidth', 'CrateDrawer', 'Trim width')
		obj.trimWidth = obj.tabSpacing * 2
		#obj.addProperty('App::PropertyLength', 'floorHeight', 'CrateDrawer', 'Floor beam height')
		#obj.floorHeight = obj.tabSpacing
		obj.addProperty('App::PropertyBool', 'screws', 'CrateDrawer', 'Whether to use screws or just glue')
		obj.screws = True
		obj.addProperty('App::PropertyDistance', 'screwSpacing', 'CrateDrawer', 'Screw spacing')
		obj.screwSpacing = u('6 in')
		obj.addProperty('App::PropertyDistance', 'screwMargin', 'CrateDrawer', 'Distance to space screws away from corners')
		obj.addProperty('App::PropertyLength', 'screwMaxLength', 'CrateDrawer', 'Maximum screw length')
		obj.screwMaxLength = u('16 mm')
		obj.addProperty('App::PropertyLength', 'screwMinLength', 'CrateDrawer', 'Minimum screw length')
		obj.screwMinLength = u('14 mm')
		obj.addProperty('App::PropertyLength', 'screwDiameter', 'CrateDrawer', 'Screw Diameter')
		obj.screwDiameter = u('3 mm')
		obj.addProperty('App::PropertyLength', 'nutDiameter', 'CrateDrawer', 'Nut Diameter')
		obj.nutDiameter = u('5.5 mm')
		obj.addProperty('App::PropertyLength', 'nutThickness', 'CrateDrawer', 'Nut Thickness')
		obj.nutThickness = u('2.4 mm')
		obj.addProperty('App::PropertyLength', 'screwHeadHeight', 'CrateDrawer', 'Height of screw heads')
		obj.screwHeadHeight = u('2.5 mm')
		obj.screwMargin = obj.nutDiameter + obj.thickness
		#obj.Proxy = self

		#obj.Shape = Part.Shape()
		#self.Object = obj
		self.left_wall = doc.addObject("Part::Feature", "Crate Left")
		self.right_wall = doc.addObject("Part::Feature", "Crate Right")
		self.back_wall = doc.addObject("Part::Feature", "Crate Back")
		self.bottom_wall = doc.addObject("Part::Feature", "Crate Bottom")
		self.trim_wall = doc.addObject("Part::Feature", "Crate Front")
		self.top_wall = doc.addObject("Part::Feature", "Crate Top")
		self.drawer_left_wall = doc.addObject("Part::Feature", "Drawer Left")
		self.drawer_right_wall = doc.addObject("Part::Feature", "Drawer Right")
		self.drawer_back_wall = doc.addObject("Part::Feature", "Drawer Back")
		self.drawer_bottom_wall = doc.addObject("Part::Feature", "Drawer Bottom")
		self.drawer_front_wall = doc.addObject("Part::Feature", "Drawer Front")
		self.sub_wall = doc.addObject("Part::Feature", "Crate Sub Bottom")

		self.drawer = doc.addObject('App::DocumentObjectGroupPython', 'Drawer')
		FrozenGroup(self.drawer, doc, [self.drawer_left_wall, self.drawer_right_wall, self.drawer_back_wall, self.drawer_bottom_wall, self.drawer_front_wall])
		VPFrozenGroup(self.drawer.ViewObject)
		FrozenGroup.__init__(self, obj, doc, [
			self.left_wall, self.right_wall, self.back_wall, self.bottom_wall, self.trim_wall, self.top_wall, self.sub_wall,
			self.drawer
			#self.drawer_left_wall, self.drawer_right_wall, self.drawer_back_wall, self.drawer_bottom_wall, self.drawer_front_wall
		])
		#obj.Group = [ self.left_wall ]
		#fp.addObject(lw)

	def onChanged(self, fp, prop):
		# a property has changed
		self.touch()
		FreeCAD.ActiveDocument.recompute()
	
	def execute(self, fp):
		# recompute

		if fp.screws:
			screwOffset = fp.screwHeadHeight
		else:
			screwOffset = 0

		if fp.screws:
			self.tabbing = Tabbing(fp.tabSpacing, fp.thickness, fp.screwSpacing, fp.screwMargin, fp.screwDiameter, fp.screwMinLength, fp.screwMaxLength, fp.nutDiameter, fp.nutThickness)
		else:
			self.tabbing = Tabbing(fp.tabSpacing, fp.thickness)

		th = fp.thickness
		owid = fp.crateOuterWidth - 2 * screwOffset
		ohit = fp.crateHeight

		TabbedCorner.reset()

		#parts = []

		ops = [
			v(-owid / 2,-owid / 2, 0),
			v(-owid / 2, owid / 2, 0),
			v(-owid / 2, owid / 2, ohit),
			v(-owid / 2,-owid / 2, ohit),
			v( owid / 2,-owid / 2, 0),
			v( owid / 2, owid / 2, 0),
			v( owid / 2, owid / 2, ohit),
			v( owid / 2,-owid / 2, ohit),
			v( owid / 2,-owid / 2, ohit - fp.trimWidth),
			v(-owid / 2,-owid / 2, ohit - fp.trimWidth),
		]

		left_face = Part.Face(Part.makePolygon([ops[0],ops[1],ops[2],ops[3],ops[0]]))
		right_face = Part.Face(Part.makePolygon([ops[4],ops[5],ops[6],ops[7],ops[4]]))
		back_face = Part.Face(Part.makePolygon([ops[1],ops[2],ops[6],ops[5],ops[1]]))
		bottom_face = Part.Face(Part.makePolygon([ops[0],ops[1],ops[5],ops[4],ops[0]]))
		trim_face = Part.Face(Part.makePolygon([ops[3],ops[7],ops[8],ops[9],ops[3]]))
		top_face = Part.Face(Part.makePolygon([ops[2],ops[3],ops[7],ops[6],ops[2]]))
		left_trim_edge = [ops[3],ops[9]]
		right_trim_edge = [ops[7],ops[8]]

		left_wall = left_face.extrude(v(th,0,0))
		right_wall = right_face.extrude(v(-th,0,0))
		back_wall = back_face.extrude(v(0,-th,0))
		bottom_wall = bottom_face.extrude(v(0,0,th))
		trim_wall = trim_face.extrude(v(0,th,0))
		top_wall = top_face.extrude(v(0,0,-th))

		for cuts in TabbedEdge.FromFaces(self.tabbing, left_face, back_face):
			left_wall = left_wall.cut(cuts[0].calculate())
			back_wall = back_wall.cut(cuts[1].calculate())

		for cuts in TabbedEdge.FromFaces(self.tabbing, right_face, back_face):
			right_wall = right_wall.cut(cuts[0].calculate())
			back_wall = back_wall.cut(cuts[1].calculate())

		for cuts in TabbedEdge.FromFaces(self.tabbing, left_face, bottom_face):
			left_wall = left_wall.cut(cuts[0].calculate())
			bottom_wall = bottom_wall.cut(cuts[1].calculate())

		for cuts in TabbedEdge.FromFaces(self.tabbing, right_face, bottom_face):
			right_wall = right_wall.cut(cuts[0].calculate())
			bottom_wall = bottom_wall.cut(cuts[1].calculate())

		for cuts in TabbedEdge.FromFaces(self.tabbing, back_face, bottom_face):
			back_wall = back_wall.cut(cuts[0].calculate())
			bottom_wall = bottom_wall.cut(cuts[1].calculate())

		trim_wall = trim_wall.cut(TabbedEdge(self.tabbing, left_trim_edge[0], left_trim_edge[1], trim_face, left_face, True, True, False, False, False, False, True, False).calculate())
		left_wall = left_wall.cut(TabbedEdge(self.tabbing, left_trim_edge[0], left_trim_edge[1], left_face, trim_face, False, False, True, False, False, True, True, False).calculate())
		trim_wall = trim_wall.cut(TabbedEdge(self.tabbing, right_trim_edge[0], right_trim_edge[1], trim_face, right_face, True, True, False, False, False, False, True, False).calculate())
		right_wall = right_wall.cut(TabbedEdge(self.tabbing, right_trim_edge[0], right_trim_edge[1], right_face, trim_face, False, False, True, False, False, True, True, False).calculate())

		for cuts in TabbedEdge.FromFaces(self.tabbing, left_face, top_face, False):
			left_wall = left_wall.cut(cuts[0].calculate())
			top_wall = top_wall.cut(cuts[1].calculate())
		for cuts in TabbedEdge.FromFaces(self.tabbing, right_face, top_face, False):
			right_wall = right_wall.cut(cuts[0].calculate())
			top_wall = top_wall.cut(cuts[1].calculate())
		for cuts in TabbedEdge.FromFaces(self.tabbing, back_face, top_face, False):
			back_wall = back_wall.cut(cuts[0].calculate())
			top_wall = top_wall.cut(cuts[1].calculate())
		for cuts in TabbedEdge.FromFaces(self.tabbing, trim_face, top_face, False):
			trim_wall = trim_wall.cut(cuts[0].calculate())
			top_wall = top_wall.cut(cuts[1].calculate())

		top_wall = top_wall.cut(Part.makeBox(fp.crateInnerWidth, fp.crateInnerWidth, th * 3, v(-fp.crateInnerWidth / 2, -fp.crateInnerWidth / 2, ohit - th)))

		# drawer
		nutHeight = (self.tabbing.nutDiameter - self.tabbing.thickness) / 2
		if nutHeight < 0:
			nutHeight = 0
		dsidemargin = self.tabbing.thickness + nutHeight
		screwHeight = fp.screwHeadHeight.Value
		if screwHeight < nutHeight:
			screwHeight = nutHeight;
		dbotmargin = self.tabbing.thickness + screwHeight
		dwid = owid.Value - self.tabbing.thickness * 2 - dsidemargin * 2
		dbot = self.tabbing.thickness + screwHeight
		dtop = ohit - fp.overlap - fp.trimWidth
		dps = [
			v(-dwid / 2,-dwid / 2, dbot),
			v(-dwid / 2, dwid / 2, dbot),
			v(-dwid / 2, dwid / 2, dtop),
			v(-dwid / 2,-dwid / 2, dtop),
			v( dwid / 2,-dwid / 2, dbot),
			v( dwid / 2, dwid / 2, dbot),
			v( dwid / 2, dwid / 2, dtop),
			v( dwid / 2,-dwid / 2, dtop),
			v(-dwid / 2, dwid / 2, dtop + fp.trimWidth),
			v( dwid / 2, dwid / 2, dtop + fp.trimWidth),
		]

		drawer_left_face = Part.Face(Part.makePolygon([dps[0],dps[1],dps[2],dps[3],dps[0]]))
		drawer_right_face = Part.Face(Part.makePolygon([dps[4],dps[5],dps[6],dps[7],dps[4]]))
		drawer_back_face = Part.Face(Part.makePolygon([dps[1],dps[2],dps[6],dps[5],dps[1]]))
		drawer_bottom_face = Part.Face(Part.makePolygon([dps[0],dps[1],dps[5],dps[4],dps[0]]))
		drawer_front_face = Part.Face(Part.makePolygon([dps[3],dps[7],dps[4],dps[0],dps[3]]))
		drawer_back_full_face = Part.Face(Part.makePolygon([dps[1],dps[8],dps[9],dps[5],dps[1]]))

		drawer_left_wall = drawer_left_face.extrude(v(th,0,0))
		drawer_right_wall = drawer_right_face.extrude(v(-th,0,0))
		drawer_back_wall = drawer_back_full_face.extrude(v(0,-th,0))
		drawer_bottom_wall = drawer_bottom_face.extrude(v(0,0,th))
		drawer_front_wall = drawer_front_face.extrude(v(0,th,0))

		for cuts in TabbedEdge.FromFaces(self.tabbing, drawer_left_face, drawer_back_face):
			drawer_left_wall = drawer_left_wall.cut(cuts[0].calculate())
			drawer_back_wall = drawer_back_wall.cut(cuts[1].calculate())

		for cuts in TabbedEdge.FromFaces(self.tabbing, drawer_right_face, drawer_back_face):
			drawer_right_wall = drawer_right_wall.cut(cuts[0].calculate())
			drawer_back_wall = drawer_back_wall.cut(cuts[1].calculate())

		for cuts in TabbedEdge.FromFaces(self.tabbing, drawer_left_face, drawer_front_face):
			drawer_left_wall = drawer_left_wall.cut(cuts[0].calculate())
			drawer_front_wall = drawer_front_wall.cut(cuts[1].calculate())

		for cuts in TabbedEdge.FromFaces(self.tabbing, drawer_right_face, drawer_front_face):
			drawer_right_wall = drawer_right_wall.cut(cuts[0].calculate())
			drawer_front_wall = drawer_front_wall.cut(cuts[1].calculate())

		for cuts in TabbedEdge.FromFaces(self.tabbing, drawer_left_face, drawer_bottom_face):
			drawer_left_wall = drawer_left_wall.cut(cuts[0].calculate())
			drawer_bottom_wall = drawer_bottom_wall.cut(cuts[1].calculate())

		for cuts in TabbedEdge.FromFaces(self.tabbing, drawer_right_face, drawer_bottom_face):
			drawer_right_wall = drawer_right_wall.cut(cuts[0].calculate())
			drawer_bottom_wall = drawer_bottom_wall.cut(cuts[1].calculate())

		for cuts in TabbedEdge.FromFaces(self.tabbing, drawer_back_face, drawer_bottom_face):
			drawer_back_wall = drawer_back_wall.cut(cuts[0].calculate())
			drawer_bottom_wall = drawer_bottom_wall.cut(cuts[1].calculate())

		for cuts in TabbedEdge.FromFaces(self.tabbing, drawer_front_face, drawer_bottom_face):
			drawer_front_wall = drawer_front_wall.cut(cuts[0].calculate())
			drawer_bottom_wall = drawer_bottom_wall.cut(cuts[1].calculate())

		self.drawer_left_wall.Shape = drawer_left_wall
		self.drawer_right_wall.Shape = drawer_right_wall
		self.drawer_back_wall.Shape = drawer_back_wall
		self.drawer_bottom_wall.Shape = drawer_bottom_wall
		self.drawer_front_wall.Shape = drawer_front_wall
		drawer = Part.Compound([drawer_left_wall, drawer_right_wall, drawer_back_wall, drawer_bottom_wall, drawer_front_wall])
		drawer.Placement.move(v(0,-dwid/2,0))

		# structure for settling under floor
		iwid = fp.crateInnerWidth.Value
		#fhit = fp.floorHeight.Value
		floor_overlap = fp.overlap

		# ####################################
		# this approach affixes further floors under the floor, flexible and simple
		sps = [
			v(-iwid / 2,-iwid / 2, 0),
			v(-iwid / 2, iwid / 2, 0),
			v( iwid / 2, iwid / 2, 0),
			v( iwid / 2,-iwid / 2, 0),
			v(-iwid / 2,-iwid / 2, 0)
		]
		settle_face = Part.Face(Part.makePolygon(sps))
		settle_wall = settle_face.extrude(v(0,0,-th))
		settle_ct = int(floor_overlap / th)
		settle_floors = []
		settle_cuts = None
		for idx in xrange(len(sps) - 1):
			settle_cut = FastenedFace(self.tabbing, sps[idx], sps[idx+1], 0, self.tabbing.screwEdgeDistance * 2, v(0,0,-1), v(0,0,-1).cross(sps[idx+1] - sps[idx])).calculate()
			if settle_cuts is None:
				settle_cuts = settle_cut
			else:
				settle_cuts = settle_cuts.fuse(settle_cut)
		bottom_wall = bottom_wall.cut(settle_cuts)
		for idx in xrange(settle_ct):
			settle_floor = settle_wall.cut(settle_cuts)
			settle_floor.Placement.move(v(0,0,idx * -th))
			settle_floors.append(settle_floor)

		# ####################################
		# this approach was by making smaller walls placed into the floor, below
		# I think the problem was that it's so close to the outer walls,
		# there can be intersection problems
		#ops = [
		#	v(-iwid / 2,-iwid / 2, self.tabbing.thickness),
		#	v(-iwid / 2, iwid / 2, self.tabbing.thickness),
		#	v(-iwid / 2, iwid / 2, -floor_overlap),
		#	v(-iwid / 2,-iwid / 2, -floor_overlap),
		#	v( iwid / 2,-iwid / 2, self.tabbing.thickness),
		#	v( iwid / 2, iwid / 2, self.tabbing.thickness),
		#	v( iwid / 2, iwid / 2, -floor_overlap),
		#	v( iwid / 2,-iwid / 2, -floor_overlap)
		#]

		#settle_left_face = Part.Face(Part.makePolygon([ops[0],ops[1],ops[2],ops[3],ops[0]]))
		#settle_right_face = Part.Face(Part.makePolygon([ops[4],ops[5],ops[6],ops[7],ops[4]]))
		#settle_back_face = Part.Face(Part.makePolygon([ops[1],ops[2],ops[6],ops[5],ops[1]]))
		#settle_front_face = Part.Face(Part.makePolygon([ops[0],ops[3],ops[4],ops[7],ops[0]]))

		#settle_left_wall = settle_left_face.extrude(v(th,0,0))
		#settle_right_wall = settle_right_face.extrude(v(-th,0,0))
		#settle_back_wall = settle_back_face.extrude(v(0,-th,0))
		#settle_front_wall = settle_front_face.extrude(v(0,th,0))

		#bottom_wall = bottom_wall.cut(TabbedEdge(self.tabbing, ops[0], ops[1], bottom_face, settle_left_face, False, True, False, True, True, True, False, False).calculate())
		#settle_left_wall = settle_left_wall.cut(TabbedEdge(self.tabbing, ops[0], ops[1], settle_left_face, bottom_face, True, False, True, False, False, False, False, False).calculate())
		#
		#parts.append(settle_left_wall)
		# ####################################

		# ####################################
		# this approach was by making naked joists that replaced the floor
		# the problem was again intersection, compounded by the lack of a
		# front wall to place them against
		#horizontal_floor_walls = []
		#horizontal_floor_faces = []
		#horizontal_floor_points = []

		#floor1SlotsOnTop = False
		#floor2SlotsOnTop = True

		#for floor_dist in (-iwid / 2, iwid / 2):
		#	floor_points = [
		#		v(-owid / 2, floor_dist, 0),
		#		v( owid / 2, floor_dist, 0),
		#		v( owid / 2, floor_dist, fhit),
		#		v(-owid / 2, floor_dist, fhit)
		#	]
		#	floor_points.append(floor_points[0])
		#	horizontal_floor_points.append(floor_points)
		#	floor_face = Part.Face(Part.makePolygon(floor_points))
		#	horizontal_floor_faces.append(floor_face)
		#	
		#	floor_wall = floor_face.extrude(v(0,-th*cmp(floor_dist,0),0))
		#	horizontal_floor_walls.append(floor_wall)

		#back_floor_points = horizontal_floor_points[1]
		#front_floor_points = horizontal_floor_points[0]
		#back_floor_wall = horizontal_floor_walls[1]
		#front_floor_wall = horizontal_floor_walls[0]
		#back_floor_face = horizontal_floor_faces[1]
		#front_floor_face = horizontal_floor_faces[0]

		#secondary_floor_walls = []

		#for floor_dist in (-iwid / 2, iwid / 2):
		#	floor_points = [
		#		v(floor_dist,-iwid / 2, 0),
		#		v(floor_dist, owid / 2, 0),
		#		v(floor_dist, owid / 2, fhit),
		#		v(floor_dist,-iwid / 2, fhit)
		#	]
		#	floor_points.append(floor_points[0])
		#	floor_face = Part.Face(Part.makePolygon(floor_points))
		#	
		#	floor_wall = floor_face.extrude(v(-th*cmp(floor_dist,0),0,0))
		#	floor_wall = floor_wall.cut(TabbedEdge(self.tabbing, floor_points[0], floor_points[3], floor_face, front_floor_face, not floor2SlotsOnTop, False, True, False, False, False, False, False).calculate())
		#	front_floor_wall = front_floor_wall.cut(TabbedEdge(self.tabbing, floor_points[0], floor_points[3], front_floor_face, floor_face, floor2SlotsOnTop, True, False, True, False, True, False, False).calculate())
		#	floor_wall = floor_wall.cut(TabbedEdge(self.tabbing, floor_points[1], floor_points[2], floor_face, back_face, not floor2SlotsOnTop, False, True, False, False, False, False, False).calculate())
		#	back_wall = back_wall.cut(TabbedEdge(self.tabbing, floor_points[1], floor_points[2], back_face, floor_face, floor2SlotsOnTop, True, False, True, False, True, False, False).calculate())
		#	secondary_floor_walls.append(floor_wall)

		#horizontal_floor_walls = []
		#for pointswallface in ((front_floor_points,front_floor_wall,front_floor_face),(back_floor_points,back_floor_wall,back_floor_face)):
		#	floor_points = pointswallface[0]
		#	floor_wall = pointswallface[1]
		#	floor_face = pointswallface[2]
		#	floor_wall = floor_wall.cut(TabbedEdge(self.tabbing, floor_points[0], floor_points[3], floor_face, left_face, not floor1SlotsOnTop, False, True, False, False, False, False, False).calculate())
		#	left_wall = left_wall.cut(TabbedEdge(self.tabbing, floor_points[0], floor_points[3], left_face, floor_face, floor1SlotsOnTop, True, False, True, False, True, False, False).calculate())
		#	floor_wall = floor_wall.cut(TabbedEdge(self.tabbing, floor_points[1], floor_points[2], floor_face, right_face, not floor1SlotsOnTop, False, True, False, False, False, False, False).calculate())
		#	right_wall = right_wall.cut(TabbedEdge(self.tabbing, floor_points[1], floor_points[2], right_face, floor_face, floor1SlotsOnTop, True, False, True, False, True, False, False).calculate())
		#	horizontal_floor_walls.append(floor_wall)
		#back_floor_wall = horizontal_floor_walls[1]
		#front_floor_wall = horizontal_floor_walls[0]
		# ####################################

		# offset parts to see better
		#back_wall.Placement.move(v(0,th*2,0))
		#bottom_wall.Placement.move(v(0,0,-th*2))
		#left_wall.Placement.move(v(-th*2,0,0))
		#right_wall.Placement.move(v(th*2,0,0))

		#parts = secondary_floor_walls

		#parts.append(back_floor_wall)
		#parts.append(front_floor_wall)

		#parts.append(back_floor_wall)
		#parts.append(front_floor_wall)
		#parts.extend(secondary_floor_walls)

		self.left_wall.Shape = left_wall
		self.right_wall.Shape = right_wall
		self.back_wall.Shape = back_wall
		self.bottom_wall.Shape = bottom_wall
		self.trim_wall.Shape = trim_wall
		self.top_wall.Shape = top_wall
		#self.drawer = drawer
		#self.settle_floors = settle_floors
		self.sub_wall.Shape = Part.makeCompound(settle_floors)

		#self.lw = FreeCAD.ActiveDocument.addObject("Part::Feature", "Left Wall")
		#self.lw.Shape = left_wall
		#fp.addObject(lw)
		
		#fp.Shape = Part.makeCompound(parts)
		#fp.Shape = Part.Compound()

#class VPCrateDrawer:
#	def __init__(self, vobj):
#		vobj.Proxy = self
#
#	def attach(self,vobj):
#		self.Object = vobj.Object
#
#	def claimChildren(self):
#		if hasattr(self,'Object'):
#			if self.Object:
#				return self.Object.Proxy.subparts
#		return []
#
#	def __getstate__(self):
#		return None
#
#	def __setstate__(self,state):
#		return None
#

def makeCrate():
		if not FreeCAD.ActiveDocument:
			FreeCAD.newDocument()
		c = FreeCAD.ActiveDocument.addObject('App::DocumentObjectGroupPython', 'CrateDrawer')
		#c = FreeCAD.ActiveDocument.addObject('Part::FeaturePython', 'CrateDrawer')
		CrateDrawer(c, FreeCAD.ActiveDocument)
		VPFrozenGroup(c.ViewObject)
		FreeCAD.ActiveDocument.recompute()
