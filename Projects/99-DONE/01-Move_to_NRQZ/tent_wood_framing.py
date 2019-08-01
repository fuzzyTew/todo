#!/usr/bin/python2

import math

# X is right, Y is front, Z is up

cm_in = 2.54
mm_cm = 10.0
mm_m = 1000.0
in_ft = 12.0
mm_in = cm_in * mm_cm
mm_ft = mm_in * in_ft

truck_mm = (7 * mm_ft + 8 * mm_in - 1.75 * mm_in, 14 * mm_ft + 7./8 * mm_in, 7 * mm_ft + 0.5 * mm_in)
tent_mm = (3 * mm_m, 2 * mm_m, 2.3 * mm_m)
intertent_mm = 50

print "truck", truck_mm, "mm"
print "tent", tent_mm, "mm"

in_mm = 1.0 / mm_in

# plan: build a frame to fit the tent into the deep end of the box, following orientation
# above, such that tent is squished with regard to width and height, but leaves much
# length.

tent_in = [x*in_mm for x in tent_mm]
truck_in = [round(x*in_mm,10) for x in truck_mm]

# the truck will actually be taller on Z than listed here, because the door is not
# present in the deep end of the box.
# the in here are a minimum.

# frame plan: 2x4's sheathed with plywood to fill to <=2"
# standard lumber lengths are even-numbered 6-24 ft
# planing is standardized to lose 0.5" from nominal dimension (for 2x's)
# so 2x4's are 1.5 " deep and we'll want plywood that's a little under
# a quarter inch to sheathe it.

# plywood likely 4'x8'
# lumber likely 8' long

# two frames: intertent and inner
# internet frame goes inbetween tent layers.

intertent_frame_outer_in = (truck_in[0], tent_in[1], 7 * 12 + 0.5 - 3.25 - 0.25) # note height is minimum

# these dimensions are all smaller than 8 ft (and greater than 6 ft)

# plan for cuts: I'll probably want the floor to be full length so the studs may rest on it
# I'll want studs in the floor to walk on.  Two ends of the floor will be full size,
# and perpendicular studs will be decreased size to fill.
# short studs 'feel' sturdier because the air spaces are smaller, but this means more
# cuts to make more studs
# maybe I'll make the smaller airspace approah.

# so, floor length will be full with 2 studs
# floor width will have successive studs
# 4 corners, 2 corner studs for each corner
# ceiling as floor
# I should cut the inner straps from the tent so I can assemble this.
# They are no longer needed.
# studs are typically 16" on center, sometimes dropped to 12" on center
# I'll do 16" on center studs

def nicelength(decimal):
	whole = int(decimal)
	denom = 32
	num = int(round((decimal - whole) * denom))
	if num > 0:
		while num & 1 == 0:
			denom /= 2
			num /= 2
		return str(whole) + "_" + str(num) + '/' + str(denom) + '"'
	else:
		return str(whole) + '"'

class Stud:
	def __init__(self, dim, length, count, label):
		self.count = int(math.ceil(count))
		self.label = label
		self.dim = (dim[0], dim[1], length)
	def __str__(self):
		return "{}x {} long {}x{} studs '{}'".format(self.count, nicelength(self.dim[2]), self.dim[0], self.dim[1], self.label)
class Panel:
	def __init__(self, depth, dim, count, label, cut_axis=0):
		self.count = count
		self.label = label
		self.cut_axis = cut_axis
		self.dim = (dim[0], dim[1], depth)
		self.total = (int(self.dim[self.cut_axis] / 48) + 1) * self.count
	def __str__(self):
		if self.dim[0] > 48 and self.dim[1] > 48:
			cuts = self.dim[self.cut_axis] / 48.0
			ret = ''
			cut_dim = [self.dim[0], self.dim[1]]
			cut_dim[self.cut_axis] = 48
			ret += "{}x {}x{} {} thick panels '{}'".format(int(cuts) * self.count, nicelength(cut_dim[0]), nicelength(cut_dim[1]), self.dim[2], self.label + ' body')
			cut_dim[self.cut_axis] = self.dim[self.cut_axis] - 48 * int(cuts)
			ret += "\n{}x {}x{} {} thick panels '{}'".format(self.count, nicelength(cut_dim[0]), nicelength(cut_dim[1]), self.dim[2], self.label + ' edge')
			return ret
		else:
			return "{}x {}x{} {} thick panels '{}'".format(self.count, self.dim[0], self.dim[1], self.dim[2], self.label)

class Frame:
	def __init__(self, x, y, z, stud_width = 3.5, stud_depth = 1.5, sheathe_depth = 0.125, stud_spacing = 12):
		self.dim = (x,y,z)
		self.stud_dim = (stud_width, stud_depth)
		self.stud_dist = stud_spacing
		self.sheathe_depth = sheathe_depth
		if x > y:
			self.long_dir = 0
		else:
			self.long_dir = 1
		self.studs = []
		self.panels = []

		# long end stud for floor and ceiling, plus 4 for kick and top plates
		floor_dim = (self.dim[1 - self.long_dir], self.dim[self.long_dir])
		self.studs.append(Stud(self.stud_dim, floor_dim[1], 4 + 4, 'end stubs & kick and top'))

		# short joists for floor and ceiling
		inner_len = floor_dim[0] - 2 * self.stud_dim[0]
		# to calculate how many studs are needed for a wall (including the two
		#  at the edges) divide the width by the spacing and add 1
		inner_count = floor_dim[1] / self.stud_dist + 1
		self.studs.append(Stud(self.stud_dim, inner_len, math.ceil(inner_count) * 2, 'joist'))
	
		# kick and top plates for short wall
		# NOTE kick and top plates need to be sideways to have correct wall depth
		short_wall_len = floor_dim[0] - self.stud_dim[1]*2 - self.sheathe_depth*4
		self.studs.append(Stud(self.stud_dim, short_wall_len, 4, '2 short kick & 2 short top'))

		# tall studs for wall, assume floor and ceiling are sheathed before raising
		inner_height = self.dim[2]
		print 'inner_height =', inner_height
		inner_height -= 2 * self.stud_dim[1] + 4 * self.sheathe_depth # floor and ceiling
		print 'inner_height =', inner_height
		inner_height -= 2 * self.stud_dim[0] # kick and top plate
		print 'inner_height =', inner_height
		# inner studs, including 2 on each wall making 2-stud corners
		wall1_stud_count = floor_dim[1] / self.stud_dist + 1
		wall0_stud_count = short_wall_len / self.stud_dist + 1
		wall_total_stud_count = (math.ceil(wall0_stud_count) + math.ceil(wall1_stud_count)) * 2
		self.studs.append(Stud(self.stud_dim, inner_height, wall_total_stud_count, 'wall stud'))

		# the wall outer sheathes do not cover (but are flush with) the kick/top
		# plates, to ease assembly from the inside

		# floor and ceiling, inner
		self.panels.append(Panel(self.sheathe_depth, (self.dim[0], self.dim[1]), 2, 'floor & ceiling'))

		# short wall, outer
		wall_sheathe_height = self.dim[2] - 2 * self.stud_dim[1] - 4 * self.sheathe_depth
		print 'wall_sheathe_height =', wall_sheathe_height
		self.panels.append(Panel(self.sheathe_depth, (short_wall_len, wall_sheathe_height), 2, 'short wall'))

		# long wall, outer
		self.panels.append(Panel(self.sheathe_depth, (floor_dim[1], wall_sheathe_height), 2, 'long wall'))
	def __str__(self):
		ret = "{}x{}x{}\n".format(self.dim[0], self.dim[1], self.dim[2])
		for stud in self.studs:
			ret = ret + str(stud) + "\n"
		for panel in self.panels:
			ret = ret + str(panel) + "\n"
		return ret


stud_width = 0.656
stud_depth = 1.468
sheathe_depth = 0.25
panel_width = 4 * 12.0
panel_length = 8 * 12.0

outer = Frame(intertent_frame_outer_in[0], intertent_frame_outer_in[1], intertent_frame_outer_in[2], stud_width, stud_depth, sheathe_depth)
print str(outer)
#inner = Frame(intertent_frame_outer_in[0] - 4, intertent_frame_outer_in[1] - 4, intertent_frame_outer_in[2] - 4, stud_width, stud_depth, sheathe_depth)
#print str(inner)

print "{} studs".format(sum([x.count for x in outer.studs]))# + sum([x.count for x in inner.studs]))
print "{} panels".format(sum([x.total for x in outer.panels]))# + sum([x.total for x in inner.panels]))
