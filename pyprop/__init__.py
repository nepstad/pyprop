#import mpi
try:
	import pylab
	from pylab import *
except:
	print "Warning: Unable to load matplotlib. Plotting will not be available"

import numpy
from numpy import *

try:
	import pypar
	ProcId = pypar.rank()
	ProcCount = pypar.size()
except:
	ProcId = 0
	ProcCount = 1
	print "Warning: unable to load mpi."

import core
reload(core)

import utilities
reload(utilities)

import serialization
reload(serialization)

import sys

execfile(__path__[0] + "/Distribution.py")
execfile(__path__[0] + "/Enum.py")
execfile(__path__[0] + "/Potential.py")
execfile(__path__[0] + "/Problem.py")

execfile(__path__[0] + "/CreateInstance.py")
execfile(__path__[0] + "/Config.py")
execfile(__path__[0] + "/Plot.py")
execfile(__path__[0] + "/Utility.py")
execfile(__path__[0] + "/Redirect.py")
execfile(__path__[0] + "/Interrupt.py")

#Load propagators
execfile(__path__[0] + "/propagator/init.py")

#set up ProcId and ProcCoun. if pympi is not imported, 
#we are on a single process"
#ProcId = 0
#ProcCount = 1
#try:
#	ProcId = pympi.rank
#	ProcCount = pympi.size
#except: pass
