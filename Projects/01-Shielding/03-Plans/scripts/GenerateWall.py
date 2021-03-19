#!/usr/bin/env python3

# GOAL: generate plans for a sturdy wall to which foil could be affixed

from dataclasses import dataclass
import numpy as np
import pint
import rpack

units = pint.UnitRegistry()

bed_dims = [1, 1] * units.meter
beam_width = 1 * units.mm

wall_dims = [1, 1] * units.meter
foil_dims = [4, 8] * units.ft

strut_width = 1 * units.inch
strut_maxdist = 8 * strut_width

def struts_per_length(width, max_distance):
    if width > max_distance:
        return np.ceil((width / distance + 1).to(units.dimensionless))
    else:
        return 2

# to place the struts in the cardboard, we'll want to stagger the slots
# [gluing the struts into the slots can probably stick some foil]

# make rectangles for the struts

#class Wall:
#    def __init__(self, width, height, depth

@dataclass
class Material:
    depth: units.Quantity

class Wall:
    def __init__(self, wallmat, width, height, strutmat, strutwidth):
        self.wallmat = wallmat
        self.width = width
        self.height = height
        self.strutmat = strutmat
        self.strutwidth = strutwidgth
        self.struts = []
        # a strut will basically need endpoints
    def studs(self, dist):
        

@dataclass
class Strut:
    width : units.Quantity
    length : units.Quantity
    wall : Wall
    
    tabdist : units.Quantity
    crossdist : units.Quantity
    cross_polarity : bool = True
        
    @property
    def rect(self):
        return (self.width, self.length)

    
        
wallmat = Material(1 * units.mm)
strutmat = Material(1 * units.mm)

strutlen0 = struts_per_length(wall_dims[0], strut_maxdist) * wall_dims[1] + wall_dims[0] * 2
strutlen1 = struts_per_length(wall_dims[1], strut_maxdist) * wall_dims[0] + wall_dims[1] * 2
if strutlen1 > strutlen0:
    up_dim = 1
    right_dim = 0
else:
    up_dim = 0
    right_dim = 1

stud = Strut(strut_width, wall_dims[up_dim], strutmat, wallmat, strut_maxdist, 0)
plate = Strut(strut_width
# try struts both ways, pick the one with smallest total length.
length_



# let's say they are already cut.
# the layout problem is hard.  we can break into add-to and make-new.

class BedLayout:
    def __init__(self, bed_dims):
        self.bed_dims = bed_dims
        self.parts = []
    def add(self, rect_dims):
        self.parts.append(rect_dims)
        # is there more space?
