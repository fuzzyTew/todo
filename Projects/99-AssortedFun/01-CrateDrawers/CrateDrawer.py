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
# 4. empathy
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

# to really listen to stories from the past, listen for what is alive in the person NOW

# X is left and right
# Y is positive away from viewer
# Z is up and down

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
	def __init__(self, tabDistance, thickness, screwDistance=0, screwDiameter=0, screwMinLength=0, screwMaxLength=0, nutDiameter=0, nutThickness=0):
		self.tabDistance = tabDistance.Value
		self.thickness = thickness.Value
		self.screwDistance = screwDistance.Value
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
	def __init__(self, v):
		self.v = v
		if self in TabbedCorner.corners:
			self.filled = True
			self.filler = TabbedCorner.corners[self]
		else:
			self.filled = False
			self.filler = None

	def fill(self, filler):
		TabbedCorner.corners[self] = filler
		self.filler = TabbedCorner.corners[self]

	def __hash__(self):
		return (hash(self.v.x) << 1) ^ hash(self.v.y) ^ (hash(self.v.z) << 2)

class TabbedEdge:
	@staticmethod
	def FromFaces(tabbing, face1, face2):
		v2v = lambda vv: v(vv.X, vv.Y, vv.Z)
		samev = lambda v1, v2: v1.x == v2.x and v1.y == v2.y and v1.z == v2.z
		coordlist = lambda v: [v.x, v.y, v.z]
		ret = []
		for edge1 in face1.Edges:
			for edge2 in face2.Edges:
				vs1 = [v2v(x) for x in edge1.Vertexes]
				vs2 = [v2v(x) for x in edge2.Vertexes]
				if (samev(vs1[0], vs2[0]) and samev(vs1[1], vs2[1])) or (samev(vs1[0], vs2[1]) and samev(vs1[1], vs2[0])):
					cutFlag = coordlist(vs1[0]) < coordlist(vs1[1])
					# we only want the component of cutDirection that is normal
					# to the edge
					edgeDir = vs1[1] - vs1[0]
					edgeDir /= edgeDir.Length
					cutDirection1 = face1.CenterOfMass - (vs1[0] + vs1[1]) / 2
					cutDirection1 -= cutDirection1.dot(edgeDir) * edgeDir
					cutDirection2 = face2.CenterOfMass - (vs1[0] + vs1[1]) / 2
					cutDirection2 -= cutDirection2.dot(edgeDir) * edgeDir
					ret.append( (
						TabbedEdge(tabbing, vs1[0], vs1[1], cutDirection1, cutFlag),
						TabbedEdge(tabbing, vs1[0], vs1[1], cutDirection2, not cutFlag)) )
		return ret
				

	def __init__(self, tabbing, v1, v2, cutDirection, cutFlag):
		self.c1 = TabbedCorner(v1)
		self.c2 = TabbedCorner(v2)
		self.dist = (v2 - v1).Length
		if self.dist == 0:
			raise Exception('endpoints are coincident')
		self.unitv = (v2 - v1) / self.dist
		self.tabbing = tabbing
		if cutDirection.Length == 0:
			raise Exception('cut direction is zero')
		self.cutDirection = cutDirection / cutDirection.Length
		self.cutFlag = cutFlag
		self.cutNormal = self.unitv.cross(self.cutDirection)
		if self.tabbing.screwDistance:
			self.screwCount = int(math.ceil(self.dist / self.tabbing.screwDistance) + 1)
		else:
			self.screwCount = 0
		if not self.c1.filled and cutFlag:
			self.c1.fill(self)
		elif not self.c2.filled and not cutFlag:
			self.c2.fill(self)
		if self.tabbing.screwDistance:
			if self.screwCount % 2 != 0:
				++ self.screwCount
			screwOffset = self.tabbing.screwTabWidth / 2 + self.tabbing.thickness
			screwDelta = (self.dist - screwOffset * 2) / (self.screwCount - 1)
			self.screwPositions = [idx * screwDelta + screwOffset for idx in xrange(self.screwCount)]
		else:
			self.screwPositions = []
	
	def calculate(self):
		pos = 0
		self.cuts = None

		self.tabbing.update()

		screwIdx = 0
		tabnext = self.cutFlag

		# fill for corner 1
		if self.c1.filler != self:
			slotpos = -self.tabbing.slotCutOverlap
			slotlen = self.tabbing.thickness + self.tabbing.slotCutOverlap
			if not tabnext:
				slotlen += self.tabbing.slotCutOverlap
			self.addslot(slotpos, slotlen)
		pos += self.tabbing.thickness

		while pos < self.dist - self.tabbing.thickness:
			possibleScrewPos = pos + self.tabbing.screwTabWidth / 2
			nextScrewPos = pos + self.tabbing.tabWidth + self.tabbing.screwTabWidth / 2
			goalScrewPos = self.screwPositions[screwIdx]
			if abs(goalScrewPos - possibleScrewPos) < abs(goalScrewPos - nextScrewPos):
				# place a screw
				#slotlen = 2 * (goalScrewPos - pos)
				#slotlen = goalScrewPos + self.tabbing.screwTabWidth / 2 - pos
				slotlen = self.tabbing.screwTabWidth
				screwpos = pos + slotlen / 2
				if tabnext:
				 	self.addscrewtab(screwpos)
				else:
				 	self.addscrewslot(pos, screwpos, slotlen)
				pos += slotlen
				screwIdx = screwIdx + 1
				if screwIdx == len(self.screwPositions):
					tabnext = not tabnext
					break
			else:
				# place a tab
				if not tabnext:
					self.addslot(pos, self.tabbing.tabWidth)
				pos += self.tabbing.tabWidth
			tabnext = not tabnext

		# fill for corner 2
		if self.c2.filler != self:
			slotpos = self.dist - self.tabbing.thickness
			slotlen = self.tabbing.thickness + self.tabbing.slotCutOverlap
			if tabnext:
				slotlen += self.tabbing.slotCutOverlap
				slotpos -= self.tabbing.slotCutOverlap
			self.addslot(slotpos, slotlen)

		return self.cuts
		
	def addcut(self, startPos, length, left, right):
		raw_coords = [v(left, 0, 0), v(right, 0, 0), v(right, length, 0), v(left, length, 0), v(left, 0, 0)]
		coords = [self.c1.v + coord.x * self.cutDirection + (coord.y + startPos) * self.unitv - self.tabbing.thickness * 2 * self.cutNormal for coord in raw_coords]
		front = Part.Face(Part.makePolygon(coords))
		cut = front.extrude(self.tabbing.thickness * 3 * self.cutNormal)
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
			self.addcut(screwPos - self.tabbing.screwDiameter / 2, self.tabbing.screwDiameter, margin, margin + self.tabbing.screwDiameter)

	def addscrewslot(self, startPos, screwPos, length):
		# other side to tab into
		self.addcut(startPos, length, -self.tabbing.thickness, self.tabbing.thickness)
		if self.tabbing.screwDiameter:
			# screw body
			self.addcut(screwPos - self.tabbing.screwDiameter / 2, self.tabbing.screwDiameter, 0, self.tabbing.screwMaxLength)
			# nut body
			self.addcut(screwPos - self.tabbing.nutDiameter / 2, self.tabbing.nutDiameter, self.tabbing.screwMinLength - self.tabbing.nutThickness, self.tabbing.screwMinLength)

class CrateDrawer:
	def __init__(self, obj, doc):
		obj.addProperty('App::PropertyLength', 'crateWidth', 'CrateDrawer', 'Width of a crate')
		obj.crateWidth = u('2 ft')
		obj.addProperty('App::PropertyLength', 'crateHeight', 'CrateDrawer', 'Height of a crate minus overlap')
		obj.crateHeight = u('18 in')
		obj.addProperty('App::PropertyLength', 'thickness', 'CrateDrawer', 'Material thickness')
		obj.thickness = u('0.25 in')
		obj.addProperty('App::PropertyLength', 'overlap', 'CrateDrawer', 'Stacking overlap')
		obj.overlap = u('0.5 in')
		obj.addProperty('App::PropertyLength', 'tabSpacing', 'CrateDrawer', 'Tab spacing')
		obj.tabSpacing = u('0.5 in')
		obj.addProperty('App::PropertyBool', 'screws', 'CrateDrawer', 'Whether to use screws or just glue')
		obj.screws = True
		obj.addProperty('App::PropertyDistance', 'screwSpacing', 'CrateDrawer', 'Screw spacing')
		obj.screwSpacing = u('6 in')
		obj.addProperty('App::PropertyLength', 'screwMaxLength', 'CrateDrawer', 'Maximum screw length')
		obj.screwMaxLength = u('14 mm')
		obj.addProperty('App::PropertyLength', 'screwMinLength', 'CrateDrawer', 'Minimum screw length')
		obj.screwMinLength = u('12 mm')
		obj.addProperty('App::PropertyLength', 'screwDiameter', 'CrateDrawer', 'Screw Diameter')
		obj.screwDiameter = u('3 mm')
		obj.addProperty('App::PropertyLength', 'nutDiameter', 'CrateDrawer', 'Nut Diameter')
		obj.nutDiameter = u('5.5 mm')
		obj.addProperty('App::PropertyLength', 'nutThickness', 'CrateDrawer', 'Nut Thickness')
		obj.nutThickness = u('2.4 mm')
		obj.addProperty('App::PropertyLength', 'screwHeadHeight', 'CrateDrawer', 'Height of screw heads')
		obj.screwHeadHeight = u('2.5 mm')
		obj.Proxy = self

		#obj.Shape = #

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
			self.tabbing = Tabbing(fp.tabSpacing, fp.thickness, fp.screwSpacing, fp.screwDiameter, fp.screwMinLength, fp.screwMaxLength, fp.nutDiameter, fp.nutThickness)
		else:
			self.tabbing = Tabbing(fp.tabSpacing, fp.thickness)

		th = fp.thickness
		owid = fp.crateWidth - 2 * screwOffset
		ohit = fp.crateHeight

		c = TabbedCorner
		ops = [
			c(v(-owid / 2,-owid / 2, 0)),
			c(v(-owid / 2, owid / 2, 0)),
			c(v(-owid / 2, owid / 2, ohit)),
			c(v(-owid / 2,-owid / 2, ohit)),
			c(v( owid / 2,-owid / 2, 0)),
			c(v( owid / 2, owid / 2, 0)),
			c(v( owid / 2, owid / 2, ohit)),
			c(v( owid / 2,-owid / 2, ohit))
		]

		for c in ops:
			c.v += v(owid / 2, -owid / 2, 0)

		left_face = Part.Face(Part.makePolygon([ops[0].v,ops[1].v,ops[2].v,ops[3].v,ops[0].v]))
		right_face = Part.Face(Part.makePolygon([ops[4].v,ops[5].v,ops[6].v,ops[7].v,ops[4].v]))
		back_face = Part.Face(Part.makePolygon([ops[1].v,ops[2].v,ops[6].v,ops[5].v,ops[1].v]))

		left_wall = left_face.extrude(v(th,0,0))
		right_wall = right_face.extrude(v(-th,0,0))
		back_wall = back_face.extrude(v(0,-th,0))

		for cuts in TabbedEdge.FromFaces(self.tabbing, left_face, back_face):
			left_wall = left_wall.cut(cuts[0].calculate())
			back_wall = back_wall.cut(cuts[1].calculate())
		
		fp.Shape = Part.Compound([left_wall, right_wall, back_wall])

def makeCrate():
		if not FreeCAD.ActiveDocument:
			FreeCAD.newDocument()
		c = FreeCAD.ActiveDocument.addObject('Part::FeaturePython', 'CrateDrawer')
		CrateDrawer(c, FreeCAD.ActiveDocument)
		c.ViewObject.Proxy = 0
		FreeCAD.ActiveDocument.recompute()
